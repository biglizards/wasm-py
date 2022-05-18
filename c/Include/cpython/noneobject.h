#ifndef C_NONEOBJECT_H
#define C_NONEOBJECT_H

/*
_Py_NoneStruct is an object of undefined type which can be used in contexts
where NULL (nil) is not suitable (since NULL often means 'error').

Don't forget to apply Py_INCREF() when returning this value!!!
*/
PyAPI_DATA(PyTypeObject) PyNone_Type;
PyAPI_DATA(PyObject) _Py_NoneStruct; /* Don't use this directly */
#define Py_None (&_Py_NoneStruct)

// Test if an object is the None singleton, the same as "x is None" in Python.
PyAPI_FUNC(int) Py_IsNone(PyObject *x);
#define Py_IsNone(x) Py_Is((x), Py_None)

/* Macro for returning Py_None from a function */
#define Py_RETURN_NONE return Py_NewRef(Py_None)

PyAPI_FUNC(PyObject*) return_none();

#endif //C_NONEOBJECT_H
