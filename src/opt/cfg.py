from __future__ import annotations

import dis
import heapq
import pprint
from collections import defaultdict

from opt.analyse import Analyzer
from opt.main import InstructionList, jumps, abs_jumps


# We need to split code into blocks based on where jumps start and end
# we also want to know, for each jump target: where is the first and last place it's jumped to


def new_cfg(func) -> ControlFlowGraph:
    il = InstructionList(list(dis.Bytecode(func)))
    return ControlFlowGraph.new(il)


def big_intersection(iterator) -> set:
    total = next(iterator)
    for item in iterator:
        total = total.intersection(item)
    return total


class ControlFlowGraph:
    class Block:
        def __init__(self):
            self.instructions: list[dis.Instruction] = []
            self.inward_edges = []
            self.outwards_edges = []
            self.offset: int = -1  # guaranteed to be valid after CFG is init

            self.parents: list[ControlFlowGraph.Block] = []
            self.children: list[ControlFlowGraph.Block] = []

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

    def __init__(self, blocks: dict[int, ControlFlowGraph.Block], instructions: InstructionList):
        self.blocks: dict[int, ControlFlowGraph.Block] = blocks
        self.instructions = instructions
        self.analyzer = Analyzer()

        self.offset_to_index = {instruction.offset: i for i, instruction in enumerate(self.instructions.instructions)}
        self.index_to_offset = {i: instruction.offset for i, instruction in enumerate(self.instructions.instructions)}

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

    def compute_dominance(self, root):
        # taken from wikipedia, todo who really came up with it
        # theoretically quadratic, practically linear
        dom = {node: set(self.blocks.keys()) for node in self.blocks.keys()}
        dom[root] = {root}

        flag = True
        while flag:
            flag = False
            for node in self.blocks.values():
                if node.offset is root:
                    continue
                new_dom = big_intersection(dom[p] for p in node.inward_edges).union({node.offset})
                if new_dom != dom[node.offset]:
                    flag = True
                    dom[node.offset] = new_dom

        return dom

    def order_blocks(self, root=None) -> tuple[list[Block], list[Loop]]:
        # generate a topological ordering (considering only the forward edges)
        # this means we must put all of a block's parents in before that block
        # additionally, we don't break up loops

        # lemma: other than loops, sorting by offset gives a topological order
        # proof: once we finish grouping loops, we have no backwards branches, so it's a DAG

        # iterate over all nodes in a mostly breadth-first way
        if root is None:
            root = self.blocks[0]

        dom = self.compute_dominance(root.offset)

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

            # node is a loop header

            # the loop body is every node that the header dominates
            dominated_nodes2 = {n for (n, dom_by) in dom.items() if node.offset in dom_by}
            dominated_nodes = {node.offset}

            def explore(node_):
                pass
                if all(n in dominated_nodes for n in node_.inward_edges):
                    dominated_nodes.add(node_.offset)
                    for n in node_.outwards_edges:
                        explore(self.blocks[n])

            for child in node.outwards_edges:
                explore(self.blocks[child])

            assert dominated_nodes2 == dominated_nodes

            # step 2: there might be sub-loops within this loop, so recurse to find them
            # TODO

            loop_blocks = [self.blocks[n] for n in sorted(dominated_nodes)]
            order.append(self.Loop(loop_blocks))

            # # ok now lets do the other branch
            # # (there should only be 1 or 0)
            for child in node.outwards_edges:
                if child > node.offset and child not in dominated_nodes and child not in visited:
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
        # order_index = {i: block.offset for i, block in enumerate(order)}
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
                        # if a scope opens after another one, the inner scope must end before the outer one end
                        # (ie: scopes are always nested)
                        # so we only need to expand the start to find the most general one
                        and (most_general_scope[0] > start
                             or (most_general_scope[0] == start and most_general_scope[1] <= end))  # is more general
                ):
                    most_general_scope = (start, end)

            return most_general_scope

        # finally we can generate a scope tree
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
            scope_start, _ = most_general_scope_containing_x_but_ending_before_y(x=jump, y=scope_end)
            if scope_start == jump:
                # that is actually very wrong
                scope_start = edge_start
            scopes.append((scope_start, scope_end, 'block'))

        # finally: sort the scopes into a tree structure
        scopes = list(sorted(scopes, key=lambda x: (x[0], x[1])))

        # 1. check forward inward scope stack consistency
        # (I don't think any backwards edges can have inputs or outputs)
        # for each forward edge:
        #   i. find the outermost block scope it crosses
        #  ii. check both sides of that scope have the same stack size
        # iii. note down that the scope produces $n$ outputs

        scope_edge_stack_size = {}

        for edge_start, edge_end in pos_edges:
            scope_end = self.prev_offset(edge_end)
            jump = self.blocks[edge_start].instructions[-1].offset
            scope_start, _ = most_general_scope_containing_x_but_ending_before_y(x=jump, y=scope_end)
            # todo: do we need to do the same hack? I dont think so
            # so now we have a pseudo-scope for this edge -- does it cross any actual scopes?
            scope = (scope_start, scope_end, 'block')
            if scope not in scopes:
                continue

            block_start = self.blocks[edge_start]
            block_start_stack_end = self.analyzer.block_ending_stack_size[block_start]
            block_end = self.blocks[edge_end]
            block_end_stack_start = self.analyzer.block_starting_stack_size[block_end]
            assert block_start_stack_end == block_end_stack_start

            if scope not in scope_edge_stack_size:
                scope_edge_stack_size[scope] = block_start_stack_end

            assert scope_edge_stack_size[scope] == block_start_stack_end

        # 2. change scopes to have results
        # 3 (extra: also have inputs)

        return scopes, order, scope_edge_stack_size

    def generate_control_flow_instructions(self):
        scopes, order, scope_edge_stack_size = self.stackify()

        # re-write the control flow instructions into 4 easy to use dicts:
        # 1+2. where do we put the start/end instructions?
        # 3+4. if i'm jumping to `offset`, what label do i jump to?
        before_instruction = defaultdict(list)
        after_instruction = defaultdict(list)
        forward_jump_table = {}
        backward_jump_table = {}

        for scope in scopes:
            start, end, label = scope
            results = scope_edge_stack_size.get(scope, 0)
            name = f'{label}_{start}_{end}'
            if results == 0:
                start_instr = f'{label} ${name}'
            else:
                start_instr = f'{label} ${name} (result {"i32 " * results})'
            before_instruction[start].insert(0, start_instr)  # bit slow, what can you do, eh
            after_instruction[end].append(f'end (; {label} ${name} ;)')

            if label == 'loop':
                backward_jump_table[start] = name
            elif label == 'block':
                forward_jump_table[self.next_offset(end)] = name
            else:
                raise RuntimeError('unreachable')

        # flatten order
        flat_order = [i for b in order for i in b.instructions]

        return flat_order, before_instruction, after_instruction, forward_jump_table, backward_jump_table


class NiceCFG:
    """A wrapper around CFG to make it a little easier to use"""
    def __init__(self, func):
        self.cfg = new_cfg(func)
        self.func = func

        for b in self.cfg.blocks.values():
            b.children = [self.cfg.blocks[c] for c in b.outwards_edges]
            b.parents = [self.cfg.blocks[c] for c in b.inward_edges]

    def flatten(self):
        bytecode, before, after, fjt, bjt = self.cfg.generate_control_flow_instructions()

        flat_code = [
            x
            for i in bytecode
            for x in [
                *before[i.offset],
                i,
                *after[i.offset]
            ]
        ]
        print('fjt', fjt)
        print('bjt', bjt)

        def jump(offset, target):
            if target > offset:
                return fjt[target]
            return bjt[target]

        return flat_code, jump


def main():
    from tests.example_files.flow_control import monster

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
