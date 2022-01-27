//
// Created by dave on 11/12/2021.
//

#include "object.h"
#include "glue.h"
#include "cpython/noneobject.h"

/*
None is a non-NULL undefined value.
There is (and should be!) no way to create other objects of this type,
so there is exactly one (which is indestructible, by the way).
*/

///* ARGSUSED */
//static PyObject *
//none_repr(PyObject *op)
//{
//    return PyUnicode_FromString("None");
//}

///* ARGUSED */
//static void _Py_NO_RETURN
//none_dealloc(PyObject* ignore)
//{
///* This should never get called, but we also don't want to SEGV if
// * we accidentally decref None out of existence.
// */
//Py_FatalError("deallocating None");
//}

//static PyObject *
//none_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
//{
//    if (PyTuple_GET_SIZE(args) || (kwargs && PyDict_GET_SIZE(kwargs))) {
//        PyErr_SetString(PyExc_TypeError, "NoneType takes no arguments");
//        return NULL;
//    }
//    Py_RETURN_NONE;
//}

static int
none_bool(PyObject *v)
{
    return 0;
}

static PyNumberMethods none_as_number = {
        0,                          /* nb_add */
        0,                          /* nb_subtract */
        0,                          /* nb_multiply */
        0,                          /* nb_remainder */
        0,                          /* nb_divmod */
        0,                          /* nb_power */
        0,                          /* nb_negative */
        0,                          /* nb_positive */
        0,                          /* nb_absolute */
        (inquiry)none_bool,         /* nb_bool */
        0,                          /* nb_invert */
        0,                          /* nb_lshift */
        0,                          /* nb_rshift */
        0,                          /* nb_and */
        0,                          /* nb_xor */
        0,                          /* nb_or */
        0,                          /* nb_int */
        0,                          /* nb_float */
        0,                          /* nb_inplace_add */
        0,                          /* nb_inplace_subtract */
        0,                          /* nb_inplace_multiply */
        0,                          /* nb_inplace_remainder */
        0,                          /* nb_inplace_power */
        0,                          /* nb_inplace_lshift */
        0,                          /* nb_inplace_rshift */
        0,                          /* nb_inplace_and */
        0,                          /* nb_inplace_xor */
        0,                          /* nb_inplace_or */
        0,                          /* nb_floor_divide */
        0,                          /* nb_true_divide */
        0,                          /* nb_inplace_floor_divide */
        0,                          /* nb_inplace_true_divide */
        0,                          /* nb_index */
};

PyTypeObject _PyNone_Type = {
//        PyVarObject_HEAD_INIT(&PyType_Type, 0)
        TYPE_HEAD
        "NoneType",
        0,
        0,
//        none_dealloc,       /*tp_dealloc*/ /*never called*/
//        0,                  /*tp_vectorcall_offset*/
//        0,                  /*tp_getattr*/
//        0,                  /*tp_setattr*/
//        0,                  /*tp_as_async*/
//        none_repr,          /*tp_repr*/
        &none_as_number,    /*tp_as_number*/
        0,                  /*tp_as_sequence*/
        0,                  /*tp_as_mapping*/
//        0,                  /*tp_hash */
//        0,                  /*tp_call */
//        0,                  /*tp_str */
//        0,                  /*tp_getattro */
//        0,                  /*tp_setattro */
//        0,                  /*tp_as_buffer */
//        Py_TPFLAGS_DEFAULT, /*tp_flags */
//        0,                  /*tp_doc */
//        0,                  /*tp_traverse */
//        0,                  /*tp_clear */
//        0,                  /*tp_richcompare */
//        0,                  /*tp_weaklistoffset */
//        0,                  /*tp_iter */
//        0,                  /*tp_iternext */
//        0,                  /*tp_methods */
//        0,                  /*tp_members */
//        0,                  /*tp_getset */
//        0,                  /*tp_base */
//        0,                  /*tp_dict */
//        0,                  /*tp_descr_get */
//        0,                  /*tp_descr_set */
//        0,                  /*tp_dictoffset */
//        0,                  /*tp_init */
//        0,                  /*tp_alloc */
//        none_new,           /*tp_new */
};

PyObject _Py_NoneStruct = {
        1, &_PyNone_Type
};

PyObject* return_none() {
    Py_RETURN_NONE;
}
