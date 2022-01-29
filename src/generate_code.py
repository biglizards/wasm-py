from functools import lru_cache
from types import CodeType

import opt.py_module
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
        self.py_module.optimise()
        # todo do some magic here to slot stuff into the wasm module

        for name, cfg in self.py_module.cfgs.items():
            wasm_func = self.func_to_wasm(name, cfg)
            self.wasm_module.add_func(wasm_func, name)
            self.wasm_module.add_func_to_table(name)  # make the func globally accessible
            self.wasm_module.add_func(self.function_wrapper(cfg.code, name), f'__{name}_wrapper')

        return self.wasm_module.compile(save_name, optimise)

    def add_to_module(self, code: CodeType, name: str):
        # current method: compile it to wasm, then add it.
        # new method: collect all functions first, then compile them all at once.
        self.py_module.add_function(code, name)

    def func_to_wasm(self, name: str, cfg: NiceCFG):
        instructions, jump_table = cfg.flatten()
        # pprint.pprint(instructions)
        # print(len(instructions))
        instructions = [self._compile_instruction(i, jump_table) for i in instructions]
        # print(len(instructions))

        return func(
            args=['i32'] * cfg.code.co_argcount,
            return_type='i32',
            instructions=instructions,
            local_arg_count=cfg.code.co_nlocals - cfg.code.co_argcount,
            export=name,
        )

    def _compile_instruction(self, i, jump_table):
        instr = self.compile_instruction(i, jump_table)
        return Instruction(instr, f'(; {str(i)} ;)\n')

    def compile_instruction(self, i: dis.Instruction, jump_table) -> Instruction:
        # todo remove
        if hasattr(i, 'delay') and i.delay:
            print(i, 'really?')
            return Instruction()

        if isinstance(i, str):
            return Instruction(i)

        if i.opname == 'LOAD_CONST':
            if isinstance(i.argval, int):
                return Instruction(f'i32.const {i.argval} '
                                   f'call {self.wasm_module.get_func_index_by_name("PyLong_FromLong")}')
            elif i.argval is None:
                return Instruction(f'call {self.wasm_module.get_func_index_by_name("return_none")}')
            else:
                raise NotImplementedError(f'consts of type {type(i.argval)} have not been implemented!')
        elif i.opname == 'RETURN_VALUE':
            # sometimes, returns are implicit. in those cases, the instruction should be optimised out
            return Instruction('return')
        elif i.opname == 'LOAD_FAST':
            # load_fast is for locals. The order is arguments, then other locals, I think.
            return Instruction('local.get ' + str(i.arg))
        elif i.opname == 'LOAD_GLOBAL':
            # load_global is for globals. Usually they're functions, stored in the table.
            # we don't use string formatting here so that we can be lazy
            strict = False
            if strict:
                return Instruction('(table.get 0', '(i32.const', self.wasm_module.get_table_entry_by_name(i.argval), '))')
            return Instruction('i32.const', self.wasm_module.get_table_entry_by_name(i.argval))

        # elif i.opname == 'LOAD_DEREF':
        #     pass
        elif i.opname == 'STORE_FAST':
            return Instruction('local.set ' + str(i.arg))
        elif i.opname == 'BINARY_ADD':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("add_pyobject")}')
        elif i.opname == 'BINARY_SUBTRACT':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("subtract_pyobject")}')
        elif i.opname == 'COMPARE_OP':
            op_type = i.argval
            if op_type == '<=':
                return Instruction(f'call {self.wasm_module.get_func_index_by_name("leq_pyobject")}')
            elif op_type == '==':
                return Instruction(f'call {self.wasm_module.get_func_index_by_name("eq_pyobject")}')
            elif op_type == '!=':
                return Instruction(f'call {self.wasm_module.get_func_index_by_name("eq_pyobject")} i32.eqz')
            else:
                raise NotImplementedError('can only handle LEQ/EQ')
        elif i.opname == 'BINARY_SUBSCR':
            return Instruction(f'call {self.wasm_module.get_func_index_by_name("subscr_pyobject")}')
        elif i.opname.startswith('POP_JUMP_IF'):
            # currently we just use native bools
            return Instruction((f'i32.eqz ' if 'FALSE' in i.opname else '')
                               + f'br_if ${jump_table(target=i.argval, offset=i.offset)}')
        elif i.opname == 'JUMP_FORWARD':
            # the argval here is the address of the target, so we can just pretend it's an absolute jump
            return Instruction(f'br ${jump_table(target=i.argval, offset=i.offset)}')
        elif i.opname == 'CALL_FUNCTION':
            # to get recursive functions working, we delay compiling these instructions
            # todo this is broken and bad and i dont like it
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
                    # todo: this never triggers due to change in analysis -- replace
                    if hasattr(i, 'func_push_instruction') and hasattr(i.func_push_instruction, 'delay'):
                        i2 = i.func_push_instruction
                        try:
                            # highly experimental optimisation -- renders all functions immutable
                            # maybe 10% faster than using call_indirect
                            index = self.wasm_module.get_func_index_by_name(i2.argval)
                            return Instruction(f'call {index}')
                        except (ValueError, KeyError):
                            pass
                        del i2.delay
                        opening_push = self.compile_instruction(i2, jump_table)
                        return Instruction(opening_push, self.call_indirect(size=i.arg))

                    if i.arg >= 1:
                        shim_id = self.function_shim(i.arg)
                        return Instruction(f'call {shim_id}')
                    else:
                        return Instruction('call_indirect (return i32)')
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
                        'call_indirect (param ' + 'i32 ' * size + ') (result i32)'
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
            return_type='i32 i32' if is_tuple else 'i32',
            instructions=[
                make_obj,
                call_fn,
                extract_value
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
