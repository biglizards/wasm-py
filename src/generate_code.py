from types import CodeType

import parse_wat
import run_wasm
from parse_wat import Func, Node, KeywordLiteral as Instruction
import dis
from typing import Optional


def func(args: list[str], return_type: str, instructions: list[Instruction], export: Optional[str] = None) -> Func:
    children = []
    if export:
        export_str = f'(export "{export}")'
        children.append(export_str)
    children.extend(f'(param {arg})' for arg in args)
    children.append(f'(result {return_type})')
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
        self.module.add_func(self.function_wrapper(name), f'__{name}_wrapper')

    def func_to_wasm(self, code: CodeType, name: str) -> Func:
        # we're compiling a function -- even simple things like "x+1" are functions (they just have no arguments)
        # well, really, the only way to make them compile to something other than None is to implicit make them
        # closer in form to "lambda: x+1"
        # anyway, the point is: as a function, we have arguments. There's a lot of ways you can confuse me:
        # (x, / y), (x=1), (*x, y)
        # for now, we assume all arguments are positional only (that is, all functions end in an implicit /)
        # and we also assume all variables are i32
        assert code.co_kwonlyargcount == 0
        instructions = [i for j in dis.Bytecode(code) if (i := self.compile_instruction(j))]

        return func(
            args=['i32']*code.co_argcount,
            return_type='i32',
            instructions=instructions,
            export=name
        )

    def compile_instruction(self, i: dis.Instruction) -> Optional[Instruction]:
        if i.opname == 'LOAD_CONST':
            if not isinstance(i.argval, int):
                raise NotImplementedError("can only handle int consts right now")
            # call $new_short with the argument i.argval
            return Instruction(f'i32.const {i.argval} '
                               f'call {self.module.get_index_by_name("PyLong_FromLong")}')
        elif i.opname == 'RETURN_VALUE':
            # sometimes, returns are implicit. in those cases, the instruction should be optimised out
            return Instruction('return')
        elif i.opname == 'LOAD_FAST':
            # load_fast is for locals. The order is arguments, then other locals, I think.
            return Instruction('local.get ' + str(i.arg))
        elif i.opname == 'BINARY_ADD':
            return Instruction(f'call {self.module.get_index_by_name("add")}')
        elif i.opname == 'COMPARE_OP':
            op_type = i.argval
            if op_type == '<=':
                return Instruction(f'call {self.module.get_index_by_name("leq")}')
            elif op_type == '==':
                return Instruction(f'call {self.module.get_index_by_name("eq")}')
            else:
                raise NotImplementedError('can only handle LEQ/EQ')
        # elif i.opname == 'POP_JUMP_IF_FALSE':
        #     pass
        # elif i.opname == 'LOAD_DEREF':
        #     pass
        # elif i.opname == 'BINARY_SUBTRACT':
        #     pass
        # elif i.opname == 'CALL_FUNCTION':
        #     pass
        else:
            raise ValueError(f'unknown opcode {i.opname}: {i}')

    def function_wrapper(self, name) -> Func:
        # so, we can't pass or receive PyObjects directly (ironic)
        # instead, we need to wrap them. Say we're calling a function which takes an int and returns an int
        # in that case, we need to write something like
        # 1. turn local 0 into a PyObject
        # 2. call the function
        # 3. extract the value

        make_obj = f'local.get 0 call {self.module.get_index_by_name("PyLong_FromLong")}'
        call_fn = f'call {self.module.get_index_by_name(name)}'
        extract_value = f'call {self.module.get_index_by_name("PyLong_AsLong")}'
        # extract_value = 'i32.load offset=12'  # extract the 4th byte from the struct (only works for positive ints)

        return func(
            args=['i32'],  # for now
            return_type='i32',  # basically forever
            instructions=[
                make_obj,
                call_fn,
                extract_value
            ],
            export=f'__{name}_wrapper'
        )


def main():
    def add1(x):
        return x+1

    g = CodeGenerator()
    g.add_to_module(add1.__code__, 'add1')

    wasm = g.module.compile()
    instance = run_wasm.run_wasm(wasm)

    print(instance.exports.__add1_wrapper(5))

    def fib(x):
        if x <= 1:
            return 1
        return fib(x-1) + fib(x-2)

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
