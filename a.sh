#!/bin/bash

# Creates empty test files for the PCB Defect Detector project.

TARGET_DIR="/Users/felixmaral/Documents/Repositories/AIVA_2026_Solder_Defect_Detector/tests"

# Ensure the target directory exists
mkdir -p "$TARGET_DIR"

# Create empty Python test files
touch "$TARGET_DIR/test_solder_defect.py"
touch "$TARGET_DIR/test_pcb_image.py"
touch "$TARGET_DIR/test_camera.py"
touch "$TARGET_DIR/test_detector.py"
touch "$TARGET_DIR/test_main_integration.py"