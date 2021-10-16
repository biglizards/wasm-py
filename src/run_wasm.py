from wasmer import engine, Store, Module, Instance
from wasmer_compiler_cranelift import Compiler


def run_wasm(wasm):
    # Let's define the store, that holds the engine, that holds the compiler.
    store = Store(engine.JIT(Compiler))

    # Let's compile the module to be able to execute it!
    module = Module(store, wasm)

    # Now the module is compiled, we can instantiate it.
    instance = Instance(module)

    # Call the exported `sum` function.
    result = instance.exports.sum(5, 37)

    return result


# noinspection PyArgumentList,PyUnresolvedReferences
def run_wasm_function(wasm, func_name, *args):
    store = Store(engine.JIT(Compiler))
    instance = Instance(Module(store, wasm))
    rv = getattr(instance.exports, func_name)(*args)
    return rv


def main():
    wasm = '''
(module
 (memory (export "memory") 1 10)
 (func (export "mem_test") (param $n i32)   
    i32.const 1       ;; base address
    ;;i32.const 1234    ;; value
    (i32.store16 offset=1
     ;;(i32.const 1)      ;; base address
     (i32.const 1234)   ;; value
    )
 )
)    '''
    store = Store(engine.JIT(Compiler))
    instance = Instance(Module(store, wasm))
    rv = getattr(instance.exports, "mem_test")(0)
    print(
        list(map(
            chr,
            instance.exports.memory.uint8_view()[0:10]
        ))
    )



if __name__ == '__main__':
    main()
