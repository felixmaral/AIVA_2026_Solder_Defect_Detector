#include <Python.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "solder_defect.h"

/* Track whether THIS library initialized Python.
 * If the .so is loaded from an existing Python process (e.g. via ctypes in
 * unit tests), Python is already running and we must NOT call Py_Finalize(). */
static int python_initialized_by_us = 0;

struct ApplicationHandle {
    PyObject* pInstance;
};

static void print_python_error() {
    if (PyErr_Occurred()) {
        PyErr_Print();
    }
}

static int parse_detection_result(PyObject* pDict, DetectionResultInfo* result) {
    result->success = 0;
    if (!pDict || !PyDict_Check(pDict)) {
        fprintf(stderr, "Error: process result is not a Python dictionary.\n");
        return 0;
    }

    PyObject* pXmlPath = PyDict_GetItemString(pDict, "xml_path");
    PyObject* pProcTimeMs = PyDict_GetItemString(pDict, "processing_time_ms");
    PyObject* pDetCount = PyDict_GetItemString(pDict, "detection_count");

    if (pXmlPath && PyUnicode_Check(pXmlPath)) {
        const char* path = PyUnicode_AsUTF8(pXmlPath);
        strncpy(result->xml_path, path, sizeof(result->xml_path) - 1);
        result->xml_path[sizeof(result->xml_path) - 1] = '\0';
    } else {
        strcpy(result->xml_path, "");
    }

    if (pProcTimeMs) {
        if (PyFloat_Check(pProcTimeMs)) {
            result->processing_time_ms = PyFloat_AsDouble(pProcTimeMs);
        } else if (PyLong_Check(pProcTimeMs)) {
            result->processing_time_ms = (double)PyLong_AsLong(pProcTimeMs);
        }
    } else {
        result->processing_time_ms = 0.0;
    }

    if (pDetCount && PyLong_Check(pDetCount)) {
        result->detection_count = (int)PyLong_AsLong(pDetCount);
    } else {
        result->detection_count = 0;
    }

    result->success = 1;
    return 1;
}

ApplicationHandle* application_create(int camera_index, const char* output_dir, int visualize) {
    if (!Py_IsInitialized()) {
        Py_Initialize();
        python_initialized_by_us = 1;
    }

    // Add current working directory to sys.path
    PyObject* sysPath = PySys_GetObject("path");
    PyObject* currentDir = PyUnicode_FromString(".");
    PyList_Append(sysPath, currentDir);
    Py_DECREF(currentDir);
    
    // Also try to add the parent directory if we are running from src/c_bindings
    PyObject* parentDir = PyUnicode_FromString("../..");
    PyList_Append(sysPath, parentDir);
    Py_DECREF(parentDir);

    PyObject* pName = PyUnicode_FromString("src.application");
    PyObject* pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule == NULL) {
        fprintf(stderr, "Error: Could not import python module 'src.application'. Make sure you are running from the project root.\n");
        print_python_error();
        return NULL;
    }

    PyObject* pClass = PyObject_GetAttrString(pModule, "Application");
    if (pClass == NULL || !PyCallable_Check(pClass)) {
        fprintf(stderr, "Error: Cannot find 'Application' class in module.\n");
        print_python_error();
        Py_DECREF(pModule);
        return NULL;
    }

    PyObject* pKwargs = PyDict_New();
    PyDict_SetItemString(pKwargs, "camera_index", PyLong_FromLong(camera_index));
    
    if (output_dir != NULL) {
        PyDict_SetItemString(pKwargs, "output_dir", PyUnicode_FromString(output_dir));
    }
    
    PyDict_SetItemString(pKwargs, "visualize", visualize ? Py_True : Py_False);

    PyObject* pArgs = PyTuple_New(0);
    PyObject* pInstance = PyObject_Call(pClass, pArgs, pKwargs);

    Py_DECREF(pArgs);
    Py_DECREF(pKwargs);
    Py_DECREF(pClass);
    Py_DECREF(pModule);

    if (pInstance == NULL) {
        fprintf(stderr, "Error: Failed to instantiate Application class.\n");
        print_python_error();
        return NULL;
    }

    ApplicationHandle* handle = (ApplicationHandle*)malloc(sizeof(ApplicationHandle));
    handle->pInstance = pInstance;

    return handle;
}

DetectionResultInfo application_process_from_path(ApplicationHandle* app, const char* image_path) {
    DetectionResultInfo result;
    memset(&result, 0, sizeof(result));
    
    if (!app || !app->pInstance) {
        fprintf(stderr, "Error: Invalid ApplicationHandle.\n");
        return result;
    }

    PyObject* pMethodName = PyUnicode_FromString("process_from_path");
    PyObject* pResult = PyObject_CallMethodObjArgs(app->pInstance, pMethodName, PyUnicode_FromString(image_path), NULL);
    Py_DECREF(pMethodName);

    if (pResult == NULL) {
        fprintf(stderr, "Error: Call to process_from_path failed.\n");
        print_python_error();
        return result;
    }

    parse_detection_result(pResult, &result);
    Py_DECREF(pResult);

    return result;
}

DetectionResultInfo application_process_live_camera(ApplicationHandle* app) {
    DetectionResultInfo result;
    memset(&result, 0, sizeof(result));
    
    if (!app || !app->pInstance) {
        fprintf(stderr, "Error: Invalid ApplicationHandle.\n");
        return result;
    }

    PyObject* pMethodName = PyUnicode_FromString("process_live_camera");
    PyObject* pResult = PyObject_CallMethodObjArgs(app->pInstance, pMethodName, NULL);
    Py_DECREF(pMethodName);

    if (pResult == NULL) {
        fprintf(stderr, "Error: Call to process_live_camera failed.\n");
        print_python_error();
        return result;
    }

    parse_detection_result(pResult, &result);
    Py_DECREF(pResult);

    return result;
}

void application_destroy(ApplicationHandle* app) {
    if (app) {
        if (app->pInstance) {
            Py_DECREF(app->pInstance);
        }
        free(app);

        if (python_initialized_by_us && Py_IsInitialized()) {
            Py_Finalize();
            python_initialized_by_us = 0;
        }
    }
}
