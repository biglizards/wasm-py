#include "object.h"
#include "cpython/boolobject.h"
#include "cpython/longintrepr.h"
#include "cpython/longobject.h"
#include "cpython/noneobject.h"

#include <stdio.h>
#include <stdlib.h>

unsigned int created_objects = 0;

//void py_set_local_decref(PyObject *value, PyObject *old)
//{
//    if (op != NULL) {
//        Py_DECREF(op);
//    }
//}

// we use a basic free-list thing here
// basically: the size is usually 2, so we have a special case for that

PyObject* free_list_head_16 = NULL;
PyObject* free_list_head_18 = NULL;

inline void* py_malloc(int size) {
    if ((size == 16 || size == 14) && free_list_head_16 != NULL) {
        PyObject* tmp = free_list_head_16;
        free_list_head_16 = (PyObject*)free_list_head_16->refCount;
        return tmp;
    }
    if (size == 18 && free_list_head_18 != NULL) {
        PyObject* tmp = free_list_head_18;
        free_list_head_18 = (PyObject*)free_list_head_18->refCount;
        return tmp;
    }
//    created_objects++;
//    printf("alloc: %d, %d, %p\n", size, created_objects, free_list_head_18);
    return malloc(size);
}

inline void py_decref(PyObject* a) {
    if (--a->refCount == 0) {
        // question: how big is this object? If it isn't a PyVarObject we can't tell
        // dumb workaround: check the type, only add ints to the free list
        if (a->type == &PyLong_Type) {
//            printf("its a long %ld \n", ((PyVarObject*)a)->ob_size );
            if (((PyVarObject*)a)->ob_size == 2 || ((PyVarObject*)a)->ob_size == 1) {
                a->refCount = (Py_ssize_t)free_list_head_16;
                free_list_head_16 = a;
//                printf("adding to free list\n");
                return;
            }
            if (((PyVarObject*)a)->ob_size == 3) {
//                printf("adding to free list\n");
                a->refCount = (Py_ssize_t)free_list_head_18;
                free_list_head_18 = a;
                return;
            }

        }
        free(a);
//        created_objects--;
//        printf("dealloc: %d\n", created_objects);
    }
}

//inline void py_decref(PyObject* a) {
//    if (--a->refCount == 0) {
//        free(a);
////        printf("%d\n", created_objects--);
//    }
//}

inline void py_incref(PyObject* a) {
    a->refCount++;
}

/* Test a value used as condition, e.g., in a while or if statement.
   Return -1 if an error occurred */

int
PyObject_IsTrue(PyObject *v)
{
    Py_ssize_t res;
    if (v == Py_True)
        return 1;
    if (v == Py_False)
        return 0;
    if (v == Py_None)
        return 0;
    else if (Py_TYPE(v)->tp_as_number != NULL &&
             Py_TYPE(v)->tp_as_number->nb_bool != NULL)
        res = (*Py_TYPE(v)->tp_as_number->nb_bool)(v);
    else if (Py_TYPE(v)->tp_as_mapping != NULL &&
             Py_TYPE(v)->tp_as_mapping->mp_length != NULL)
        res = (*Py_TYPE(v)->tp_as_mapping->mp_length)(v);
    else if (Py_TYPE(v)->tp_as_sequence != NULL &&
             Py_TYPE(v)->tp_as_sequence->sq_length != NULL)
        res = (*Py_TYPE(v)->tp_as_sequence->sq_length)(v);
    else
        return 1;
    /* if it is negative, it should be either -1 or -2 */
    return (res > 0) ? 1 : Py_SAFE_DOWNCAST(res, Py_ssize_t, int);
}

#undef Py_NewRef
#undef Py_XNewRef

// Export Py_NewRef() and Py_XNewRef() as regular functions for the stable ABI.
PyObject*
Py_NewRef(PyObject *obj)
{
    return _Py_NewRef(obj);
}

PyObject*
Py_XNewRef(PyObject *obj)
{
    return _Py_XNewRef(obj);
}
