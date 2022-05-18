from functools import lru_cache
from types import FunctionType, CodeType

import opt.py_module, opt.main
import parse_wat
import run_wasm
from opt.cfg import NiceCFG
from parse_wat import Func, KeywordLiteral as Instruction
import dis
from typing import Optional


def func(
        args: list[str],
        return_type: str,
        instructions: list[Instruction],
        local_arg_count: int = 0,
        export: Optional[str] = None,
) -> Func:
    children = []
    if export:
        export_str = f'(export "{export}")'
        children.append(export_str)
    children.extend(f'(param {arg})' for arg in args)
    children.append(f'(result {return_type})')
    if local_arg_count:
        locals_str = f'(local {"i32 " * local_arg_count})'
        children.append(locals_str)
    children.extend(instructions)
    return Func(
        children=children,
        name='func',  # yeah this is kinda weird -- we might want a better/more aware wrapper object in future
    )


class CodeGenerator:
    def __init__(self, path='/home/dave/PycharmProjects/wasm-py/build/emcc/add2.wasm'):
        self.path = path
        self.wasm_module = parse_wat.load(path)
        self.py_module = opt.py_module.PythonModule()

    def compile(self, save_name=None, optimise=True):
        self.py_module.analyse()
        # generate a wasm global for each global
        for global_name in self.py_module.all_globals:
            glob = self.wasm_module.add_global(global_name)
            glob.mutated = global_name in self.py_module.mutated_globals
            # todo: populate global? Or can we only do that once the function is defined?

        self.py_module.optimise()
        # todo do some magic here to slot stuff into the wasm module
        self.add_rotation_funcs()

        for name, cfg in self.py_module.cfgs.items():
            wasm_func = self.func_to_wasm(name, cfg)
            self.wasm_module.add_func(wasm_func, name)
            self.wasm_module.add_func_to_table(name)  # make the func globally accessible
            self.wasm_module.add_func(self.function_wrapper(cfg.func.__code__, name), f'__{name}_wrapper')

        for glob in map(self.wasm_module.get_global_by_name, self.py_module.all_globals):
            if glob.func_name in self.wasm_module.funcs_by_name:
                # populate the global with the table index of the function
                value = self.wasm_module.get_table_entry_by_name(glob.func_name)
            else:
                # populate it with None to begin with (we need to populate it with something, right?)
                # todo replace with sentry value
                value = self.wasm_module.get_global_by_name('_Py_NoneStruct').children[1].children[0]
            self.wasm_module.set_global_value(glob.func_name, value)

        return self.wasm_module.compile(save_name, optimise)

    def add_rotation_funcs(self):
        # they're not very efficient, but they'll be inlined by wasm-opt
        # todo test these functions -- the only case so far has been in test_while_loop.efficient_fib
        rot_two = func(
            args=['i32', 'i32'],
            return_type='i32 i32',
            instructions=[
                Instruction('local.get 1 local.get 0')
            ],
        )
        rot_three = func(
            args=['i32', 'i32', 'i32'],
            return_type='i32 i32 i32',
            instructions=[
                Instruction('local.get 2 local.get 0 local.get 1')
            ],
        )
        rot_four = func(
            args=['i32', 'i32', 'i32', 'i32'],
            return_type='i32 i32 i32 i32',
            instructions=[
                Instruction('local.get 3 local.get 0 local.get 1 local.get 2')
            ],
        )
        dup_top = func(
            args=['i32'],
            return_type='i32 i32',
            instructions=[
                Instruction('local.get 0 local.get 0')
            ],
        )
        dup_top_two = func(
            args=['i32', 'i32'],
            return_type='i32 i32 i32 i32',
            instructions=[
                Instruction('local.get 1 local.get 0 local.get 1 local.get 0')
            ],
        )

        self.wasm_module.add_func(rot_two, '__internal_rot_two')
        self.wasm_module.add_func(rot_three, '__internal_rot_three')
        self.wasm_module.add_func(rot_four, '__internal_rot_three')
        self.wasm_module.add_func(dup_top, '__internal_dup_top')
        self.wasm_module.add_func(dup_top_two, '__internal_dup_top_two')

    def add_to_module(self, function: FunctionType, name: str):
        # current method: compile it to wasm, then add it.
        # new method: collect all functions first, then compile them all at once.
        self.py_module.add_function(function, name)

    def func_to_wasm(self, name: str, cfg: NiceCFG):
        instructions, jump_table = cfg.flatten()
        # pprint.pprint(instructions)
        # print(len(instructions))
        local_count = cfg.func.__code__.co_nlocals
        instructions = [self._compile_instruction(i, jump_table, local_count) for i in instructions]
        # print(len(instructions))

        return func(
            args=['i32'] * cfg.func.__code__.co_argcount,
            return_type='i32',
            instructions=instructions,
            local_arg_count=cfg.func.__code__.co_nlocals - cfg.func.__code__.co_argcount,
            export=name,
        )

    def _compile_instruction(self, i, jump_table, local_count):
        print(i)  # for debug reasons
        instr = self.compile_instruction(i, jump_table, local_count)
        return Instruction(instr, f'(; {str(i)} ;)\n')

    def compile_instruction(self, i: dis.Instruction, jump_table, local_count) -> Instruction:
        if hasattr(i, 'disable') and i.disable:
            # some instructions are "removed" as part of the optimisation step.
            # Really, they should _actually_ be removed, but this works too.
            return Instruction()

        if isinstance(i, str):
            return Instruction(i)

        if i.opname == 'LOAD_CONST':
            if isinstance(i.argval, int):
                return Instruction(f'i32.const {i.argval} '
                                   f'call {self.wasm_module.get_func_index_by_name("PyLong_FromLong")}')
            elif isinstance(i.argval, float):
                return Instruction(f'f64.const {i.argval} '
                                   f'call {self.wasm_module.get_func_index_by_name("PyFloat_FromDouble")}')
            elif i.argval is None:
                return Instruction(f'call {self.wasm_module.get_func_index_by_name("return_none")}')
            else:
                raise NotImplementedError(f'consts of type {type(i.argval)} have not been implemented!')
        elif i.opname == 'RETURN_VALUE':
            # sometimes, returns are implicit. in those cases, the instruction should be optimised out
            # also: when the function ends, call py_decref on each local, once
            values = [f'local.get {n} call {self.wasm_module.get_func_index_by_name("py_decref")} '
                      for n in range(local_count)]
            return Instruction(*values, 'return')
        elif i.opname == 'LOAD_FAST':
            # load_fast is for locals. The order is arguments, then other locals, I think.
            return Instruction(f'local.get {i.arg} '
                               f'local.get {i.arg} '
                               f'call {self.wasm_module.get_func_index_by_name("py_incref")}')
        elif i.opname == 'LOAD_GLOBAL':
            # load_global is for globals. Usually they're functions, stored in the table.
            # we don't use string formatting here so that we can be lazy
            # strict = False
            # if strict:
            #     return Instruction('(table.get 0', '(i32.const', self.wasm_module.get_table_entry_by_name(i.argval), '))')
            # return Instruction('i32.const', self.wasm_module.get_table_entry_by_name(i.argval))
            return Instruction('global.get', self.wasm_module.global_index_by_name[i.argval])
        elif i.opname == 'STORE_GLOBAL':
            return Instruction('global.set', self.wasm_module.global_index_by_name[i.argval])

        # elif i.opname == 'LOAD_DEREF':
        #     pass
        elif i.opname == 'STORE_FAST':
            # in theory, this approach may become invalid in the future, if gc calls __del__ methods
            return Instruction(f'local.get {i.arg} '
                               f'call {self.wasm_module.get_func_index_by_name("py_decref")} '
                               f'local.set {i.arg}')
            # return Instruction(f'local.set {i.arg}')
        # currently no types support inplace operations (or, at least, treat them differently)
        # in the future, this will have to change, but it's good for now
        elif i.opname in ['BINARY_ADD', 'INPLACE_ADD']:
            if i.use_static_typing and i.static_type is opt.main.Int:
                return Instruction(f'call {self.wasm_module.get_func_index_by_name("long_add_direct")}')
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("add_pyobject")}')
        elif i.opname in ['BINARY_SUBTRACT', 'INPLACE_SUBTRACT']:
            if i.use_static_typing and i.static_type is opt.main.Int:
                return Instruction(f'call {self.wasm_module.get_func_index_by_name("long_sub_direct")}')
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("subtract_pyobject")}')

        # todo: static typing optimisations on these number functions too
        elif i.opname in ['BINARY_MODULO', 'INPLACE_MODULO']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("rem_pyobject")}')
        elif i.opname in ['BINARY_TRUE_DIVIDE', 'INPLACE_TRUE_DIVIDE']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("div_pyobject")}')
        elif i.opname in ['BINARY_FLOOR_DIVIDE', 'INPLACE_FLOOR_DIVIDE']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("floor_div_pyobject")}')
        elif i.opname in ['BINARY_POWER', 'INPLACE_POWER']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("bin_pow_pyobject")}')
        elif i.opname in ['BINARY_LSHIFT', 'INPLACE_LSHIFT']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("lshift_pyobject")}')
        elif i.opname in ['BINARY_RSHIFT', 'INPLACE_RSHIFT']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("rshift_pyobject")}')
        elif i.opname in ['BINARY_AND', 'INPLACE_AND']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("and_pyobject")}')
        elif i.opname in ['BINARY_XOR', 'INPLACE_XOR']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("xor_pyobject")}')
        elif i.opname in ['BINARY_OR', 'INPLACE_OR']:
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("or_pyobject")}')

        elif i.opname == 'UNARY_POSITIVE':
            # possibly always a no-op? Who uses unary plus anyway, not worth my time.
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("pos_pyobject")}')
        elif i.opname == 'UNARY_NEGATIVE':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("neg_pyobject")}')
        elif i.opname == 'UNARY_NOT':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("not_pyobject")}')
        elif i.opname == 'UNARY_INVERT':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("inv_pyobject")}')
        elif i.opname == 'IS_OP':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("is_pyobject")}')

        elif i.opname == 'COMPARE_OP':
            op_map = {
                '<': 'lt', '<=': 'lte', '==': 'eq', '!=': 'neq', '>': 'gt', '>=': 'gte'
            }
            op_name = op_map[i.argval]
            if i.use_static_typing and i.static_type is opt.main.Int:
                return Instruction(f'call {self.wasm_module.get_func_index_by_name(f"long_{op_name}_direct")}')
            return Instruction(f'call {self.wasm_module.get_func_index_by_name(f"long_{op_name}")}')
        elif i.opname == 'BINARY_SUBSCR':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("subscr_pyobject")}')
        elif i.opname.startswith('POP_JUMP_IF'):
            # currently we just use native bools
            return Instruction((f'i32.eqz ' if 'FALSE' in i.opname else '')
                               + f'br_if ${jump_table(target=i.argval, offset=i.offset)}')
        elif i.opname.startswith('JUMP_IF'):
            return Instruction(
                f'call {self.wasm_module.get_func_index_by_name("__internal_dup_top")} '
                + (f'i32.eqz ' if 'FALSE' in i.opname else '')
                + f'br_if ${jump_table(target=i.argval, offset=i.offset)} '
                  f'drop'
            )
        elif i.opname in ['JUMP_FORWARD', 'JUMP_ABSOLUTE']:
            # the argval here is the address of the target so we can just pretend it's always an absolute jump
            return Instruction(f'br ${jump_table(target=i.argval, offset=i.offset)}')
        elif i.opname == 'CALL_FUNCTION':
            # to get recursive functions working, we delay compiling these instructions
            class LazyCallFunction:
                def __init__(self):
                    self.val = None

                def __str__(self):
                    if self.val:
                        return self.val
                    self.val = str(self.make())
                    return self.val

                def make(_self):
                    # so, the problem here is calling convention: we have a function taking i.arg arguments,
                    # and then, after that, a function pointer. However, that's the wrong way around --
                    # call indirect expects the function pointer at the top of the stack.

                    # optimisation: sometimes we can call the function directly
                    if i.use_direct_function_call:
                        return Instruction(f'call {self.wasm_module.get_func_index_by_name(i.base_func_name)}')
                    # secondary, less common case: similar analysis, but it's a local (ie an argument)
                    # (we don't do that right now. but could)

                    # fallback using shims -- avoid if possible
                    if i.arg >= 1:
                        shim_id = self.function_shim(i.arg)
                        return Instruction(f'call {shim_id}')
                    else:
                        return Instruction('call_indirect (result i32)')
            return Instruction(LazyCallFunction())
        elif i.opname == 'BUILD_TUPLE':
            # ooh this is a fun one
            # we pop this many things off the stack, and put them in our tuple
            # todo: optimisation: add dedicated functions for "build tuple of n args" for small n
            # todo optimisation 2: we can simply set the value directly
            tuple_size = i.arg
            instruction = [f'(call {self.wasm_module.get_func_index_by_name("PyTuple_New")} (i32.const {tuple_size}))'] + [
                # then call "add to ith slot" n times
                f'(call {self.wasm_module.get_func_index_by_name("PyTuple_set_item_unchecked")} (i32.const {j - 1}))'
                for j in range(tuple_size, 0, -1)
            ]

            return Instruction('\n'.join(instruction))
        # stack swiggling operations are done by calling simple shim functions -- these are optimised out later
        elif i.opname in ['POP_TOP', 'PRINT_EXPR']:
            return Instruction(f'drop')
        elif i.opname == 'ROT_TWO':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("__internal_rot_two")}')
        elif i.opname == 'ROT_THREE':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("__internal_rot_three")}')
        elif i.opname == 'ROT_FOUR':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("__internal_rot_four")}')
        elif i.opname == 'DUP_TOP':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("__internal_dup_top")}')
        elif i.opname == 'DUP_TOP_TWO':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("__internal_dup_top_two")}')
        elif i.opname == 'EXTENDED_ARG':
            pass
        else:
            raise ValueError(f'unknown opcode {i.opname}: {i}')

    @staticmethod
    def call_indirect(size):
        return f'call_indirect (param {"i32 " * size}) (result i32)'

    @lru_cache(maxsize=None)
    def function_shim(self, size, strict=False):
        # push local args 1 through size
        # then push local arg 0
        # note: we can't call a funcref directly, so instead we need to push it into the table
        # this is about 2x time slower than passing the table id (instead of a funcref),
        # so if we're confident it won't cause issues, we can disable strict mode for a speed boost.

        if strict:
            shim = func(
                args=['funcref', 'i32 ' * size],
                return_type='i32',
                instructions=[
                    Instruction(
                        *[f'local.get {i}' for i in range(1, size + 1)],
                        f'(table.set 0 (i32.const {self.wasm_module.tmp_register}) (local.get 0))',
                        f'(i32.const {self.wasm_module.tmp_register})',
                        self.call_indirect(size)
                    )
                ]
            )
        else:
            shim = func(
                args=['i32 ' * (size + 1)],
                return_type='i32',
                instructions=[
                    Instruction(
                        *[f'local.get {i}' for i in range(1, size + 1)],
                        'local.get 0',
                        f'call_indirect (param {"i32 " * size}) (result i32)'
                    )
                ]
            )

        name = f'__internal__{size}_arg_shim'
        self.wasm_module.add_func(shim, name)
        return self.wasm_module.get_func_index_by_name(name)

    def function_wrapper(self, code: CodeType, name) -> Func:
        # so, we can't pass or receive PyObjects directly (ironic)
        # instead, we need to wrap them. Say we're calling a function which takes an int and returns an int
        # in that case, we need to write something like
        # 1. turn local 0 into a PyObject
        # 2. call the function
        # 3. extract the value
        # the problem is that we need to extract arbitrary values (eg tuples, multi-word ints)
        # which requires us to know the type (or at least size) of our return type at compile time
        # this is, notably, impossible, and also not part of the project, so a crude approximation of a solution is used

        make_obj = ' '.join(
            f'local.get {i} call {self.wasm_module.get_func_index_by_name("PyLong_FromLong")}'
            for i in range(code.co_argcount)
        )
        call_fn = f'call {self.wasm_module.get_func_index_by_name(name)}'

        is_tuple = name == 'swap'  # todo awful goddamn fucking bad shitty inference method

        if is_tuple:
            i = code.co_argcount
            extract_value = (
                f'local.set {i} '
                f'(call {self.wasm_module.get_func_index_by_name("PyTuple_GetItem")} (local.get {i}) (i32.const 0)) '
                f'call {self.wasm_module.get_func_index_by_name("PyLong_AsLong")} '
                f'(call {self.wasm_module.get_func_index_by_name("PyTuple_GetItem")} (local.get {i}) (i32.const 1)) '
                f'call {self.wasm_module.get_func_index_by_name("PyLong_AsLong")} '
            )
        else:
            extract_value = f'call {self.wasm_module.get_func_index_by_name("PyLong_AsLong")}'
            # extract_value = 'i32.load offset=12'  # extract the 4th byte from the struct (only works for positive ints)

        return func(
            args=['i32'] * code.co_argcount,
            return_type='i32',  # 'i32 i32' if is_tuple else 'i32',
            instructions=[
                make_obj,
                call_fn,
                # extract_value,
            ],
            export=f'__{name}_wrapper',
            local_arg_count=is_tuple,
        )


def main():
    def add1(x):
        return x + 1

    g = CodeGenerator()
    g.add_to_module(add1.__code__, 'add1')

    wasm = g.wasm_module.compile()
    instance = run_wasm.run_wasm(wasm)

    print(instance.exports.__add1_wrapper(5))

    def fib(x):
        if x <= 1:
            return 1
        return fib(x - 1) + fib(x - 2)

    g.add_to_module(fib.__code__, 'fib')
    wasm = g.wasm_module.compile()
    instance = run_wasm.run_wasm(wasm)
    print(instance.exports.__fib_wrapper(5))

    # def add(x, y):
    #     def inner_add(a, b):
    #         return a + b
    #
    #     return inner_add(x, y)
    #
    # func = func_to_wasm(
    #     code=add.__code__,
    #     name='add'
    # )
    #
    # assert run_func(func, 'add', 3, 33) == 36


if __name__ == '__main__':
    main()
