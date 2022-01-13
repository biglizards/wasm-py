from __future__ import annotations

import dis
import functools
import heapq
import pprint
from collections import deque, defaultdict


class Var:
    def __init__(self, value=None, instruction=None):
        self.value = value
        self.scope = {
            'LOAD_CONST': 'const',
            'LOAD_FAST': 'local',
            'LOAD_GLOBAL': 'global',
        }.get(getattr(instruction, 'opname', None))
        self.pushed_by = instruction

    def __repr__(self):
        if self.value:
            return f'Var({repr(self.value)})'
        else:
            return f'Var()'


class Int(Var):
    def __repr__(self):
        if self.value is not None:
            return f'Short({repr(self.value)})'
        return f'Short()'


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
            return f'({repr(self.arg_types)} => {repr(self.return_type)})'
        return f'Function({self.arg_count}, {repr(self.arg_types)}, {repr(self.return_type)})'


def mutate_stack(stack, instruction, type_map):
    if instruction.opname in ['LOAD_FAST', 'LOAD_CONST', 'LOAD_GLOBAL']:
        if isinstance(instruction.argval, int):
            stack.append(Int(instruction.argval, instruction))
        else:
            if instruction.argval in type_map:
                stack.append(
                    type_map[instruction.argval](
                        value=instruction.argval,
                        instruction=instruction,
                    )
                )
            else:
                stack.append(Var(instruction.argval, instruction=instruction))
    elif instruction.opname in ['POP_JUMP_IF_FALSE']:
        stack.pop()
    elif instruction.opname in ['COMPARE_OP']:
        stack.pop()
        stack.pop()
        stack.append(Bool())  # strictly, rich comparisons allow for non-bool return types
    elif instruction.opname in ['BINARY_SUBTRACT', 'BINARY_ADD']:
        a = stack.pop()
        b = stack.pop()
        if isinstance(a, Int) and isinstance(b, Int):
            stack.append(Int())
        else:
            stack.append(Var())
    elif instruction.opname in ['RETURN_VALUE']:
        assert len(stack) == 1
    elif instruction.opname in ['CALL_FUNCTION']:
        assert len(stack) >= 1 + instruction.arg
        args = [stack.pop() for _ in range(instruction.arg)]
        function: Var = stack.pop()

        # see calling_functions entries 3/4 for more detail

        # assert: since function is on the stack, we must not have branched
        # in such a way that two different functions could be called
        assert not hasattr(function.pushed_by, 'delay')
        assert not hasattr(instruction, 'func_push_instruction')

        function.pushed_by.delay = True
        instruction.func_push_instruction = function.pushed_by

        if (isinstance(function, Function)
                and function.arg_types and function.return_type
                and all(
                    type(arg) is type(arg_type)
                    for arg, arg_type in zip(args, function.arg_types))):
            stack.append(function.return_type)
        elif isinstance(function, Var):
            # maybe we can figure out
            stack.append(Var(instruction=instruction))
        else:
            stack.append(Var())
    else:
        raise ValueError(f'unexpected opcode: {instruction}')


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


# We need to split code into blocks based on where jumps start and end
# we also want to know, for each jump target: where is the first and last place it's jumped to


def new_cfg(code) -> ControlFlowGraph:
    il = InstructionList(list(dis.Bytecode(code)))
    return ControlFlowGraph.new(il)


class InstructionList:
    def __init__(self, instructions: list[dis.Instruction]):
        self.instructions = instructions
        self.indices = {
            x.offset: i for i, x in enumerate(self.instructions)
        }
        self.indices_inv = {
            i: x.offset for i, x in enumerate(self.instructions)
        }


class ControlFlowGraph:
    class Block:
        def __init__(self):
            self.instructions: list[dis.Instruction] = []
            self.inward_edges = []
            self.outwards_edges = []
            self.offset: int = -1  # guaranteed to be valid after CFG is init

        def add(self, i: dis.Instruction):
            self.instructions.append(i)
            if self.offset == -1:
                self.offset = i.offset

        def __repr__(self):
            return f'<Block(\n{pprint.pformat(self.instructions)},\n\t{pprint.pformat(self.outwards_edges)})>'

    class Loop:
        def __init__(self, blocks: list[ControlFlowGraph.Block]):
            self.blocks = blocks
            self.offset = self.blocks[0].offset

    def __init__(self, blocks: dict[int, Block], instructions: InstructionList):
        self.blocks = blocks
        self.instructions = instructions

        self.offset_to_index = {instruction.offset: i for i, instruction in enumerate(self.instructions.instructions)}
        self.index_to_offset = {i: instruction.offset for i, instruction in enumerate(self.instructions.instructions)}

        to_tree(self.instructions)

    def __repr__(self):
        return f'<ControlFlowGraph({self.blocks})>'

    @staticmethod
    def new(instructions: InstructionList):
        # this takes two passes
        # 1. separate into blocks
        # 2. generate the edges

        blocks: dict[int, ControlFlowGraph.Block] = {}
        current_block = ControlFlowGraph.Block()

        def new_block():
            nonlocal current_block
            if current_block.instructions:
                blocks[current_block.instructions[0].offset] = current_block
            current_block = ControlFlowGraph.Block()

        for instruction in instructions.instructions:
            if instruction.is_jump_target:
                new_block()

            current_block.add(instruction)

            if instruction.opname in jumps:
                new_block()
        new_block()

        # time for pass 2
        for block in blocks.values():
            # invariant: blocks are non-empty
            # invariant: blocks contain at most one jump, which (if it exists) is at the end
            jump = block.instructions[-1]

            try:
                if jump.opname not in abs_jumps:
                    next_offset = instructions.indices_inv[instructions.indices[jump.offset] + 1]
                    target = blocks[next_offset]
                    block.outwards_edges.append(target.offset)
                    target.inward_edges.append(block.offset)
            except KeyError:
                pass  # end of function

            if jump.opname in jumps:
                target = blocks[jump.argval]
                block.outwards_edges.append(target.offset)
                target.inward_edges.append(block.offset)

        return ControlFlowGraph(blocks, instructions)

    def prev_offset(self, offset):
        # this is unbelievably dumb
        return self.index_to_offset[self.offset_to_index[offset] - 1]

    def next_offset(self, offset):
        return self.index_to_offset[self.offset_to_index[offset] + 1]

    def sort_groups(self, a):
        if isinstance(a, self.Loop):
            a = a.blocks[0]
        return a.offset

    def order_blocks(self, root=None) -> tuple[list[Block], list[Loop]]:
        # generate a topological ordering (considering only the forward edges)
        # this means we must put all of a blocks parents in before that block
        # additionally, we don't break up loops

        # lemma: other than loops, sorting by offset gives a topological order
        # proof: once we finish grouping loops, we have no backwards branches, so it's a DAG

        # iterate over all nodes in a mostly breadth-first way
        if root is None:
            root = self.blocks[0]

        order = []

        visited = {root.offset}
        queue = [root.offset]

        while queue:
            node_offset = heapq.heappop(queue)
            node = self.blocks[node_offset]

            # question: is root a loop header (ie do any backwards edges end in it)
            for loop_end in node.inward_edges:
                if loop_end >= node_offset:
                    break
            else:
                # not a loop header
                order.append(node)
                for child in node.outwards_edges:
                    if child > node_offset and child not in visited:
                        heapq.heappush(queue, child)
                        visited.add(child)
                continue

            # root is a loop header

            # now we figure out which side the loop is on
            # we do this by working backwards from the end, in a depth-first way, on forwards edges
            # because forwards edges form a DAG, we never get stuck

            node_ = self.blocks[loop_end]
            while node_ is not node and node_.offset not in node.outwards_edges:
                for parent in node_.inward_edges:
                    if parent >= node_.offset:
                        continue  # don't touch inner loops yet -- we'll handle that case later
                    node_ = self.blocks[parent]

            loop_start = node_
            loop_blocks = [
                node
            ]

            # if the loop is a single block, don't include children in the loop
            if loop_start is not node:
                blocks, _loops = self.order_blocks(loop_start)
                loop_blocks.extend(
                    blocks
                )

            order.append(self.Loop(loop_blocks))

            # ok now lets do the other branch
            # (there should only be 1 or 0)
            for child in node.outwards_edges:
                if child > node_offset and child != loop_start.offset and child not in visited:
                    heapq.heappush(queue, child)
                    visited.add(child)

        order.sort(
            key=self.sort_groups
        )

        # split out the loops from the order now
        order2 = []
        loops = []

        for item in order:
            if isinstance(item, self.Loop):
                order2.extend(item.blocks)
                loops.append(item)
            else:
                order2.append(item)

        return order2, loops

    def positive_edges(self) -> list[tuple[int, int]]:
        edges = []
        # fun fact that we will probably rely on:
        # the iteration order here is sorted by offset
        for offset, block in self.blocks.items():
            edges.extend((offset, child) for child in block.outwards_edges if child > offset)

        return edges

    def stackify(self):
        order, loops = self.order_blocks()
        order_index = {i: block.offset for i, block in enumerate(order)}
        order_index_inv = {block.offset: i for i, block in enumerate(order)}

        # def prev_block(block) -> int:  # returns an offset
        #     if isinstance(block, (self.Block, self.Loop)):
        #         return order_index[order_index_inv[block.offset] - 1]
        #     elif isinstance(block, int):  # we assume it's an offset
        #         return prev_block(self.blocks[block])

        def consecutive(a, b):
            return order_index_inv[b] - order_index_inv[a] == 1

        def most_general_scope_containing_x_but_ending_before_y(x, y):
            most_general_scope = (x, x)
            for start, end, _label in scopes:
                if (
                        (start <= x <= end)  # contains x
                        and (y >= end)  # ends before y
                        # if a scope opens after another one, it must end before it ends
                        # so we only need to expand the start to find the most general one
                        and (most_general_scope[0] > start
                             or (most_general_scope[0] == start and most_general_scope[1] <= end))  # is more general
                ):
                    most_general_scope = (start, end)

            return most_general_scope

        # finally we can apply the stackify algorithm to generate a scope tree
        # to do this, we iterate over the forward edges in the tree
        # if they're consecutive, continue
        # otherwise, place a new `block` scope S such that
        #  - S ends immediately before the end of the edge
        #  - S starts immediately before the outermost scope O such that
        #    - O closes between the jump and the end of S

        # we could probably use an interval tree (to get O(n log n) instead of O(n^2)),
        # but i can't imagine we'll ever see big enough n for this to be a problem
        # (maybe we could even make it linear by using a control flow stack?)

        pos_edges = self.positive_edges()
        scopes = [
            (b.blocks[0].offset, b.blocks[-1].instructions[-1].offset, 'loop')
            for b in loops
        ]

        for edge_start, edge_end in pos_edges:
            if consecutive(edge_start, edge_end):
                continue
            # we need to place a new block scope
            scope_end = self.prev_offset(edge_end)  # ends immediately before the end of the edge

            # now we iterate over all the scopes O in increasing order of specificity
            # end of this block:
            jump = self.blocks[edge_start].instructions[-1].offset
            outer_est_scope = most_general_scope_containing_x_but_ending_before_y(x=jump, y=scope_end)
            scope_start = outer_est_scope[0]
            if scope_start == jump:
                # that is actually very wrong
                scope_start = edge_start
            scopes.append((scope_start, scope_end, 'block'))

        return scopes, order

    def generate_control_flow_instructions(self):
        scopes, order = self.stackify()

        # re-write the control flow instructions into 3 easy to use dicts:
        # 1+2. where do we put the start/end instructions?
        # 3. if i'm jumping to `offset`, what label do i jump to?
        before_instruction = defaultdict(list)
        after_instruction = defaultdict(list)
        forward_jump_table = {}
        backward_jump_table = {}

        for start, end, label in scopes:
            name = f'{label}_{start}_{end}'
            before_instruction[start].append(f'{label} ${name}')
            after_instruction[end].append(f'end')

            if label == 'loop':
                backward_jump_table[start] = name
            elif label == 'block':
                forward_jump_table[self.next_offset(end)] = name
            else:
                raise RuntimeError('unreachable')

        # flatten order
        flat_order = [i for b in order for i in b.instructions]

        return flat_order, before_instruction, after_instruction, forward_jump_table, backward_jump_table


def to_tree(instr_list: InstructionList):
    stack = []
    to_tree_subset(
        instr_list, 0, stack,
        {
            'n': Int,
            'fib': Function.factory(
                1,
                arg_types=[Int],
                return_type=Int
            )
        }
    )


def to_tree_subset(instructions, start, stack, type_map):
    for instruction in instructions.instructions[start:]:
        mutate_stack(stack, instruction, type_map)
        print(instruction.opname, '\t', stack)
        if instruction.opname in ['POP_JUMP_IF_FALSE']:
            print("--- START BLOCK ---")
            new_stack = []  # stack.copy()
            # bug?? arg seems to be the same as the index here
            addr = instruction.arg  # instructions.indices[instruction.arg]
            to_tree_subset(instructions, addr, new_stack, type_map)
            print("--- END BLOCK ---")
        elif instruction.opname in ['RETURN_VALUE']:
            return


def main():
    from tests.example_files.flow_control import mini_monster, monster

    bytecode = dis.Bytecode(monster)
    instr_list = InstructionList(list(bytecode))

    cfg = ControlFlowGraph.new(instr_list)

    dis.dis(monster)

    # pprint.pprint(cfg.blocks)
    # print('\n\n')
    # pprint.pprint(cfg.order_blocks())
    # print('\n\n')
    # pprint.pprint(cfg.positive_edges())
    # print('\n\n')
    pprint.pprint(cfg.generate_control_flow_instructions())


if __name__ == '__main__':
    main()
