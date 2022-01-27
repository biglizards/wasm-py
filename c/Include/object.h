//
// Created by dave on 19/11/2021.
//

#ifndef WASM_PY_OBJECT_H
#define WASM_PY_OBJECT_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "glue.h"


struct __object;
typedef struct __object PyObject;
//typedef struct _typeobject PyTypeObject;
typedef struct __type Type;

typedef PyObject * (*unaryfunc)(PyObject *);
typedef PyObject * (*binaryfunc)(PyObject *, PyObject *);
typedef PyObject * (*ternaryfunc)(PyObject *, PyObject *, PyObject *);
typedef int (*inquiry)(PyObject *);
typedef Py_ssize_t (*lenfunc)(PyObject *);
typedef PyObject *(*ssizeargfunc)(PyObject *, Py_ssize_t);
typedef PyObject *(*ssizessizeargfunc)(PyObject *, Py_ssize_t, Py_ssize_t);
typedef int(*ssizeobjargproc)(PyObject *, Py_ssize_t, PyObject *);
typedef int(*ssizessizeobjargproc)(PyObject *, Py_ssize_t, Py_ssize_t, PyObject *);
typedef int(*objobjargproc)(PyObject *, PyObject *, PyObject *);

typedef int (*objobjproc)(PyObject *, PyObject *);
typedef int (*visitproc)(PyObject *, void *);
typedef int (*traverseproc)(PyObject *, visitproc, void *);


typedef void (*freefunc)(void *);
typedef void (*destructor)(PyObject *);
typedef PyObject *(*getattrfunc)(PyObject *, char *);
typedef PyObject *(*getattrofunc)(PyObject *, PyObject *);
typedef int (*setattrfunc)(PyObject *, char *, PyObject *);
typedef int (*setattrofunc)(PyObject *, PyObject *, PyObject *);
typedef PyObject *(*reprfunc)(PyObject *);
//typedef Py_hash_t (*hashfunc)(PyObject *);
typedef PyObject *(*richcmpfunc) (PyObject *, PyObject *, int);
typedef PyObject *(*getiterfunc) (PyObject *);
typedef PyObject *(*iternextfunc) (PyObject *);
typedef PyObject *(*descrgetfunc) (PyObject *, PyObject *, PyObject *);
typedef int (*descrsetfunc) (PyObject *, PyObject *, PyObject *);
typedef int (*initproc)(PyObject *, PyObject *, PyObject *);
typedef PyObject *(*newfunc)(PyTypeObject *, PyObject *, PyObject *);
typedef PyObject *(*allocfunc)(PyTypeObject *, Py_ssize_t);

// BinTest just returns a straight-up bool (not a pyobject)
// is this sound? Probably not -- worth looking into
typedef int (* BinTest)(PyObject*, PyObject*);

/* PyObject_HEAD defines the initial segment of every PyObject. */
#define PyObject_HEAD                   PyObject ob_base;

#define PyObject_HEAD_INIT(type) { 1, type },

#define PyVarObject_HEAD_INIT(type, size)       \
    { PyObject_HEAD_INIT(type) size },

/* PyObject_VAR_HEAD defines the initial segment of all variable-size
 * container objects.  These end with a declaration of an array with 1
 * element, but enough space is malloc'ed so that the array actually
 * has room for ob_size elements.  Note that ob_size is an element count,
 * not necessarily a byte count.
 */
#define PyObject_VAR_HEAD      PyVarObject ob_base;
#define Py_INVALID_SIZE (Py_ssize_t)-1


//struct _typeobject {
//    PyObject_VAR_HEAD
//    const char *tp_name; /* For printing, in format "<module>.<name>" */
//    Py_ssize_t tp_basicsize, tp_itemsize; /* For allocation */
//
//    /* Methods to implement standard operations */
//
//    destructor tp_dealloc;
//    Py_ssize_t tp_vectorcall_offset;
//    getattrfunc tp_getattr;
//    setattrfunc tp_setattr;
//    PyAsyncMethods *tp_as_async; /* formerly known as tp_compare (Python 2)
//                                    or tp_reserved (Python 3) */
//    reprfunc tp_repr;
//
//    /* Method suites for standard classes */
//
//    PyNumberMethods *tp_as_number;
//    PySequenceMethods *tp_as_sequence;
//    PyMappingMethods *tp_as_mapping;
//
//    /* More standard operations (here for binary compatibility) */
//
//    hashfunc tp_hash;
//    ternaryfunc tp_call;
//    reprfunc tp_str;
//    getattrofunc tp_getattro;
//    setattrofunc tp_setattro;
//
//    /* Functions to access object as input/output buffer */
//    PyBufferProcs *tp_as_buffer;
//
//    /* Flags to define presence of optional/expanded features */
//    unsigned long tp_flags;
//
//    const char *tp_doc; /* Documentation string */
//
//    /* Assigned meaning in release 2.0 */
//    /* call function for all accessible objects */
//    traverseproc tp_traverse;
//
//    /* delete references to contained objects */
//    inquiry tp_clear;
//
//    /* Assigned meaning in release 2.1 */
//    /* rich comparisons */
//    richcmpfunc tp_richcompare;
//
//    /* weak reference enabler */
//    Py_ssize_t tp_weaklistoffset;
//
//    /* Iterators */
//    getiterfunc tp_iter;
//    iternextfunc tp_iternext;
//
//    /* Attribute descriptor and subclassing stuff */
//    struct PyMethodDef *tp_methods;
//    struct PyMemberDef *tp_members;
//    struct PyGetSetDef *tp_getset;
//    // Strong reference on a heap type, borrowed reference on a static type
//    struct _typeobject *tp_base;
//    PyObject *tp_dict;
//    descrgetfunc tp_descr_get;
//    descrsetfunc tp_descr_set;
//    Py_ssize_t tp_dictoffset;
//    initproc tp_init;
//    allocfunc tp_alloc;
//    newfunc tp_new;
//    freefunc tp_free; /* Low-level free-memory routine */
//    inquiry tp_is_gc; /* For PyObject_IS_GC */
//    PyObject *tp_bases;
//    PyObject *tp_mro; /* method resolution order */
//    PyObject *tp_cache;
//    PyObject *tp_subclasses;
//    PyObject *tp_weaklist;
//    destructor tp_del;
//
//    /* Type attribute cache version tag. Added in version 2.6 */
//    unsigned int tp_version_tag;
//
//    destructor tp_finalize;
//    vectorcallfunc tp_vectorcall;
//};


struct __object {
    Py_ssize_t refCount;
    Type* type;
};

typedef struct {
    PyObject ob_base;
    intptr_t ob_size; /* Number of items in variable part */
} PyVarObject;

typedef struct {
    /* Number implementations must check *both*
       arguments for proper type and implement the necessary conversions
       in the slot functions themselves. */

    binaryfunc nb_add;
    binaryfunc nb_subtract;
    binaryfunc nb_multiply;
    binaryfunc nb_remainder;
    binaryfunc nb_divmod;
    ternaryfunc nb_power;
    unaryfunc nb_negative;
    unaryfunc nb_positive;
    unaryfunc nb_absolute;
    inquiry nb_bool;
    unaryfunc nb_invert;
    binaryfunc nb_lshift;
    binaryfunc nb_rshift;
    binaryfunc nb_and;
    binaryfunc nb_xor;
    binaryfunc nb_or;
    unaryfunc nb_int;
//    void *nb_reserved;  /* the slot formerly known as nb_long */
    unaryfunc nb_float;

    binaryfunc nb_inplace_add;
    binaryfunc nb_inplace_subtract;
    binaryfunc nb_inplace_multiply;
    binaryfunc nb_inplace_remainder;
    ternaryfunc nb_inplace_power;
    binaryfunc nb_inplace_lshift;
    binaryfunc nb_inplace_rshift;
    binaryfunc nb_inplace_and;
    binaryfunc nb_inplace_xor;
    binaryfunc nb_inplace_or;

    binaryfunc nb_floor_divide;
    binaryfunc nb_true_divide;
    binaryfunc nb_inplace_floor_divide;
    binaryfunc nb_inplace_true_divide;

    unaryfunc nb_index;
//
//    binaryfunc nb_matrix_multiply;
//    binaryfunc nb_inplace_matrix_multiply;
} PyNumberMethods;

typedef struct {
    lenfunc sq_length;
    binaryfunc sq_concat;
//    ssizeargfunc sq_repeat;
//    ssizeargfunc sq_item;
//    void *was_sq_slice;
//    ssizeobjargproc sq_ass_item;
//    void *was_sq_ass_slice;
//    objobjproc sq_contains;
//
//    binaryfunc sq_inplace_concat;
//    ssizeargfunc sq_inplace_repeat;
} PySequenceMethods;

typedef struct {
    lenfunc mp_length;
    binaryfunc mp_subscript;
    objobjargproc mp_ass_subscript;
} PyMappingMethods;

#define NO_NUMBER_METHODS 0
#define NO_SEQUENCE_METHODS (PySequenceMethods*)0
#define NO_MAPPING_METHODS 0

// just in case we want to make them pointers in the future
#define NUMBER_METHODS(methods) methods
#define SEQUENCE_METHODS(methods) methods
#define MAPPING_METHODS(methods) methods

typedef struct __type {
    PyObject_VAR_HEAD;

    const char *tp_name; /* For printing, in format "<module>.<name>" */
    Py_ssize_t tp_basicsize, tp_itemsize; /* For allocation */

    // todo maybe these should not be pointers?
    // although this _does_ make static typing look more impressive
    PyNumberMethods *tp_as_number;
    PySequenceMethods *tp_as_sequence;
    PyMappingMethods *tp_as_mapping;

    // we deviate from CPython a little by having different fields for each comparison
    BinTest cmp_eq;
    BinTest cmp_leq;
} Type;

// probably should be in a .c file
extern unsigned int created_objects;

void py_decref(PyObject* a);
void py_incref(PyObject* a);


// and now, a load of macros for compatability purposes

#define _PyObject_CAST(op) ((PyObject*)(op))
#define _PyObject_CAST_CONST(op) ((const PyObject*)(op))

#define _PyVarObject_CAST(op) ((PyVarObject*)(op))
#define _PyVarObject_CAST_CONST(op) ((const PyVarObject*)(op))

#define Py_TYPE(ob)             (_PyObject_CAST(ob)->type)
#define Py_SIZE(ob)             (_PyVarObject_CAST(ob)->ob_size)

static inline void _Py_SET_REFCNT(PyObject *ob, Py_ssize_t refcnt) {
    ob->refCount = refcnt;
}
#define Py_SET_REFCNT(ob, refcnt) _Py_SET_REFCNT(_PyObject_CAST(ob), refcnt)


static inline void _Py_SET_TYPE(PyObject *ob, Type *type) {
    ob->type = type;
}
#define Py_SET_TYPE(ob, type) _Py_SET_TYPE(_PyObject_CAST(ob), type)


static inline void _Py_SET_SIZE(PyVarObject *ob, Py_ssize_t size) {
    ob->ob_size = size;
}
#define Py_SET_SIZE(ob, size) _Py_SET_SIZE(_PyVarObject_CAST(ob), size)


/* REFCOUNTING STUFF */

#define Py_INCREF(op) py_incref(_PyObject_CAST(op))
#define Py_DECREF(op) py_decref(_PyObject_CAST(op))

/* Function to use in case the object pointer can be NULL: */
static inline void _Py_XINCREF(PyObject *op)
{
    if (op != NULL) {
        Py_INCREF(op);
    }
}

#define Py_XINCREF(op) _Py_XINCREF(_PyObject_CAST(op))

static inline void _Py_XDECREF(PyObject *op)
{
    if (op != NULL) {
        Py_DECREF(op);
    }
}

#define Py_XDECREF(op) _Py_XDECREF(_PyObject_CAST(op))

/* Safely decref `op` and set `op` to `op2`.
 *
 * As in case of Py_CLEAR "the obvious" code can be deadly:
 *
 *     Py_DECREF(op);
 *     op = op2;
 *
 * The safe way is:
 *
 *      Py_SETREF(op, op2);
 *
 * That arranges to set `op` to `op2` _before_ decref'ing, so that any code
 * triggered as a side-effect of `op` getting torn down no longer believes
 * `op` points to a valid object.
 *
 * Py_XSETREF is a variant of Py_SETREF that uses Py_XDECREF instead of
 * Py_DECREF.
 */
// Since we don't have the GIL (or even threads) I _think_ it's acceptable to use the "obvious" method
// is there much performance gain from doing that? Much like glass coffins: remains to be seen.

#define Py_SETREF(op, op2)                      \
    do {                                        \
        PyObject *_py_tmp = _PyObject_CAST(op); \
        (op) = (op2);                           \
        Py_DECREF(_py_tmp);                     \
    } while (0)

#define Py_XSETREF(op, op2)                     \
    do {                                        \
        PyObject *_py_tmp = _PyObject_CAST(op); \
        (op) = (op2);                           \
        Py_XDECREF(_py_tmp);                    \
    } while (0)



static inline void
_PyObject_Init(PyObject* op, Type* typeobj)
{
//    assert(op != NULL);
    Py_SET_TYPE(op, typeobj);
//    if (_PyType_HasFeature(typeobj, Py_TPFLAGS_HEAPTYPE)) {
//        Py_INCREF(typeobj);
//    }
    Py_SET_REFCNT(op, 1);  // ie _Py_NewReference(op);
}

static inline void
_PyObject_InitVar(PyVarObject* op, Type* typeobj, Py_ssize_t size)
{
//    assert(op != NULL);
    Py_SET_SIZE(op, size);
    _PyObject_Init((PyObject *)op, typeobj);
}

static inline int _Py_IS_TYPE(const PyObject *ob, const PyTypeObject *type) {
    // bpo-44378: Don't use Py_TYPE() since Py_TYPE() requires a non-const
    // object.
    return ob->type == type;
}
#define Py_IS_TYPE(ob, type) _Py_IS_TYPE(_PyObject_CAST_CONST(ob), type)

static inline Py_ssize_t _Py_REFCNT(const PyObject *ob) {
    return ob->refCount;
}
#define Py_REFCNT(ob) _Py_REFCNT(_PyObject_CAST_CONST(ob))

// Fast inlined version of PyIndex_Check()
static inline int
_PyIndex_Check(PyObject *obj)
{
    PyNumberMethods *tp_as_number = Py_TYPE(obj)->tp_as_number;
    return (tp_as_number != NULL && tp_as_number->nb_index != NULL);
}

// Create a new strong reference to an object:
// increment the reference count of the object and return the object.
PyAPI_FUNC(PyObject*) Py_NewRef(PyObject *obj);

// Similar to Py_NewRef(), but the object can be NULL.
PyAPI_FUNC(PyObject*) Py_XNewRef(PyObject *obj);

static inline PyObject* _Py_NewRef(PyObject *obj)
{
    Py_INCREF(obj);
    return obj;
}

static inline PyObject* _Py_XNewRef(PyObject *obj)
{
    Py_XINCREF(obj);
    return obj;
}

// Py_NewRef() and Py_XNewRef() are exported as functions for the stable ABI.
// Names overriden with macros by static inline functions for best
// performances.
#define Py_NewRef(obj) _Py_NewRef(_PyObject_CAST(obj))
#define Py_XNewRef(obj) _Py_XNewRef(_PyObject_CAST(obj))


PyAPI_FUNC(int) PyObject_IsTrue(PyObject *);


#endif //WASM_PY_OBJECT_H
