import os
import sys
import time
import glob
import argparse
import datetime
import random
import itertools
import cv2

# Ensure the project root is in the python path to allow absolute imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.hardware.camera import Camera
from src.vision.detector import Detector

def apply_random_augmentation(pcb_image):
    """
    Applies a random transformation to the PCBImage to simulate variations.
    Possible transformations: Horizontal flip, Vertical flip, Slight rotation, or None.
    """
    pcb_image._calculate_dimensions()
    img = pcb_image._decoded_image
    
    if img is None:
        return
        
    choice = random.choice(['hflip', 'vflip', 'rotate', 'none'])
    
    if choice == 'hflip':
        img = cv2.flip(img, 1)
    elif choice == 'vflip':
        img = cv2.flip(img, 0)
    elif choice == 'rotate':
        angle = random.uniform(-5, 5)
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderValue=(0, 0, 0))
        
    if choice != 'none':
        success, buffer = cv2.imencode('.jpg', img)
        if success:
            pcb_image._image_data = buffer.tobytes()
            pcb_image._decoded_image = img

def process_image(camera, detector, image_path=None, pcb_image=None):
    """
    Executes a single detection cycle on a given image.
    """
    try:
        if pcb_image is None:
            if image_path:
                print(f"\nProcessing local image: {image_path}")
                pcb_image = camera.get_image_from_file(image_path)
            else:
                print("\nError: No image path provided.")
                return 0.0

        print(f"Image captured: {pcb_image.get_resolution()} - {pcb_image.get_size_bytes()} bytes")
        
        # Inicio estricto del cronómetro "desde que nos entregan la imagen"
        proc_start = time.time()
        
        print("Running defect detection...")
        detection_result = detector.detect(pcb_image)
        xml_report = detection_result.to_xml()
        
        print("Inspection Completed. XML Report:")
        print(xml_report)
        
        # Save XML to reports/xml
        xml_dir = os.path.join(project_root, "reports", "xml")
        os.makedirs(xml_dir, exist_ok=True)
        
        if image_path:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
        else:
            base_name = f"Capture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        xml_filename = os.path.join(xml_dir, f"{base_name}.xml")
        with open(xml_filename, 'w') as f:
            f.write(xml_report)
        print(f"XML saved to {xml_filename}")
        
        # Fin del cronómetro "hasta que se entrega el xml"
        proc_time = time.time() - proc_start
        return proc_time
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 0.0
    except Exception as e:
        print(f"An unexpected error occurred during detection: {e}")
        return 0.0

def main():
    """
    Main execution flow for the PCB inspection system.
    Orchestrates camera capture, detection, and XML reporting.
    """
    parser = argparse.ArgumentParser(description="PCB Solder Defect Detector")
    parser.add_argument('--mode', type=str, choices=['single', 'simulate', 'simulate_24h'], default='single',
                        help="Execution mode: 'single' for a single image capture, 'simulate' for a cadence simulation, 'simulate_24h' for infinite loops with augmented data.")
    parser.add_argument('--image', type=str, default=None,
                        help="Path to an image file (for 'single' mode). If not provided, it attempts to use the physical camera.")
    parser.add_argument('--sim_time', type=float, default=None,
                        help="Time in seconds between frames for 'simulate' mode. If not provided, it runs at maximum speed and calculates statistics.")
    args = parser.parse_args()

    print("Initializing hardware camera interface...")
    camera = Camera(camera_index=0)
    
    print("Loading YOLO detector...")
    try:
        detector = Detector()
    except FileNotFoundError as e:
        print(f"Error loading model: {e}")
        return

    if args.mode == 'single':
        process_image(camera, detector, args.image)
    
    elif args.mode == 'simulate':
        simulate_dir = os.path.join(project_root, "data", "simulate")
        print(f"\n--- Entering Simulation Mode ---")
        print(f"Reading images from: {simulate_dir}")
        
        if not os.path.exists(simulate_dir):
            print(f"Simulation directory not found: {simulate_dir}")
            return
            
        valid_extensions = ('*.jpg', '*.jpeg', '*.png')
        image_files = []
        for ext in valid_extensions:
            image_files.extend(glob.glob(os.path.join(simulate_dir, ext)))
            
        image_files.sort()
        
        if not image_files:
            print(f"No images found in {simulate_dir}")
            return
            
        if args.sim_time is not None:
            print(f"Found {len(image_files)} images. Starting {args.sim_time}-second cadence simulation...\n")
        else:
            print(f"Found {len(image_files)} images. Starting maximum speed simulation...\n")
        
        total_images = 0
        overall_start_time = time.time()
        processing_times = []
        
        try:
            for img_path in image_files:
                start_time = time.time()
                
                proc_time = process_image(camera, detector, image_path=img_path)
                if proc_time > 0:
                    processing_times.append(proc_time)
                
                total_images += 1
                
                if args.sim_time is not None:
                    elapsed_time = time.time() - start_time
                    sleep_time = max(0, args.sim_time - elapsed_time)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\nSimulation aborted by user.")
            
        if processing_times:
            total_elapsed = time.time() - overall_start_time
            fps = total_images / total_elapsed
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)
            
            if args.sim_time is None:
                print("\n--- Simulation Speed Statistics ---")
                print(f"Total images processed: {total_images}")
                print(f"Total time elapsed: {total_elapsed:.2f} seconds")
                print(f"Speed: {fps:.2f} FPS")
                print(f"Average processing time per image: {avg_time*1000:.2f} ms")
                
            report_dir = os.path.join(project_root, "reports", "simulate")
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = os.path.join(report_dir, f"simulation_report_{timestamp}.txt")
            
            with open(report_filename, 'w') as f:
                f.write("=== Simulation Mode Report ===\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Total Uptime: {total_elapsed:.2f} seconds\n")
                f.write(f"Total Images Processed: {total_images}\n")
                f.write(f"Effective Speed: {fps:.2f} FPS\n")
                f.write(f"Average Processing Time: {avg_time*1000:.2f} ms\n")
                f.write(f"Max Processing Time: {max_time*1000:.2f} ms\n")
                f.write(f"Min Processing Time: {min_time*1000:.2f} ms\n")
                
            print(f"\nSimulation report saved to: {report_filename}")

    elif args.mode == 'simulate_24h':
        simulate_dir = os.path.join(project_root, "data", "simulate")
        print(f"\n--- Entering 24H Simulation Mode ---")
        
        valid_extensions = ('*.jpg', '*.jpeg', '*.png')
        image_files = []
        for ext in valid_extensions:
            image_files.extend(glob.glob(os.path.join(simulate_dir, ext)))
            
        if not image_files:
            print(f"No images found in {simulate_dir}")
            return
            
        mu = args.sim_time if args.sim_time is not None else 5.0
        sigma = 2.0
        print(f"Starting 24H simulation with {len(image_files)} base images.")
        print(f"Gaussian cadence: mu={mu}s, sigma={sigma}s\n")
        
        processing_times = []
        overall_start_time = time.time()
        
        try:
            for img_path in itertools.cycle(image_files):
                start_time = time.time()
                
                print(f"\n[24H Sim] Processing augmented image from: {img_path}")
                pcb_img = camera.get_image_from_file(img_path)
                apply_random_augmentation(pcb_img)
                
                proc_time = process_image(camera, detector, image_path=img_path, pcb_image=pcb_img)
                if proc_time > 0:
                    processing_times.append(proc_time)
                
                elapsed_time = time.time() - start_time
                target_sleep = random.gauss(mu, sigma)
                sleep_time = max(0.1, target_sleep - elapsed_time)  # At least 0.1s to prevent locking
                print(f"Waiting for next plate... ({sleep_time:.2f}s)")
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\n24H Simulation aborted by user. Generating Stress Report...")
            
            if processing_times:
                total_uptime = time.time() - overall_start_time
                total_processed = len(processing_times)
                avg_time = sum(processing_times) / total_processed
                max_time = max(processing_times)
                min_time = min(processing_times)
                
                report_dir = os.path.join(project_root, "reports", "stress_tests")
                os.makedirs(report_dir, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                report_filename = os.path.join(report_dir, f"stress_report_{timestamp}.txt")
                
                with open(report_filename, 'w') as f:
                    f.write("=== 24H Stress Test Report ===\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Total Uptime: {total_uptime:.2f} seconds\n")
                    f.write(f"Total Images Processed: {total_processed}\n")
                    f.write(f"Average Processing Time: {avg_time*1000:.2f} ms\n")
                    f.write(f"Max Processing Time: {max_time*1000:.2f} ms\n")
                    f.write(f"Min Processing Time: {min_time*1000:.2f} ms\n")
                    
                print(f"Report generated successfully: {report_filename}")
            else:
                print("Simulation aborted before any image was processed. No report generated.")

if __name__ == "__main__":
    main()
