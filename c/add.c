#include <stdio.h>
#include <stdlib.h>

#include "short.h"

#include "glue.h"
#include "object.h"
#include "cpython/longintrepr.h"
#include "cpython/longobject.h"
#include "cpython/tupleobject.h"

//#include "Python.h"

//extern unsigned char __heap_base;
//unsigned int bump_pointer = &__heap_base;

//extern int addwat(int, int);


#define LONG(x)

//void* malloc(unsigned long n) {
//  unsigned int r = bump_pointer;
//  bump_pointer += n;
//  created_objects++;
//  return (void *)r;
//}
//
//void free(void* p) {
//  // lol
//    created_objects--;
//}



// todo: there's some weird subclassing stuff going on here in CPython
#define BINARY_FUNC(ret, name, path) ret name(PyObject* a, PyObject* b) { \
    if (a->type->path != NULL) return a->type->path(a,b);                 \
    if (b->type->path != NULL) return b->type->path(a,b);                 \
    PANIC(#name "(" #path ") Not implemented!");                          \
}

#define BINARY_FUNC2(ret, name, lens, path) ret name(PyObject* a, PyObject* b) { \
    if (a->type->lens != NULL &&  a->type->lens->path != NULL) return a->type->lens->path(a,b); \
    if (b->type->lens != NULL &&  b->type->lens->path != NULL) return b->type->lens->path(a,b); \
    PANIC(#name "(" #lens "->" #path ") Not implemented!");                                 \
}


#define BIN_OP_FUNC(name, path) BINARY_FUNC(PyObject*, name, path)
#define BIN_OP_FUNC2(name, lens, path) BINARY_FUNC2(PyObject*, name, lens, path)
#define BIN_TEST_FUNC(name, path) BINARY_FUNC(int, name, path)

BIN_OP_FUNC2(add_pyobject, tp_as_number, nb_add)
BIN_OP_FUNC2(subtract_pyobject, tp_as_number, nb_subtract)
BIN_OP_FUNC2(subscr_pyobject, tp_as_mapping, mp_subscript)
BIN_TEST_FUNC(leq_pyobject, cmp_leq)
BIN_TEST_FUNC(eq_pyobject, cmp_eq)

PyObject* fib2(PyObject* a) {
    if (leq_pyobject(a, (PyObject * ) & small_shorts[1])) {
        small_shorts[1].Base.refCount++;
        Py_DECREF(a);
        return (PyObject * ) & small_shorts[1];
    }
    small_shorts[1].Base.refCount++;
    small_shorts[2].Base.refCount++;
    Py_INCREF(a);

    return add_pyobject(
            fib2(subtract_pyobject(a, (PyObject * ) & small_shorts[1])),
            fib2(subtract_pyobject(a, (PyObject * ) & small_shorts[2]))
    );
}

PyObject* fib3(PyObject* a) {
    int bool = leq_pyobject(a, (PyObject * ) & SMALL_INT(1));
    if (bool) {
//        SMALL_INT(1).ob_base.ob_base.refCount++;
//        py_decref(a);
        return (PyObject * ) & SMALL_INT(1);
    }
//    SMALL_INT(1).ob_base.ob_base.refCount++;
//    SMALL_INT(2).ob_base.ob_base.refCount++;
    Py_INCREF(a);
    PyObject* b = fib3(subtract_pyobject(a, (PyObject * ) & SMALL_INT(1)));
    PyObject* c = fib3(subtract_pyobject(a, (PyObject * ) & SMALL_INT(2)));
    PyObject* d = add_pyobject(b, c);

    return d;
}


int fib(int a) {
    if (a <= 1) {
        return 1;
    }
    return fib(a - 1) + fib(a - 2);
}

int one = 1;

int* ptr_fib(int* a) {
    if (*a <= 1) {
        return &one;
    }
    int a1 = *a - 1;
    int a2 = *a - 2;
    int* answer2 = malloc(sizeof(int));
    *answer2 = *ptr_fib(&a1) + *ptr_fib(&a2);
    return answer2;
}

int main2(int a) {
    PyObject* obj = (PyObject*) new_short(a);
    Short* fib_out = (Short*) fib2(obj);
//    return bump_pointer;
//    printf("%d\n", created_objects);
    return fib_out->value;
}

long main5(int a) {
    PyObject* obj = PyLong_FromLong(a);
    PyObject* fib_out = fib3(obj);

//    return bump_pointer;
    printf("%d\n", created_objects);
    long result = PyLong_AsLong(fib_out);
    py_decref(fib_out);
    return result;
}

void what_the_fuck() {
    debug_print(&PyTuple_Type);
}

int flow_control_example(int a) {
    int b = a * 2;
    if (a >= 3) {
        b += 5;
    } else {
        b = b * b;
    }
    return b;
}

long add_long(int a, int b) {
    PyObject* obj = PyLong_FromLong(a);
    PyObject* obj2 = PyLong_FromLong(b);

    PyObject* result = add_pyobject(obj, obj2);

    return PyLong_AsLong(result);
}

int main_long(int a) {
    PyLongObject* obj = (PyLongObject*) PyLong_FromLong(a);

    return obj->ob_digit[0];
}


int main3(int a) {
    Short* obj = new_short(a);
    Short* fib_out = (Short*) short_fib(obj);
//    return bump_pointer;
    printf("what? %d\n", created_objects);
    return fib_out->value;
}

int main4(int a) {
//    return addwat(a, a);
    return *ptr_fib(&a);
}

int get_int_from_short(Short* a) {
    return a->value;
}


PyObject* make_pair(PyObject* a, PyObject* b) {
    PyObject* tuple = PyTuple_New(2);
    PyTuple_SetItem(tuple, 0, a);
    PyTuple_SetItem(tuple, 1, b);
    return tuple;
}

PyObject* pair(int a, int b) {
    // manually coding up the wrapper
    return make_pair(PyLong_FromLong(a), PyLong_FromLong(b));
}

long first(PyObject* x) {
    return PyLong_AsLong(PyTuple_GetItem(x, 0));
}

long second(PyObject* x) {
    return PyLong_AsLong(PyTuple_GetItem(x, 1));
}


void emscripten_notify_memory_growth(size_t blubb) {}

// honestly -- no idea when this happens. Maybe we just panic?
// this doesn't statically remove any references to this func because it's in the table
// which makes me _really_ confused
int __stdio_seek(int a, double b, int c, int d) {
    return 0;
}
int __stdio_close(int a) {
    return 0;
}

//int main() {
////    printf("1\n");
//    main_long(35);
//    printf("%d\n", created_objects);
//}

