import dis


class Short:
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f'Short({repr(self.value)})'
        return f'Short()'


class Var:
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        if self.value:
            return f'Var({repr(self.value)})'
        else:
            return f'Var()'


class Bool:
    def __repr__(self):
        return f'Bool()'


class Function:
    def __init__(self, arg_count, arg_types=None, return_type=None):
        self.arg_count = arg_count
        self.arg_types = arg_types
        self.return_type = return_type

    def __repr__(self):
        if self.arg_types and self.return_type:
            return f'({repr(self.arg_types)} => {repr(self.return_type)})'
        return f'Function({self.arg_count}, {repr(self.arg_types)}, {repr(self.return_type)})'


def mutate_stack(stack, instruction, type_map):
    if instruction.opname in ['LOAD_FAST', 'LOAD_CONST', 'LOAD_GLOBAL']:
        if isinstance(instruction.argval, int):
            stack.append(Short(instruction.argval))
        else:
            if instruction.argval in type_map:
                stack.append(type_map[instruction.argval])
            else:
                stack.append(Var(instruction.argval))
    elif instruction.opname in ['POP_JUMP_IF_FALSE']:
        stack.pop()
    elif instruction.opname in ['COMPARE_OP']:
        stack.pop()
        stack.pop()
        stack.append(Bool())  # strictly, rich comparisons allow for non-bool return types
    elif instruction.opname in ['BINARY_SUBTRACT', 'BINARY_ADD']:
        a = stack.pop()
        b = stack.pop()
        if isinstance(a, Short) and isinstance(b, Short):
            stack.append(Short())
        else:
            stack.append(Var())
    elif instruction.opname in ['RETURN_VALUE']:
        assert len(stack) == 1
    elif instruction.opname in ['CALL_FUNCTION']:
        assert len(stack) >= 1 + instruction.arg
        args = [stack.pop() for _ in range(instruction.arg)]
        function = stack.pop()
        if (isinstance(function, Function)
                and function.arg_types and function.return_type
                and all(
                    type(arg) is type(arg_type)
                    for arg, arg_type in zip(args, function.arg_types))):
            stack.append(function.return_type)
        else:
            stack.append(Var())


class InstructionList:
    def __init__(self, instructions):
        self.instructions = instructions
        self.indices = {
            x.offset: i for i, x in enumerate(self.instructions)
        }


def to_tree(code):
    bytecode = dis.Bytecode(code)
    instr_list = InstructionList(list(bytecode))
    stack = []
    to_tree_subset(
        instr_list, 0, stack,
        {
            'n': Short('n'),
            'fib': Function(
                1,
                arg_types=[Short()],
                return_type=Short()
            )
        }
    )


def to_tree_subset(instructions, start, stack, type_map):
    for instruction in instructions.instructions[start:]:
        mutate_stack(stack, instruction, type_map)
        print(instruction.opname, '\t', stack)
        if instruction.opname in ['POP_JUMP_IF_FALSE']:
            print("--- START BLOCK ---")
            new_stack = stack.copy()
            addr = instructions.indices[instruction.arg]
            to_tree_subset(instructions, addr, new_stack, type_map)
            print("--- END BLOCK ---")
        elif instruction.opname in ['RETURN_VALUE']:
            return


def main():
    import tests.example_files.fib
    to_tree(tests.example_files.fib.fib.__code__)


if __name__ == '__main__':
    main()
