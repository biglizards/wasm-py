//
// Created by dave on 19/11/2021.
//

#ifndef WASM_PY_SHORT_H
#define WASM_PY_SHORT_H

#include "object.h"

typedef struct _short {
    PyObject Base;
    int value;
} Short;

// we want some kind of cool public interface to make a new item of a given type
// something like `new_object(Type, args...)` would be good, but hard to meaningfully type
// lets just make all constructors public and think about it later

Short* new_short(int a);
Short* short_fib(Short* a);

#define SHORT_SMALL_START 0
#define SHORT_SMALL_END 256
extern Short small_shorts[];


#endif //WASM_PY_SHORT_H
