/**
 * @file example.c
 * @brief Minimal C client demonstrating the solder defect detection API.
 *
 * This program shows the complete lifecycle of the C API:
 *   1. Initialise the vision system (loads the camera and YOLO model).
 *   2. Inspect a reference PCB image from disk.
 *   3. Take a robot control decision based on the result.
 *   4. Shut down cleanly before process exit.
 *
 * Compile and run from the project root after building the shared library:
 * @code{.sh}
 *   make -C src/c_bindings
 *   cd src/c_bindings && ./example
 * @endcode
 */

#include <stdio.h>
#include "solder_defect.h"

int main(void) {
    printf("=== Robot Control Software — PCB Inspection Demo ===\n\n");

    /* ── Step 1: Initialise the vision system ──────────────────────────────
     * camera_index = 0  → primary Raspberry Pi camera
     * output_dir   = NULL → use default reports/xml/ directory
     * visualize    = 0  → headless mode (no OpenCV window)                 */
    printf("Initializing vision system...\n");
    ApplicationHandle* app = application_create(0, NULL, 0);
    if (!app) {
        fprintf(stderr, "Fatal: Failed to initialise the vision system.\n");
        return 1;
    }
    printf("Vision system ready.\n\n");

    /* ── Step 2: Inspect a reference PCB image ──────────────────────────── */
    const char* sample_image = "data/simulate/Muestra_017.jpg";
    printf("Inspecting plate: %s\n", sample_image);

    DetectionResultInfo result = application_process_from_path(app, sample_image);

    /* ── Step 3: Robot control decision ─────────────────────────────────── */
    if (result.success) {
        printf("\n>>> Inspection Result <<<\n");
        printf("  Defects found   : %d\n",   result.detection_count);
        printf("  Processing time : %.2f ms\n", result.processing_time_ms);
        printf("  XML report      : %s\n",   result.xml_path);

        if (result.detection_count > 0) {
            printf("\n[ROBOT] Defective plate — routing to re-soldering station.\n");
        } else {
            printf("\n[ROBOT] No defects — advancing plate to next stage.\n");
        }
    } else {
        fprintf(stderr, "\n[ROBOT] Inspection failed. Halting line for manual review.\n");
    }

    /* ── Step 4: Clean shutdown ──────────────────────────────────────────── */
    printf("\nShutting down vision system...\n");
    application_destroy(app);
    printf("Done.\n");

    return 0;
}
