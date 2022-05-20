from __future__ import annotations

import dis
import typing
from collections import defaultdict

from opt.main import Int, Var, Bool, Function, Tuple, Float

if typing.TYPE_CHECKING:
    from opt.cfg import NiceCFG, ControlFlowGraph


# general todo: I think some things might be made neater when analysed using the "bag of instructions" model
# especially stuff like globals. It's not a huge problem, but it would make the code more modular
class Analyzer:
    def __init__(self):
        # for each function, determine where it may be called
        self.funcs_for_call = defaultdict(list)
        # for each call instruction, determine which functions may be called
        self.calls_for_func = defaultdict(list)

        self.block_starting_stacks = defaultdict(list)
        self.block_ending_stacks = defaultdict(list)
        self.block_ending_type_maps = defaultdict(list)

        self.block_starting_stack_size = {}
        self.block_ending_stack_size = {}

        # list of consts and their associated WASM global
        self.consts = []

        # list of instructions which mutate global state (ie STORE_GLOBAL and DELETE_GLOBAL)
        self.mutated_globals = []
        # similar, but for all globals
        self.globals = []

    def generate_stack_sizes(self):
        for block, stacks in self.block_starting_stacks.items():
            size = len(stacks[0])
            assert all(len(stack) == size for stack in stacks)
            self.block_starting_stack_size[block] = size

        for block, stacks in self.block_ending_stacks.items():
            size = len(stacks[0])
            assert all(len(stack) == size for stack in stacks)
            self.block_ending_stack_size[block] = size

    def get_push_pop_pairs(self, cfg):
        # if all instructions which push and/or pop the same variable all agree on types,
        # then we can use that type without indirection. Returns a collection of bipartite graphs,
        # along with the most general type of those instructions

        # step 1. pick an instruction from the bag
        #   for each variable it pushes, recurse on the instructions which pop that variable
        #   for each variable it pops, recurse on the instruction which pushed that variable
        # once we're done, remove all of these from the bag, and go back to step 1
        bag: set[dis.Instruction] = set(cfg.cfg.instructions.instructions)

        def pick():
            item = next(iter(bag))
            return item

        def process(item: dis.Instruction) -> set:
            bag.remove(item)
            items = {item}
            if hasattr(item, 'pops_values'):
                for value_set in item.pops_values.values():
                    for value in value_set:
                        if value.pushed_by in bag:
                            items.update(process(value.pushed_by))
                        elif value.pushed_by is None:
                            # this seems like some sort of error condition -- todo check later
                            pass
            if hasattr(item, 'pushes_values'):
                for value_set in item.pushes_values.values():
                    for value in value_set:
                        for instruction in value.popped_by:
                            if instruction in bag:
                                items.update(process(instruction))
            return items

        bipartite_sets = []

        while bag:
            item = pick()
            items = {item, *process(item)}
            bipartite_sets.append(items)

        return bipartite_sets

    def mutate_stack(self, stack, instruction, type_map):
        pop_count = 0
        push_count = 0

        def pop():
            # when we pop a value, note down the instruction which consumed it
            nonlocal pop_count
            if not hasattr(instruction, 'pops_values'):
                instruction.pops_values = defaultdict(set)
                instruction.pops_types = defaultdict(set)
            value = stack.pop()
            instruction.pops_values[pop_count].add(value)
            instruction.pops_types[pop_count].add(type(value))
            value.popped_by.append(instruction)
            pop_count += 1
            return value

        def push(value):
            nonlocal push_count
            if not hasattr(instruction, 'pushes_values'):
                instruction.pushes_values = defaultdict(set)
                instruction.pushes_types = defaultdict(set)
            stack.append(value)
            instruction.pushes_values[push_count].add(value)
            instruction.pushes_types[push_count].add(type(value))
            push_count += 1
            if value.pushed_by is None:
                value.pushed_by = instruction

        if instruction.opname.endswith('GLOBAL'):
            self.globals.append(instruction)

        if instruction.opname in ['LOAD_FAST', 'LOAD_CONST', 'LOAD_GLOBAL']:
            if isinstance(instruction.argval, int):
                push(Int(instruction.argval, instruction))
            else:
                if instruction.argval in type_map:
                    push(
                        type_map[instruction.argval](
                            value=instruction.argval,
                            instruction=instruction,
                        )
                    )
                else:
                    push(Var(instruction.argval, instruction=instruction))
        elif instruction.opname in ['POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE']:
            pop()
        elif instruction.opname in ['STORE_FAST']:
            type_map[instruction.argval] = type(pop())
        elif instruction.opname in ['STORE_GLOBAL']:
            pop()
            self.mutated_globals.append(instruction)
        elif instruction.opname in ['DELETE_GLOBAL']:
            self.mutated_globals.append(instruction)
        elif instruction.opname in ['JUMP_FORWARD']:
            pass  # does not effect the stack
        elif instruction.opname in ['COMPARE_OP']:
            pop()
            pop()
            push(Bool())  # strictly, rich comparisons allow for non-bool return types
        elif instruction.opname in ['UNARY_NEGATIVE', 'UNARY_POSITIVE']:
            push(pop())
        # todo this section is a bit messy -- clean it up
        elif instruction.opname in ['BINARY_SUBTRACT', 'INPLACE_SUBTRACT',
                                    'BINARY_ADD', 'INPLACE_ADD', 'BINARY_MULTIPLY',
                                    'BINARY_MODULO', 'BINARY_FLOOR_DIVIDE',
                                    'BINARY_POWER', 'BINARY_RSHIFT', 'BINARY_LSHIFT',
                                    'BINARY_OR', 'BINARY_AND',
                                    ]:
            a = pop()
            b = pop()
            if isinstance(a, Int) and isinstance(b, Int):
                push(Int())
            else:
                push(Var())
        elif instruction.opname in ['BINARY_TRUE_DIVIDE']:
            a = pop()
            b = pop()
            if isinstance(a, Int) and isinstance(b, Int):
                push(Float())
            else:
                push(Var())
        elif instruction.opname in ['BINARY_SUBSCR']:
            # todo: can we statically type tuples?
            pop()
            pop()
            push(Var())
        elif instruction.opname in ['RETURN_VALUE']:
            assert len(stack) == 1
            pop()
        elif instruction.opname in ['CALL_FUNCTION']:
            assert len(stack) >= 1 + instruction.arg
            args = [pop() for _ in range(instruction.arg)]
            function: Var = pop()

            # see calling_functions entries 3/4 for more detail

            # assert: since function is on the stack, we must not have branched
            # in such a way that two different functions could be called

            self.calls_for_func[function.pushed_by].append(instruction)
            self.funcs_for_call[instruction].append(function.pushed_by)

            if (isinstance(function, Function)
                    and function.arg_types and function.return_type
                    and all(
                        type(arg) is arg_type
                        for arg, arg_type in zip(args, function.arg_types))):
                push(function.return_type())
            elif isinstance(function, Var):
                # maybe we can figure out
                push(Var(instruction=instruction))
            else:
                push(Var())
        elif instruction.opname == 'BUILD_TUPLE':
            tuple_size = instruction.arg
            tuple_args = [pop() for _ in range(tuple_size)]
            push(Tuple(tuple_args, instruction))
        elif instruction.opname == 'ROT_TWO':
            # explicitly don't use push or pop macros
            stack[-2:] = stack[-2:][::-1]
        else:
            raise ValueError(f'unexpected opcode: {instruction}')

    def to_tree(self, cfg: NiceCFG):
        # poorly named -- this essentially does basic type checking
        # runs over the CFG in-order.
        stack = []
        root_block = cfg.cfg.blocks[0]  # todo nicer api

        # currently we only keep the types for our function
        # in the future it would be nice to have all module functions,
        # as well as some of the builtins
        type_map = {int: Int}  # todo meaningfully support non-int types
        types = {x: type_map.get(d, Var) for (x, d) in typing.get_type_hints(cfg.func).items()}
        arguments = [types.get(x, Var) for x in cfg.func.__code__.co_varnames]
        ret = types.get('return', Var)

        self.to_tree_subset(
            root_block, stack,
            {
                **types,
                cfg.func.__name__: Function.factory(
                    1,
                    arg_types=arguments,
                    return_type=ret
                )
            }
        )

    def to_tree_subset(self, block: ControlFlowGraph.Block, stack, type_map):
        # print(f'--- START BLOCK {block.offset} {stack} ---')
        self.block_starting_stacks[block].append(stack.copy())

        for instruction in block.instructions:
            self.mutate_stack(stack, instruction, type_map)
            # print(instruction.opname, '\t', stack)

        # print(f'--- END BLOCK {block.offset} {stack} ---')
        self.block_ending_stacks[block].append(stack)

        # avoid blowup
        if not stack and any(type_map == map_ for map_ in self.block_ending_type_maps[block]):
            # we already did this, so stop
            return
        self.block_ending_type_maps[block].append(type_map.copy())

        for child in block.children:
            if child.offset <= instruction.offset:
                continue  # if it's a backwards jump, we already covered this
                # do we need to check the start and end stacks are the same?

            # assert not stack
            new_stack = stack.copy()  # it should be empty though
            self.to_tree_subset(child, new_stack, type_map.copy())
            # we can't assert the new stack is empty, since it might be an old copy
            # indeed even looking at it here is kind of a bad idea

