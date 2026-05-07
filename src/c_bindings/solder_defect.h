/**
 * @file solder_defect.h
 * @brief Public C API for the PCB Solder Defect Detection System.
 *
 * This header exposes a minimal, opaque C interface that allows any native
 * client (C or C++) to drive the Python-based ``Application`` class without
 * any knowledge of Python internals. The implementation embeds the CPython
 * interpreter inside the shared library, so clients link against a single
 * ``libsolder_defect.so`` / ``.dylib`` and include this header.
 *
 * ## Typical Usage
 *
 * @code{.c}
 * #include "solder_defect.h"
 *
 * int main(void) {
 *     // Initialise the vision system once (camera + model load)
 *     ApplicationHandle* app = application_create(0, NULL, 0);
 *     if (!app) { return 1; }
 *
 *     // Inspect plates in the robot control loop
 *     DetectionResultInfo result = application_process_from_path(app, "pcb.jpg");
 *     if (result.success && result.detection_count > 0) {
 *         printf("Defective plate — sending to re-solder.\n");
 *     }
 *
 *     // Release resources when the machine shuts down
 *     application_destroy(app);
 *     return 0;
 * }
 * @endcode
 *
 * ## Threading
 * All functions acquire and release the Python GIL internally. Calling them
 * from multiple threads concurrently is safe as long as each thread uses its
 * own ``ApplicationHandle``.
 *
 * ## Build
 * Compile the shared library from ``src/c_bindings/``:
 * @code{.sh}
 * make
 * @endcode
 */

#ifndef SOLDER_DEFECT_H
#define SOLDER_DEFECT_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Opaque handle representing a live ``Application`` Python instance.
 *
 * Clients must treat this type as a black box. The internal layout is an
 * implementation detail and is not part of the public API.
 */
typedef struct ApplicationHandle ApplicationHandle;

/**
 * @brief Plain-data result structure returned by every inspect call.
 *
 * All fields are value types (no heap allocation required), so the struct can
 * be used directly on the stack without any cleanup step.
 */
typedef struct {
    /** Null-terminated absolute path to the saved XML report on disk. */
    char xml_path[512];

    /** Wall-clock inference duration in milliseconds. */
    double processing_time_ms;

    /** Number of solder defects detected in the inspected image. */
    int detection_count;

    /**
     * Inspection status flag.
     * - ``1`` — inspection completed successfully; other fields are valid.
     * - ``0`` — inspection failed; other fields contain undefined data.
     */
    int success;
} DetectionResultInfo;

/**
 * @brief Initialises the Python interpreter and creates an ``Application`` instance.
 *
 * This function must be called once before any other API function. It starts
 * the embedded CPython interpreter (if not already running), adds the project
 * root to ``sys.path``, imports ``src.application``, and instantiates the
 * ``Application`` class, which loads the camera interface and YOLO weights.
 *
 * @param camera_index OpenCV device index for the physical camera. Pass ``0``
 *                     for the primary Raspberry Pi camera.
 * @param output_dir   Null-terminated path to the XML output directory. Pass
 *                     ``NULL`` to use the default ``reports/xml/`` directory.
 * @param visualize    Set to ``1`` to enable the live OpenCV detection window;
 *                     ``0`` for headless (production) operation.
 *
 * @return A valid ``ApplicationHandle`` pointer on success, or ``NULL`` if
 *         initialisation fails (e.g., missing model weights, bad camera index).
 *
 * @note The returned handle must be released with ``application_destroy`` when
 *       no longer needed to avoid resource leaks.
 */
ApplicationHandle* application_create(int camera_index, const char* output_dir, int visualize);

/**
 * @brief Inspects a PCB image from disk and returns the detection result.
 *
 * Reads the image at @p image_path, runs YOLO inference, saves an XML report,
 * and returns a ``DetectionResultInfo`` struct. The function is reentrant and
 * can be called in a tight loop without additional initialisation overhead.
 *
 * @param app        Handle returned by ``application_create``. Must not be NULL.
 * @param image_path Null-terminated path to the PCB image (JPEG or PNG).
 *
 * @return A populated ``DetectionResultInfo``. Check ``result.success`` before
 *         reading other fields.
 */
DetectionResultInfo application_process_from_path(ApplicationHandle* app, const char* image_path);

/**
 * @brief Captures a live frame from the hardware camera and inspects it.
 *
 * Triggers a single-shot capture from the camera device associated with the
 * handle, runs inference, and saves the XML report. Use this function in
 * real-time production deployments where the robot control software signals
 * that a PCB has reached the inspection position.
 *
 * @param app Handle returned by ``application_create``. Must not be NULL.
 *
 * @return A populated ``DetectionResultInfo``. Check ``result.success`` before
 *         reading other fields.
 */
DetectionResultInfo application_process_live_camera(ApplicationHandle* app);

/**
 * @brief Releases all resources held by the application handle.
 *
 * Decrements the Python reference count on the ``Application`` instance and
 * frees the handle memory. If this library initialised the Python interpreter
 * (i.e., it was not already running when ``application_create`` was called),
 * ``Py_Finalize`` is also called to shut it down cleanly.
 *
 * @param app Handle to release. Passing NULL is a safe no-op.
 *
 * @warning After this call, @p app is invalid and must not be used.
 */
void application_destroy(ApplicationHandle* app);

#ifdef __cplusplus
}
#endif

#endif /* SOLDER_DEFECT_H */
