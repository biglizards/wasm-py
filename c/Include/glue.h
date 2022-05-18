#ifndef WASM_PY_GLUE_H
#define WASM_PY_GLUE_H

#define NDEBUG

#import <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#define _PyVarObject_CAST(op) ((PyVarObject*)(op))
#define Py_SIZE(ob)             (_PyVarObject_CAST(ob)->ob_size)

#ifdef __has_builtin
#  define _Py__has_builtin(x) __has_builtin(x)
#else
#  define _Py__has_builtin(x) 0
#endif

#define Py_BUILD_ASSERT_EXPR(cond) \
    (sizeof(char [1 - 2*!(cond)]) - 1)

#define Py_BUILD_ASSERT(cond)  do {         \
        (void)Py_BUILD_ASSERT_EXPR(cond);   \
    } while(0)

#define PYLONG_BITS_IN_DIGIT 15

typedef uintptr_t       Py_uintptr_t;
typedef intptr_t        Py_intptr_t;

typedef Py_intptr_t     Py_ssize_t;

#define Py_ABS(x) ((x) < 0 ? -(x) : (x))

//#  define SIZE_MAX		(18446744073709551615UL)
/* Largest possible value of size_t. */
#define PY_SIZE_MAX SIZE_MAX
/* Largest positive value of type Py_ssize_t. */
#define PY_SSIZE_T_MAX ((Py_ssize_t)(((size_t)-1)>>1))
/* Smallest negative value of type Py_ssize_t. */
#define PY_SSIZE_T_MIN (-PY_SSIZE_T_MAX-1)

// this one is especially funny because it isn't safe
#define Py_SAFE_DOWNCAST(VALUE, WIDE, NARROW) (NARROW)(VALUE)

#undef LONG_MIN
#define LONG_MIN (-LONG_MAX - 1L)
#undef LONG_MAX
#define LONG_MAX __LONG_MAX__

#define PyAPI_FUNC(symbol) symbol
#define PyAPI_DATA(symbol) extern symbol
#define PyTypeObject Type

//#define assert(cond) do {} while (0)

#define PANIC(str) do {printf(str "\n"); assert(0); exit(-1);} while (0)
// black macro magic from https://stackoverflow.com/a/2670919
#define STRINGIZE(x) STRINGIZE2(x)
#define STRINGIZE2(x) #x
#define LINE_STRING STRINGIZE(__LINE__)
//#define assert(cond) if (!cond) PANIC(__FILE__ ":" LINE_STRING \
//                               ": Assertion Violated: `" #cond "`\n");

//static inline void print_backtrace() {
//    void* callstack[128];
//    int i, frames = backtrace(callstack, 128);
//    char** strs = backtrace_symbols(callstack, frames);
//    for (i = 0; i < frames; ++i) {
//        printf("%s\n", strs[i]);
//    }
//    free(strs);
//}
// todo: when exception handling is added, turn these into real exceptions
#define PyErr_SetString(exception, string) PANIC(string)
#define PyErr_BadInternalCall() PANIC("bad internal call!")
#define PyErr_Format(exception, string, ...) printf(string, __VA_ARGS__); PANIC("\nexception raised!")

#define PyErr_BadArgument() PANIC("error: bad argument");

#define eprintf(...) fprintf (stderr, __VA_ARGS__)
static inline void* PyErr_NoMemory() {
    PANIC("out of memory!");
}

#define TYPE_HEAD PyVarObject_HEAD_INIT(NULL, 0)
#define PyObject_Malloc malloc
#define Py_LOCAL_INLINE(type) static inline type
#define Py_ARITHMETIC_RIGHT_SHIFT(TYPE, I, J) ((I) >> (J))

/* Two gcc extensions.
   &a[0] degrades to a pointer: a different type from an array */
#define Py_ARRAY_LENGTH(array) \
    (sizeof(array) / sizeof((array)[0]) \
     + Py_BUILD_ASSERT_EXPR(!__builtin_types_compatible_p(typeof(array), \
                                                          typeof(&(array)[0]))))

#define PyErr_Occurred() 0

#define Py_IS_INFINITY(X) isinf(X)
#define Py_IS_NAN(X) isnan(X)

/* Minimum value between x and y */
#define Py_MIN(x, y) (((x) > (y)) ? (y) : (x))

/* Maximum value between x and y */
#define Py_MAX(x, y) (((x) > (y)) ? (x) : (y))

/* Absolute value of the number x */
#define Py_ABS(x) ((x) < 0 ? -(x) : (x))

#define Py_RETURN_NOTIMPLEMENTED PANIC("returning not implemented!")
#define Py_UNREACHABLE() PANIC("unreachable code reached!")

#define glue(x, y) x##y
#define glue3(x, y, z) x##y##z
#define CMP_OP(name, symbol, type) int glue(type,_##name)(PyLongObject* a, PyLongObject* b) { \
    return glue(type,_compare)(a, b) symbol 0;\
}\
int glue3(type,_##name,_direct)(PyLongObject* a, PyLongObject* b) {\
    int rv = long_##name(a, b);\
    Py_DECREF(b);\
    Py_DECREF(a);\
    return rv;\
}




#endif //WASM_PY_GLUE_H
