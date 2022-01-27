//
// Created by dave on 12/11/2021.
//

#ifndef WASM_PY_GLUE_H
#define WASM_PY_GLUE_H

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
// change: usually it's `extern symbol`. I don't know why this change is needed.
#define PyAPI_DATA(symbol) extern symbol
#define PyTypeObject Type

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


#define eprintf(...) fprintf (stderr, __VA_ARGS__)
static inline void* PyErr_NoMemory() {
    PANIC("out of memory!");
}

#define TYPE_HEAD PyVarObject_HEAD_INIT(NULL, 0)

#endif //WASM_PY_GLUE_H
