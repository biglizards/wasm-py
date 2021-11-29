from wasmer import engine, Store, Module as w_Module, Instance
from wasmer_compiler_cranelift import Compiler

import ws_struct
from main_old import Module, Memory, Func


def test_either_can_store_and_access():
    base_addr = '(i32.const 1)'
    test_str = '(i64.const 3544952156018063160)'

    mod = Module(
        Memory(1, export='memory'),
        Func(
            args=[],
            return_type='',
            instructions=[
                ws_struct.Either.set('b', base_addr, value=test_str),
            ],
            export='mem_test'
        )
    )

    wasm = mod.compile()
    store = Store(engine.JIT(Compiler))
    instance = Instance(w_Module(store, wasm))

    instance.exports.mem_test()
    memory = instance.exports.memory.uint8_view()[0:20]
    assert memory == [0, 0, 0, 0, 0, 0, 0, 0, 0, 56, 55, 54, 53, 52, 51, 50, 49, 0, 0, 0]



