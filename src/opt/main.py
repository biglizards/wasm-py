import dis
import functools


class Var:
    def __init__(self, value=None, instruction=None):
        self.value = value
        self.scope = {
            'LOAD_CONST': 'const',
            'LOAD_FAST': 'local',
            'LOAD_GLOBAL': 'global',
        }.get(getattr(instruction, 'opname', None))
        self.pushed_by = instruction
        self.popped_by = []

    def __repr__(self):
        if self.value:
            return f'Var({repr(self.value)})'
        else:
            return f'Var()'


class Tuple(Var):
    def __init__(self, value, instruction):
        super().__init__(instruction=instruction)
        self.value = value

    def __repr__(self):
        return f'Tuple({", ".join(map(repr, self.value))})'


class Int(Var):
    def __repr__(self):
        if self.value is not None:
            return f'Int({repr(self.value)})'
        return f'Int()'


class Float(Var):
    def __repr__(self):
        if self.value is not None:
            return f'Float({repr(self.value)})'
        return f'Float()'


class Bool(Var):
    def __repr__(self):
        return f'Bool()'


class Function(Var):
    @staticmethod
    def factory(arg_count, arg_types=None, return_type=None):
        return functools.partial(Function, arg_count, arg_types, return_type)

    def __init__(self, arg_count, arg_types=None, return_type=None, value=None, instruction=None):
        super().__init__(value, instruction)
        self.arg_count = arg_count
        self.arg_types = arg_types
        self.return_type = return_type

    def __repr__(self):
        if self.arg_types and self.return_type:
            return f'Function({repr(self.arg_types)} => {repr(self.return_type)})'
        return f'Function({self.arg_count}, {repr(self.arg_types)}, {repr(self.return_type)})'


class InstructionList:
    def __init__(self, instructions: list[dis.Instruction]):
        self.instructions = instructions
        self.indices = {
            x.offset: i for i, x in enumerate(self.instructions)
        }
        self.indices_inv = {
            i: x.offset for i, x in enumerate(self.instructions)
        }


jumps = [
    'JUMP_FORWARD',
    'POP_JUMP_IF_TRUE',
    'POP_JUMP_IF_FALSE',
    'JUMP_IF_NOT_EXC_MATCH',
    'JUMP_IF_TRUE_OR_POP',
    'JUMP_IF_FALSE_OR_POP',
    'JUMP_ABSOLUTE',
]
abs_jumps = [
    'JUMP_FORWARD',
    'JUMP_ABSOLUTE'
]