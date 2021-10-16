(module
 (memory (export "memory") 1 10)
 (func (export "mem_test") (param $n i32)
    i32.const 0     ;; base address
    i32.const 1234  ;; value
    i32.store16 (i32.const 0) (i32.const 0)   ;; alignment, offset
 )
)