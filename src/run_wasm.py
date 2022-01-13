import sys

from wasmer import engine, Store, Module, Instance, Memory, ImportObject, Function, FunctionType, Type
from wasmer_compiler_cranelift import Compiler
from wasmer_compiler_singlepass import Compiler as C2

# from generate_code import CodeGenerator


def run_wasm(wasm):
    e = engine.JIT(Compiler)
    store = Store(e)
    module = Module(store, wasm)

    # the file has some imports we need to fill in
    # specifically: emscripten_resize_heap, emscripten_memcpy_big, fd_write, and setTempRet0
    # not all of these seem to be used, but it complains if we don't have them
    # more may be added as we do more complex things with C
    # fun fact: most of these have been removed now, due to being totally useless.
    # but i'll keep them around for legacy compatablity for a while

    # I have never seen these 4 be called -- they seem to be vestigial, as the heap grows itself.
    def emscripten_resize_heap(x: int) -> int:
        raise RuntimeError('emscripten_resize_heap', x)

    def emscripten_memcpy_big(x: int, y: int, z: int) -> int:
        raise RuntimeError('emscripten_memcpy_big', x, y, z)

    def emscripten_notify_memory_growth(x: int):
        # raise RuntimeError('emscripten_notify_memory_growth', x)
        print('emscripten_notify_memory_growth', x)

    def setTempRet0(x: int):
        raise RuntimeError('setTempRet0', x)

    def fd_write(fd: int, iov: int, iovcnt: int, pnum: int) -> int:
        # transcribed from emscripten (i have no idea how this works)
        # reads what i can only assume to be a null-terminated string from memory into a file descriptor
        # (currently only stdout is supported)
        if fd not in {1, 2}:
            raise NotImplementedError('trying to write to a file other than stdout/err!')

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

    # Now the module is compiled, we can instantiate it.
    instance = Instance(module, import_object)
    memory: Memory = instance.exports.memory

    return instance


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
