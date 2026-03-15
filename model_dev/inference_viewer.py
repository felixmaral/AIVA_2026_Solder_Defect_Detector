import os
import cv2
from ultralytics import YOLO

def run_interactive_inference(weights_path: str, images_dir: str) -> None:
    """
    Loads a trained YOLO model and opens an interactive OpenCV window to visually 
    evaluate images from a specified directory. Navigation is controlled via keyboard.
    
    Args:
        weights_path (str): Absolute path to the trained YOLO weights (.pt file).
        images_dir (str): Absolute path to the directory containing test images.
    """
    if not os.path.exists(weights_path):
        print(f"Error: Weights file not found at {weights_path}")
        return
        
    if not os.path.exists(images_dir):
        print(f"Error: Image directory not found at {images_dir}")
        return

    # Initialize the YOLO model
    model = YOLO(weights_path)
    
    # Filter valid image files and sort them alphabetically
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(valid_extensions)]
    image_files.sort()
    
    total_images = len(image_files)
    if total_images == 0:
        print("Error: No valid images found in the specified directory.")
        return

    print("Interactive Inference Viewer Started.")
    print("Controls:")
    print("  - Right Arrow (or 'D'): Next image")
    print("  - Left Arrow (or 'A'): Previous image")
    print("  - ESC or 'Q': Quit viewer")

    current_index = 0
    window_name = "YOLO Inference Evaluation"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        file_name = image_files[current_index]
        image_path = os.path.join(images_dir, file_name)
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print(f"Warning: Could not read image {file_name}. Skipping.")
            current_index = min(current_index + 1, total_images - 1)
            continue
            
        # Preprocessing: Convert to grayscale and back to 3 channels to match training data
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_input = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        
        # Execute inference
        # YOLO's predict method handles the bounding box and confidence rendering internally
        results = model.predict(source=img_input, conf=0.25, verbose=False)
        annotated_frame = results[0].plot()
        
        # UI Overlay: Display progress
        text_overlay = f"Image {current_index + 1}/{total_images}: {file_name}"
        cv2.putText(annotated_frame, text_overlay, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow(window_name, annotated_frame)
        
        # Wait for user input (waitKeyEx captures special keys like arrows across OS)
        key = cv2.waitKeyEx(0)
        
        # Exit condition: ESC (27) or 'q'
        if key == 27 or key == ord('q') or key == ord('Q'):
            break
            
        # Next image: Right Arrow keys (OS dependent codes) or 'd'
        elif key in (2555904, 63235, 83, ord('d'), ord('D')):
            if current_index < total_images - 1:
                current_index += 1
                
        # Previous image: Left Arrow keys (OS dependent codes) or 'a'
        elif key in (2424832, 63234, 81, ord('a'), ord('A')):
            if current_index > 0:
                current_index -= 1

    # Clean up resources
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Update these paths according to your local environment structure
    TRAINED_WEIGHTS = "/Users/felixmaral/Documents/Repositories/AIVA_2026_Solder_Defect_Detector/model_dev/weights/best.pt"
    TEST_IMAGES_DIR = "model_dev/datasets"
    
    run_interactive_inference(TRAINED_WEIGHTS, TEST_IMAGES_DIR)