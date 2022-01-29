# basically, this just loads a complex file generated by emscripten and runs it
# some support is required
import time
from functools import lru_cache

from wasmer import engine, Store, Module, Instance, ImportObject, Function, Memory, FunctionType, Type
from wasmer_compiler_cranelift import Compiler

from generate_code import CodeGenerator
from run_wasm import run_wasm


def make_instance(path='build/emcc/add2.wasm'):
    store = Store(engine.JIT(Compiler))
    module = Module(store, open(path, 'rb').read())

    # the file has some imports we need to fill in

    def emscripten_resize_heap(x: int) -> int:
        print('emscripten_resize_heap', x)
        return 0

    def emscripten_memcpy_big(x: int, y: int, z: int) -> int:
        print('emscripten_memcpy_big', x, y, z)
        return 0

    def fd_write(fd: int, iov: int, iovcnt: int, pnum: int) -> int:
        # transcribed from emscripten (i have no idea what this does)
        if fd not in {1, 2}:
            raise NotImplementedError('trying to write to a file other than stdout/err!')

        import sys
        sink = {1: sys.stdout, 2: sys.stderr}[fd]

        i32 = memory.int32_view()
        u8 = memory.uint8_view()

        num = 0
        for i in range(iovcnt):
            ptr = i32[((iov + (i * 8)) >> 2)]
            len_ = i32[((iov + (i * 8 + 4)) >> 2)]
            # i would write it as a slice, but the buffers are weird and return an int for slices of size 1
            string = ''.join(chr(u8[ptr + j]) for j in range(len_))
            print(string, end='', file=sink)
            num += len_
        i32[pnum >> 2] = num
        return 0

    def fd_close(x: int) -> int:
        raise RuntimeError('fd_close called!', x)

    def fd_seek(x: int, y: int, z: int, a: int) -> int:
        raise RuntimeError('fd_seek called!', x, y, z, a)

    def setTempRet0(x: int):
        print('setTempRet0', x)
        return

    def emscripten_notify_memory_growth(x: int):
        # print('setTempRet0', x)
        return

    def proc_exit(x: int):
        if x != 0:
            raise RuntimeError('process exited with non-zero code!')

    import_object = ImportObject()
    import_object.register(
        'env', {
            'emscripten_resize_heap': Function(store, emscripten_resize_heap),
            'emscripten_memcpy_big': Function(store, emscripten_memcpy_big),
            'setTempRet0': Function(store, setTempRet0),
            'emscripten_notify_memory_growth': Function(store, emscripten_notify_memory_growth)
        }
    )
    import_object.register(
        'wasi_snapshot_preview1', {
            'fd_write': Function(store, fd_write),
            'fd_close': Function(store, fd_close),
            'fd_seek': Function(store, fd_seek, FunctionType([Type.I32, Type.I64, Type.I32, Type.I32], [Type.I32])),
            'proc_exit': Function(store, proc_exit)
        }
    )

    instance = Instance(module, import_object)
    memory: Memory = instance.exports.memory

    return instance


def main():
    g = CodeGenerator()
    wasm = g.wasm_module.compile()
    i = run_wasm(wasm)

    assert i.exports.fib(1) == 1
    assert i.exports.fib(2) == 2
    assert i.exports.fib(3) == 3
    assert i.exports.fib(4) == 5
    assert i.exports.fib(5) == 8

    # assert i.exports.main4(5) == 8
    assert i.exports.main2(6) == 13
    assert i.exports.main2(12) == 233
    assert i.exports.main2(13) == 377

    assert i.exports.main4(6) == 13
    assert i.exports.main4(12) == 233
    assert i.exports.main4(13) == 377

    assert i.exports.main5(6) == 13
    assert i.exports.main5(12) == 233
    assert i.exports.main5(13) == 377
    assert i.exports.main5(23) == 46368

    # ok this is a bit silly but lets go for it
    pair = i.exports.pair(5, 27)
    assert i.exports.first(pair) == 5
    assert i.exports.second(pair) == 27


    # assert i.exports.main5(23) == 46368, i.exports.fib(23)

    # for x in range(35):
    #     print(x, i.exports.main5(x), i.exports.main5(x), i.exports.fib(x))

    # for x in range(-300, 300):
    #     b = i.exports.add_long(x, 3)
    #     assert b == (x+3)

    bench(i.exports.main2)
    bench(i.exports.main3)
    bench(i.exports.main4)
    bench(i.exports.main5)


def bench(f, n=35):
    answer = fib(n)
    t = time.time()
    assert f(n) == answer
    print(f'took {(time.time() - t) * 1000:.0f}ms', )


@lru_cache
def fib(n):
    if n <= 1:
        return 1
    return fib(n - 1) + fib(n - 2)


def main2():
    import parse_wat
    module = parse_wat.load('build/emcc/add2.wasm')
    print(module)

    # open('add_out.wasm', 'wb').write(ans.compile())


if __name__ == '__main__':
    main()
