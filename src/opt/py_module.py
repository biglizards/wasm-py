# Rough way this works:
# PyModule stores all the functions, globals, etc from the module we're compiling.
# it has four phases:
# 1. Collection - gather up all of the functions, globals, etc, just as python objects.
# 2. Analysis - now we have all the functions, we can ask questions (like which globals are immutable)
# 3. Optimisation - re-ordering or changing instructions, like function calls
# 4. Code generation - this probably shouldn't be part of opt, but rather have it's own sub-package
#                      (currently it's just code_generation.py)

# So, we currently have a CodeGenerator that does mostly the same thing
# What we probably want is to keep optimisations using bytecode
# (or some very similar intermediate)
# and then leave code generation to purely deal with the IR -> WASM conversion, and all the hacks that entails
# so the CodeGenerator has a PythonModule, and interacts with that until it's ready to emit code.

# this awkwardly means we have two classes that are called *Module -- fine, whatever.
from types import FunctionType
from typing import Any

from opt.analyse import Analyzer
from opt.cfg import NiceCFG
from opt.main import InstructionList


class PythonModule:
    def __init__(self):
        self.functions: dict[str, Any] = {}
        self.cfgs: dict[str, NiceCFG] = {}
        self.phase = 1  # state machine: collection, then analysis, then optimisation

        # analysis variables:
        self.all_globals = set()
        self.mutated_globals = set()

    def add_function(self, func: FunctionType, name: str):
        # as a function, we have arguments. There's a lot of ways you can confuse me:
        # (x, / y), (x=1), (*x, y)
        # for now, we assume all arguments are positional only (that is, all functions end in an implicit /)
        # and we also assume all variables are i32 (this is actually a valid assumption, because we use 32-bit pointers)
        # todo actually check this at compile time

        if self.phase != 1:
            raise RuntimeError(f'Tried to add function during phase {self.phase}!')
        if name in self.functions:
            print(f'warning: overwriting function named {func}')

        self.functions[name] = func
        self.cfgs[name] = NiceCFG(func)

    def analyse(self):
        if self.phase != 1:
            raise RuntimeError(f'Tried to move to analysis during phase {self.phase}!')
        self.phase = 2

        for name, cfg in self.cfgs.items():
            analyzer = cfg.cfg.analyzer
            analyzer.to_tree(cfg)
            analyzer.generate_stack_sizes()
            pairs = analyzer.get_push_pop_pairs(cfg)

            self.mutated_globals.update(v.argrepr for v in analyzer.mutated_globals)
            self.all_globals.update(v.argrepr for v in analyzer.globals)

        # todo: analysis
        # step 1: determine immutable globals
        # i. give all globals an associated WASM global
        # ii. mark this global if it's mutated at any point

        # step 2: generate the stack machine generation/consumption tree

        # step 3: speculate about what type arguments have, given partially typed stack
        # step 4: re-analyse the module post-speculation to ensure consistency

    def optimise(self):
        if self.phase == 1:
            self.analyse()
        if self.phase != 2:
            raise RuntimeError(f'Tried to move to optimisation during phase {self.phase}!')
        self.phase = 3

        for cfg in self.cfgs.values():
            for instruction in cfg.cfg.instructions.instructions:
                self.apply_static_typing_optimisation(instruction)
                if instruction.opname == 'CALL_FUNCTION':
                    self.apply_direct_function_call_optimisation(instruction)

    def apply_direct_function_call_optimisation(self, i):
        try:
            values = i.pops_values[max(i.pops_values.keys())]
            base_func_name = next(iter(values)).pushed_by.argval
            if (
                    # we always call the same function (name)
                    all(t_func.pushed_by.argval == base_func_name for t_func in values)
                    # AND that function is a global
                    and all(t_func.pushed_by.opname == 'LOAD_GLOBAL' for t_func in values)
                    and base_func_name in self.all_globals
                    # AND it's never mutated
                    and base_func_name not in self.mutated_globals
            ):
                # then we can call it directly
                # 1. emit a `call {function_id_by_name(base_func_name)}`
                i.use_direct_function_call = True
                i.base_func_name = base_func_name
                # 2. remove the instructions emitted by the prior `LOAD_GLOBAL`(s)
                for t_func in values:
                    t_func.pushed_by.disable = True
                return
        except (AttributeError, ValueError):
            pass
        i.use_direct_function_call = False

    @staticmethod
    def apply_static_typing_optimisation(i):
        # switch on type of instruction?
        # for proof of concept reasons we only do `BINARY_ADD`, `BINARY_SUBTRACT`, and `COMPARE_OP`

        i.use_static_typing = False

        # binary funcs
        if i.opname in ['BINARY_ADD', 'BINARY_SUBTRACT', 'COMPARE_OP']:
            # 1. check both args are the same
            base_type = next(iter(i.pops_types[0]))
            if all(
                t == base_type
                for types in i.pops_types.values()
                for t in types
            ):
                # 2. mark it as allowed
                i.use_static_typing = True
                i.static_type = base_type
