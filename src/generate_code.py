from functools import lru_cache
from types import CodeType

import parse_wat
import run_wasm
from opt import ControlFlowGraph, new_cfg
from parse_wat import Func, Node, KeywordLiteral as Instruction
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
        self.module = parse_wat.load(path)

    def add_to_module(self, code: CodeType, name: str):
        self.module.add_func(self.func_to_wasm(code, name), name)
        self.module.add_func(self.function_wrapper(code, name), f'__{name}_wrapper')

    def func_to_wasm(self, code: CodeType, name: str) -> Func:
        # we're compiling a function -- even simple things like "x+1" are functions (they just have no arguments)
        # well, really, the only way to make them compile to something other than None is to implicit make them
        # closer in form to "lambda: x+1"
        # anyway, the point is: as a function, we have arguments. There's a lot of ways you can confuse me:
        # (x, / y), (x=1), (*x, y)
        # for now, we assume all arguments are positional only (that is, all functions end in an implicit /)
        # and we also assume all variables are i32 (this is actually a valid assumption, because we use 32-bit pointers)
        assert code.co_kwonlyargcount == 0

        cfg = new_cfg(code)

        bytecode, before, after, fjt, bjt = cfg.generate_control_flow_instructions()

        def compile_instruction(i: dis.Instruction):
            return Instruction(
                *before[i.offset],
                *self.compile_instruction(i, fjt, bjt).content,
                *after[i.offset],
            )

        instructions = [compile_instruction(j) for j in bytecode]

        # print('\n'.join(str(i) for i in instructions))

        return func(
            args=['i32'] * code.co_argcount,
            return_type='i32',
            instructions=instructions,
            local_arg_count=code.co_nlocals,
            export=name,
        )

    def compile_instruction(self, i: dis.Instruction, fjt, bjt) -> Instruction:
        if hasattr(i, 'delay') and i.delay:
            return Instruction()

        if i.opname == 'LOAD_CONST':
            if isinstance(i.argval, int):
                return Instruction(f'i32.const {i.argval} '
                                   f'call {self.module.get_func_index_by_name("PyLong_FromLong")}')
            elif i.argval is None:
                return Instruction(f'call {self.module.get_func_index_by_name("return_none")}')
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
                return Instruction('(table.get 0', '(i32.const', self.module.get_table_entry_by_name(i.argval), '))')
            return Instruction('i32.const', self.module.get_table_entry_by_name(i.argval))

        # elif i.opname == 'LOAD_DEREF':
        #     pass
        elif i.opname == 'STORE_FAST':
            return Instruction('local.set ' + str(i.arg))
        elif i.opname == 'BINARY_ADD':
            return Instruction(f'call {self.module.get_func_index_by_name("add_pyobject")}')
        elif i.opname == 'BINARY_SUBTRACT':
            return Instruction(f'call {self.module.get_func_index_by_name("subtract_pyobject")}')
        elif i.opname == 'COMPARE_OP':
            op_type = i.argval
            if op_type == '<=':
                return Instruction(f'call {self.module.get_func_index_by_name("leq_pyobject")}')
            elif op_type == '==':
                return Instruction(f'call {self.module.get_func_index_by_name("eq_pyobject")}')
            elif op_type == '!=':
                return Instruction(f'call {self.module.get_func_index_by_name("eq_pyobject")} i32.eqz')
            else:
                raise NotImplementedError('can only handle LEQ/EQ')
        elif i.opname == 'BINARY_SUBSCR':
            return Instruction(f'call {self.module.get_func_index_by_name("subscr_pyobject")}')
        elif i.opname.startswith('POP_JUMP_IF'):
            # currently we just use native bools
            if i.argval > i.offset:  # todo is this right?
                label = fjt[i.argval]
            else:
                label = bjt[i.argval]

            return Instruction((f'i32.eqz ' if 'FALSE' in i.opname else '')
                               + f'br_if ${label}')
        elif i.opname == 'CALL_FUNCTION':
            # to get recursive functions working, we delay compiling these instructions
            class LazyCallFunction:
                def __str__(self):
                    return str(self.make())

                def make(_self):
                    # so, the problem here is calling convention: we have a function taking i.arg arguments,
                    # and then, after that, a function pointer. However, that's the wrong way around --
                    # call indirect expects the function pointer at the top of the stack.
                    if hasattr(i, 'func_push_instruction'):
                        i2 = i.func_push_instruction
                        try:
                            # highly experimental optimisation -- renders all functions immutable
                            # maybe 10% faster than using call_indirect
                            index = self.module.get_func_index_by_name(i2.argval)
                            return Instruction(f'call {index}')
                        except (ValueError, KeyError):
                            pass
                        del i2.delay
                        opening_push = self.compile_instruction(i2, fjt, bjt)
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
            instruction = [f'(call {self.module.get_func_index_by_name("PyTuple_New")} (i32.const {tuple_size}))'] + [
                # then call "add to ith slot" n times
                f'(call {self.module.get_func_index_by_name("PyTuple_set_item_unchecked")} (i32.const {j - 1}))'
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
                        f'(table.set 0 (i32.const {self.module.tmp_register}) (local.get 0))',
                        f'(i32.const {self.module.tmp_register})',
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
        self.module.add_func(shim, name)
        return self.module.get_func_index_by_name(name)


    def function_wrapper(self, code: CodeType, name) -> Func:
        # so, we can't pass or receive PyObjects directly (ironic)
        # instead, we need to wrap them. Say we're calling a function which takes an int and returns an int
        # in that case, we need to write something like
        # 1. turn local 0 into a PyObject
        # 2. call the function
        # 3. extract the value

        make_obj = ' '.join(
            f'local.get {i} call {self.module.get_func_index_by_name("PyLong_FromLong")}'
            for i in range(code.co_argcount)
        )
        call_fn = f'call {self.module.get_func_index_by_name(name)}'

        is_tuple = name == 'swap'  # todo awful goddamn fucking bad shitty inference method

        if is_tuple:
            i = code.co_argcount
            extract_value = (
                f'local.set {i} '
                f'(call {self.module.get_func_index_by_name("PyTuple_GetItem")} (local.get {i}) (i32.const 0)) '
                f'call {self.module.get_func_index_by_name("PyLong_AsLong")} '
                f'(call {self.module.get_func_index_by_name("PyTuple_GetItem")} (local.get {i}) (i32.const 1)) '
                f'call {self.module.get_func_index_by_name("PyLong_AsLong")} '
            )
        else:
            extract_value = f'call {self.module.get_func_index_by_name("PyLong_AsLong")}'
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

    wasm = g.module.compile()
    instance = run_wasm.run_wasm(wasm)

    print(instance.exports.__add1_wrapper(5))

    def fib(x):
        if x <= 1:
            return 1
        return fib(x - 1) + fib(x - 2)

    g.add_to_module(fib.__code__, 'fib')
    wasm = g.module.compile()
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
