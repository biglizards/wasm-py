from __future__ import annotations

import dis
import subprocess
from abc import ABC
from types import CodeType
from typing import Optional

from run_wasm import run_wasm_function


class WasmThing(ABC):
    def __init__(self, *children):
        self.children = children
        self.name: str

    def __str__(self) -> str:
        return ' '.join(['(', self.name, *self._body_to_wat(), ')'])

    def __repr__(self):
        return f'{type(self).__name__}({str(self)})'

    def _body_to_wat(self) -> list[str]:
        return [str(child) for child in self.children]

    def compile(self) -> bytes:
        process = subprocess.run(['wat2wasm', '-', '-o', '/dev/stdout'], input=str(self).encode(), capture_output=True)
        if process.returncode != 0:
            raise RuntimeError(f'Failed to compile {str(self)} {process}')
        return process.stdout


class Module(WasmThing):
    name = 'module'


class Func(WasmThing):
    name = 'func'

    class Arg(WasmThing):
        name = 'param'

    class RetType(WasmThing):
        name = 'result'

    def __init__(
            self,
            args: list[Arg],
            return_type: RetType,
            instructions: list[Instruction],
            export: Optional[str] = None
    ) -> None:
        super().__init__()
        self.args = args
        self.return_type = return_type
        self.instructions = instructions
        self.export = export

        if export:
            export_str = f'(export "{export}")'
            self.children = [export_str, *args, return_type, *instructions]
        else:
            self.children = [*args, return_type, *instructions]


class Instruction(WasmThing):
    def __init__(self, code: str):
        super().__init__()
        self.code = code

    def __str__(self) -> str:
        return self.code


class Memory(WasmThing):
    name = 'memory'

    def __init__(self, minimum, maximum=None, export=None):
        if export:
            export = f'(export "{export}")'
        children = [x for x in [export, minimum, maximum] if x]
        super().__init__(*children)


def test():
    return 1 + 2


def module_test():
    m = Module(
        Func(
            args=[Func.Arg('i32'),
                  Func.Arg('i32')],
            return_type=Func.RetType('i32'),
            instructions=[Instruction('local.get 0'),
                          Instruction('local.get 1'),
                          Instruction('i32.add')],
            export='sum'
        )
    )

    import run_wasm
    result = run_wasm.run_wasm(m.compile())
    print(result)


def func_to_wasm(code: CodeType, name: str) -> Func:
    # we're compiling a function -- even simple things like "x+1" are functions (they just have no arguments)
    # well, really, the only way to make them compile to something other than None is to implicit make them
    # closer in form to "lambda: x+1"
    # anyway, the point is: as a function, we have arguments. There's a lot of ways you can confuse me:
    # (x, / y), (x=1), (*x, y)
    # for now, we assume all arguments are positional only (that is, all functions end in an implicit /)
    # and we also assume all variables are i32
    assert code.co_kwonlyargcount == 0
    instructions = [i for j in dis.Bytecode(code) if (i := compile_instruction(j))]

    return Func(
        args=[Func.Arg('i32')]*code.co_argcount,
        return_type=Func.RetType('i32'),
        instructions=instructions,
        export=name
    )


def compile_instruction(i) -> Optional[Instruction]:
    if i.opname == 'LOAD_CONST':
        if not isinstance(i.argval, int):
            raise NotImplementedError("can only handle int consts right now")
        return Instruction('i32.const ' + str(i.argval))
    elif i.opname == 'RETURN_VALUE':
        # it's a stack machine, so returns are implicit
        return None
    elif i.opname == 'LOAD_FAST':
        # load_fast is for locals
        return Instruction('local.get ' + str(i.arg))
    elif i.opname == 'BINARY_ADD':
        return Instruction('i32.add')
    else:
        raise ValueError(f'unknown opcode {i.opname}: {i}')


def run_func(func, func_name, *args):
    # create a dummy module, and run the exported function
    mod = Module(func)
    wasm = mod.compile()
    return run_wasm_function(wasm, func_name, *args)


def main():
    def add1(x):
        return x+1
    print(func_to_wasm(add1.__code__, 'add1'))


    def add(x, y):
        def inner_add(a, b):
            return a + b

        return inner_add(x, y)

    func = func_to_wasm(
        code=add.__code__,
        name='add'
    )

    assert run_func(func, 'add', 3, 33) == 36


if __name__ == '__main__':
    main()
