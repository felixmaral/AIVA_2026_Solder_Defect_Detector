#include <stdio.h>
#include <unistd.h>
#include "solder_defect.h"

int main() {
    printf("Starting Robot Control Software (C Client)\n");
    printf("------------------------------------------\n");

    // Initialize the vision system (camera 0, default output dir, visualize = false)
    printf("Initializing Vision System...\n");
    ApplicationHandle* app = application_create(0, NULL, 0);
    
    if (!app) {
        fprintf(stderr, "Fatal Error: Could not initialize vision system.\n");
        return 1;
    }
    printf("Vision System initialized successfully.\n\n");

    // Example 1: Process an existing file
    const char* sample_image = "data/simulate/Muestra_017.jpg";
    printf("Robot sending image to vision system: %s\n", sample_image);
    
    DetectionResultInfo result = application_process_from_path(app, sample_image);
    
    if (result.success) {
        printf(">>> Inspection Result <<<\n");
        printf("Defects found: %d\n", result.detection_count);
        printf("Processing time: %.2f ms\n", result.processing_time_ms);
        printf("XML Report saved to: %s\n", result.xml_path);
        
        if (result.detection_count > 0) {
            printf("[ROBOT ACTION] Solding PCB due to defects.\n");
        } else {
            printf("[ROBOT ACTION] PCB is good. Moving to next stage.\n");
        }
    } else {
        printf("Inspection failed.\n");
    }
    
    printf("\n");

    // Clean up
    printf("Shutting down Vision System...\n");
    application_destroy(app);
    printf("Done.\n");

    return 0;
}
