( module
    (type $funcsig (func ( param i32 ) ( param i32 ) ( result i32 )))
    (table 1 funcref)
    (elem (i32.const 0) $add $add1)

    ( func $add ( export "sum" ) ( param i32 ) ( param i32 ) ( result i32 )
        local.get 0
        local.get 1
        i32.add
    )
    ( func $add1 ( export "add1" ) ( param i32 ) ( result i32 )
        local.get 0
        i32.const 1
        i32.const 0  ;; this is the pointer to the function
        call_indirect (type $funcsig)
    )
)
