/**
 * @file solder_defect.c
 * @brief CPython-embedding implementation of the solder defect detection C API.
 *
 * This translation unit bridges the gap between native C robot control code and
 * the Python ``Application`` class. It embeds the CPython interpreter inside the
 * shared library and forwards every public API call to the corresponding Python
 * method, converting return values from Python dictionaries into plain C structs.
 *
 * ## GIL Management
 * When this library is loaded by a Python process (e.g., via ``ctypes`` in unit
 * tests), ``ctypes`` releases the GIL before calling any foreign function. Every
 * function in this file therefore acquires the GIL explicitly via
 * ``PyGILState_Ensure`` at its entry point and releases it via
 * ``PyGILState_Release`` before returning. This makes the API safe to call from
 * both pure C programs and live Python processes.
 *
 * ## Python Interpreter Ownership
 * The static flag ``python_initialized_by_us`` tracks whether this library
 * started the interpreter. ``Py_Finalize`` is called in ``application_destroy``
 * only when this library owns the interpreter, preventing accidental teardown of
 * an already-running Python process (e.g., when loaded via ``ctypes``).
 */

#include <Python.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "solder_defect.h"

/* Track whether THIS library initialized Python.
 * If the .so is loaded from an existing Python process (e.g. via ctypes in
 * unit tests), Python is already running and we must NOT call Py_Finalize(). */
static int python_initialized_by_us = 0;

/** @brief Internal struct holding the CPython object for the Application instance. */
struct ApplicationHandle {
    PyObject* pInstance; /**< Borrowed reference to the Python Application object. */
};

/* ── Private helpers ────────────────────────────────────────────────────── */

/**
 * @brief Prints the current Python exception to stderr and clears it.
 *
 * Must only be called while the GIL is held.
 */
static void print_python_error(void) {
    if (PyErr_Occurred()) {
        PyErr_Print();
    }
}

/**
 * @brief Extracts fields from a Python result dict into a ``DetectionResultInfo``.
 *
 * Reads ``xml_path``, ``processing_time_ms``, and ``detection_count`` from the
 * given Python dictionary and copies them into @p result. Sets ``result->success``
 * to ``1`` on success, ``0`` on failure.
 *
 * @param pDict  Python dictionary returned by an ``Application`` process method.
 * @param result Output struct to populate.
 * @return       ``1`` on success, ``0`` if @p pDict is NULL or not a dict.
 */
static int parse_detection_result(PyObject* pDict, DetectionResultInfo* result) {
    result->success = 0;
    if (!pDict || !PyDict_Check(pDict)) {
        fprintf(stderr, "Error: process result is not a Python dictionary.\n");
        return 0;
    }

    PyObject* pXmlPath    = PyDict_GetItemString(pDict, "xml_path");
    PyObject* pProcTimeMs = PyDict_GetItemString(pDict, "processing_time_ms");
    PyObject* pDetCount   = PyDict_GetItemString(pDict, "detection_count");

    if (pXmlPath && PyUnicode_Check(pXmlPath)) {
        const char* path = PyUnicode_AsUTF8(pXmlPath);
        strncpy(result->xml_path, path, sizeof(result->xml_path) - 1);
        result->xml_path[sizeof(result->xml_path) - 1] = '\0';
    } else {
        strcpy(result->xml_path, "");
    }

    if (pProcTimeMs) {
        if (PyFloat_Check(pProcTimeMs))
            result->processing_time_ms = PyFloat_AsDouble(pProcTimeMs);
        else if (PyLong_Check(pProcTimeMs))
            result->processing_time_ms = (double)PyLong_AsLong(pProcTimeMs);
    } else {
        result->processing_time_ms = 0.0;
    }

    if (pDetCount && PyLong_Check(pDetCount))
        result->detection_count = (int)PyLong_AsLong(pDetCount);
    else
        result->detection_count = 0;

    result->success = 1;
    return 1;
}

/* ── Public API implementation ──────────────────────────────────────────── */

ApplicationHandle* application_create(int camera_index, const char* output_dir, int visualize) {
    /* Start the interpreter only if it is not already running (e.g., when
     * invoked from a pure C program). Record ownership for Py_Finalize later. */
    if (!Py_IsInitialized()) {
        Py_Initialize();
        python_initialized_by_us = 1;
    }

    /* Acquire the GIL before touching any Python C API objects. When called
     * from a Python process via ctypes, the GIL has been released by ctypes
     * before entering this function. */
    PyGILState_STATE gstate = PyGILState_Ensure();

    /* Extend sys.path with the current working directory so that the
     * 'src.application' package is importable from the project root. */
    PyObject* sysPath = PySys_GetObject("path");
    PyObject* cwdDir  = PyUnicode_FromString(".");
    PyList_Append(sysPath, cwdDir);
    Py_DECREF(cwdDir);

    /* Import the application module */
    PyObject* pName   = PyUnicode_FromString("src.application");
    PyObject* pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule == NULL) {
        fprintf(stderr, "Error: Could not import 'src.application'. "
                        "Make sure you run from the project root.\n");
        print_python_error();
        PyGILState_Release(gstate);
        return NULL;
    }

    /* Retrieve the Application class object from the imported module */
    PyObject* pClass = PyObject_GetAttrString(pModule, "Application");
    if (pClass == NULL || !PyCallable_Check(pClass)) {
        fprintf(stderr, "Error: Cannot find 'Application' class in module.\n");
        print_python_error();
        Py_XDECREF(pClass);
        Py_DECREF(pModule);
        PyGILState_Release(gstate);
        return NULL;
    }

    /* Build keyword argument dict: Application(camera_index=, output_dir=, visualize=) */
    PyObject* pKwargs = PyDict_New();
    PyDict_SetItemString(pKwargs, "camera_index", PyLong_FromLong(camera_index));
    if (output_dir != NULL)
        PyDict_SetItemString(pKwargs, "output_dir", PyUnicode_FromString(output_dir));
    PyDict_SetItemString(pKwargs, "visualize", visualize ? Py_True : Py_False);

    PyObject* pArgs     = PyTuple_New(0);   /* Application takes no positional args */
    PyObject* pInstance = PyObject_Call(pClass, pArgs, pKwargs);

    Py_DECREF(pArgs);
    Py_DECREF(pKwargs);
    Py_DECREF(pClass);
    Py_DECREF(pModule);

    if (pInstance == NULL) {
        fprintf(stderr, "Error: Failed to instantiate Application class.\n");
        print_python_error();
        PyGILState_Release(gstate);
        return NULL;
    }

    ApplicationHandle* handle = (ApplicationHandle*)malloc(sizeof(ApplicationHandle));
    handle->pInstance = pInstance;

    PyGILState_Release(gstate);
    return handle;
}

DetectionResultInfo application_process_from_path(ApplicationHandle* app, const char* image_path) {
    DetectionResultInfo result;
    memset(&result, 0, sizeof(result));

    if (!app || !app->pInstance) {
        fprintf(stderr, "Error: Invalid ApplicationHandle.\n");
        return result;
    }

    PyGILState_STATE gstate = PyGILState_Ensure();

    /* Call Application.process_from_path(image_path) */
    PyObject* pResult = PyObject_CallMethod(
        app->pInstance, "process_from_path", "s", image_path);

    if (pResult == NULL) {
        fprintf(stderr, "Error: Call to process_from_path failed.\n");
        print_python_error();
        PyGILState_Release(gstate);
        return result;
    }

    parse_detection_result(pResult, &result);
    Py_DECREF(pResult);

    PyGILState_Release(gstate);
    return result;
}

DetectionResultInfo application_process_live_camera(ApplicationHandle* app) {
    DetectionResultInfo result;
    memset(&result, 0, sizeof(result));

    if (!app || !app->pInstance) {
        fprintf(stderr, "Error: Invalid ApplicationHandle.\n");
        return result;
    }

    PyGILState_STATE gstate = PyGILState_Ensure();

    /* Call Application.process_live_camera() — no arguments */
    PyObject* pResult = PyObject_CallMethod(
        app->pInstance, "process_live_camera", NULL);

    if (pResult == NULL) {
        fprintf(stderr, "Error: Call to process_live_camera failed.\n");
        print_python_error();
        PyGILState_Release(gstate);
        return result;
    }

    parse_detection_result(pResult, &result);
    Py_DECREF(pResult);

    PyGILState_Release(gstate);
    return result;
}

void application_destroy(ApplicationHandle* app) {
    if (!app)
        return; /* Passing NULL is documented as a safe no-op */

    PyGILState_STATE gstate = PyGILState_Ensure();

    if (app->pInstance)
        Py_DECREF(app->pInstance); /* Release the Python Application object */

    PyGILState_Release(gstate);
    free(app);

    /* Shut down the interpreter only if this library started it. Calling
     * Py_Finalize from inside a running Python process would be catastrophic. */
    if (python_initialized_by_us && Py_IsInitialized()) {
        Py_Finalize();
        python_initialized_by_us = 0;
    }
}
