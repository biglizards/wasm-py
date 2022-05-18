#include <stdio.h>
#include <stdlib.h>

#include "short.h"

#include "glue.h"
#include "object.h"
#include "cpython/longintrepr.h"
#include "cpython/longobject.h"
#include "cpython/tupleobject.h"
#include "cpython/noneobject.h"
#include "cpython/boolobject.h"
#include "cpython/floatobject.h"

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
    ret rv;                                                               \
    if (a->type->path != NULL) rv = a->type->path(a,b);                   \
    else if (b->type->path != NULL) rv = b->type->path(a,b);              \
    else PANIC(#name "(" #path ") Not implemented!");                     \
    Py_DECREF(b); Py_DECREF(a);                                           \
    return rv;                                                            \
}

#define BINARY_FUNC2(ret, name, lens, path) ret name(PyObject* a, PyObject* b) { \
    ret rv;                                                                      \
    if (a->type->lens != NULL && a->type->lens->path != NULL) rv = a->type->lens->path(a,b);                   \
    else if (b->type->lens != NULL && b->type->lens->path != NULL) rv = b->type->lens->path(a,b);               \
    else PANIC(#name "(" #path ") Not implemented!");                     \
    Py_DECREF(b); Py_DECREF(a);                                           \
    return rv;                                                            \
}

#define TRINARY_FUNC2(ret, name, lens, path) ret name(PyObject* a, PyObject* b, PyObject* c) { \
    ret rv;                                                                      \
    if (a->type->lens != NULL && a->type->lens->path != NULL) rv = a->type->lens->path(a,b,c);                   \
    else if (b->type->lens != NULL && b->type->lens->path != NULL) rv = b->type->lens->path(a,b,c);              \
    else if (c->type->lens != NULL && c->type->lens->path != NULL) rv = c->type->lens->path(a,b,c);\
    else PANIC(#name "(" #path ") Not implemented!");                     \
    Py_DECREF(c); Py_DECREF(b); Py_DECREF(a);                                           \
    return rv;                                                            \
}

#define UNARY_FUNC2(ret, name, lens, path) ret name(PyObject* a) { \
    if (a->type->lens != NULL && a->type->lens->path != NULL) return a->type->lens->path(a); \
    PANIC(#name "(" #lens "->" #path ") Not implemented!");                                   \
}

#define BIN_OP(name, path) BINARY_FUNC(PyObject*, name, path)
#define BIN_OP_NB(name, path) BINARY_FUNC2(PyObject*, name, tp_as_number, path)
#define BIN_OP_MP(name, path) BINARY_FUNC2(PyObject*, name, tp_as_mapping, path)
#define BIN_TEST(name, path) BINARY_FUNC(int, name, path)
#define UNARY_TEST_NB(name, path) UNARY_FUNC2(int, name, tp_as_number, path)
#define TRI_OP_NB(name, path) TRINARY_FUNC2(PyObject*, name, tp_as_number, path)
#define UNARY_OP_NB(name, path) UNARY_FUNC2(PyObject*, name, tp_as_number, path)

BIN_OP_NB(add_pyobject, nb_add)
BIN_OP_NB(subtract_pyobject, nb_subtract)
BIN_OP_NB(mul_pyobject, nb_multiply)
BIN_OP_NB(rem_pyobject, nb_remainder)
TRI_OP_NB(tri_pow_pyobject, nb_power)
UNARY_OP_NB(neg_pyobject, nb_negative)
UNARY_OP_NB(pos_pyobject, nb_positive)
UNARY_OP_NB(abs_pyobject, nb_absolute)
UNARY_TEST_NB(bool_pyobject, nb_bool)
UNARY_OP_NB(inv_pyobject, nb_invert)
BIN_OP_NB(lshift_pyobject, nb_lshift)
BIN_OP_NB(rshift_pyobject, nb_rshift)
BIN_OP_NB(and_pyobject, nb_and)
BIN_OP_NB(xor_pyobject, nb_xor)
BIN_OP_NB(or_pyobject, nb_or)
UNARY_OP_NB(int_pyobject, nb_int)
UNARY_OP_NB(float_pyobject, nb_float)

BIN_OP_NB(floor_div_pyobject, nb_floor_divide)
BIN_OP_NB(div_pyobject, nb_true_divide)

BIN_OP_MP(subscr_pyobject, mp_subscript)
BIN_TEST(leq_pyobject, cmp_lte)
BIN_TEST(eq_pyobject, cmp_eq)

PyObject* bin_pow_pyobject(PyObject* a, PyObject* b) {
    // todo: directly implement this for each type, see if that's faster
    PyObject* rv;
    if (a->type->tp_as_number != NULL && a->type->tp_as_number->nb_power != NULL) rv = a->type->tp_as_number->nb_power(a,b,Py_None);
    else if (b->type->tp_as_number != NULL && b->type->tp_as_number->nb_power != NULL) rv = b->type->tp_as_number->nb_power(a,b,Py_None);
    else PANIC("bin_pow_pyobject Not implemented!");
    Py_DECREF(b); Py_DECREF(a);
    return rv;
}

PyObject* not_pyobject(PyObject* a) {
    int is_true = PyObject_IsTrue(a);
    Py_DECREF(a);
    if (is_true) {
        Py_RETURN_FALSE;
    } else {
        Py_RETURN_TRUE;
    }
}

int is_pyobject(PyObject* a, PyObject* b) {
    int eq = a == b;
    Py_DECREF(a);
    Py_DECREF(b);
    return eq;
}

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

int get_type(PyObject* in) {
    if (in->type == &PyLong_Type) return 1;
    if (in->type == &PyTuple_Type) return 2;
    if (in->type == &PyBool_Type) return 3;
    if (in->type == &PyNone_Type) return 4;
    if (in->type == &PyFloat_Type) return 5;
//    if (in->type == PyLong_Type) return 5;
    return -1;
}

void raise_name_error() {
    printf("NameError: attempt to access uninitialised variable\n");
    exit(-1);
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

double add_float(double a, double b) {
    PyObject* obj = PyFloat_FromDouble(a);
    PyObject* obj2 = PyFloat_FromDouble(b);

    PyObject* result = add_pyobject(obj, obj2);

    return PyFloat_AsDouble(result);

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

