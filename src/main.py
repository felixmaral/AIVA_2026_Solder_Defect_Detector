"""
main.py — PCB Solder Defect Detector entry point.

This module is the command-line interface for the PCB inspection system. It
provides two operational modes that exercise the ``Application`` façade:

``single``
    Inspects a single image (from disk or live camera) and exits. Designed for
    on-demand checks and integration testing.

``simulate``
    Cycles continuously through a dataset of reference images stored in
    ``data/simulate/``, applying random data augmentation to each image before
    inference. The inter-plate cadence follows a Gaussian distribution defined
    by ``--mean`` and ``--deviation``. The simulation runs until ``--sim_time``
    seconds have elapsed or the operator presses Ctrl+C, at which point a
    performance report is saved to ``reports/simulate/``.

Usage examples::

    # Inspect a single image file
    python -m src.main --mode single --image data/simulate/Muestra_017.jpg

    # Run a 60-second Gaussian-cadenced simulation (5 ± 2 s between plates)
    python -m src.main --mode simulate --mean 5.0 --deviation 2.0 --sim_time 60

    # Run indefinitely at maximum speed with live visualisation
    python -m src.main --mode simulate --visualize
"""

import os
import sys
import time
import glob
import argparse
import datetime
import random
import itertools
import cv2
import xml.dom.minidom


# Ensure the project root is in sys.path so that ``src.*`` imports resolve
# correctly regardless of the current working directory.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from src.application import Application


def apply_random_augmentation(pcb_image) -> None:
    """
    Applies a random geometric transformation to a ``PCBImage`` in-place.

    Used by the ``simulate`` mode to artificially increase visual diversity
    within a finite dataset, preventing the inference engine from processing
    identical inputs on every cycle. The transformation is applied directly to
    the decoded image matrix and the result is re-encoded as JPEG to keep the
    ``PCBImage`` contract (raw byte payload) consistent.

    Possible transformations (selected uniformly at random):

    - **hflip**: Mirror the image horizontally.
    - **vflip**: Mirror the image vertically.
    - **rotate**: Rotate by a random angle in [-5°, +5°].
    - **none**: Pass the image through without modification.

    Args:
        pcb_image (PCBImage): The image object to transform. Modified in-place;
            both ``_image_data`` and ``_decoded_image`` are updated if a
            transformation is applied.
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
        # Re-encode the transformed matrix back to a JPEG byte payload so that
        # the PCBImage internal state remains consistent for downstream consumers
        success, buffer = cv2.imencode('.jpg', img)
        if success:
            pcb_image._image_data = buffer.tobytes()
            pcb_image._decoded_image = img


def print_xml_if_requested(result: dict, print_xml: bool) -> None:
    """
    Pretty-prints the XML inspection report to stdout if requested.

    Reads either inline XML content (``xml_content`` key) or an XML file path
    (``xml_path`` key) from the result dictionary and formats it with indentation
    for readability. Silently skips if the ``--print-xml`` flag is not set.

    Args:
        result (dict): The result dictionary returned by an ``Application``
            process method. Expected keys: ``xml_content`` and/or ``xml_path``.
        print_xml (bool): Whether to print the XML. Corresponds to the
            ``--print-xml`` command-line flag.
    """
    if not print_xml or not result:
        return

    xml_content = result.get("xml_content")
    xml_path = result.get("xml_path")

    try:
        if xml_content:
            pretty_xml = xml.dom.minidom.parseString(xml_content).toprettyxml(indent="  ")
            print("\n===== XML OUTPUT =====")
            print(pretty_xml)
        elif xml_path and os.path.exists(xml_path):
            with open(xml_path, "r", encoding="utf-8") as f:
                raw_xml = f.read()
            pretty_xml = xml.dom.minidom.parseString(raw_xml).toprettyxml(indent="  ")
            print("\n===== XML OUTPUT =====")
            print(pretty_xml)
        else:
            print("\n[--print-xml] No XML content or xml_path found in result.")
    except Exception as e:
        print(f"[--print-xml] Could not print XML: {e}")


def main() -> None:
    """
    Parses command-line arguments and delegates to the appropriate execution mode.

    Initialises a single ``Application`` instance (which loads the model and
    camera once) and then drives it through either a single inspection or a
    continuous simulation loop. All heavy setup cost is paid once at startup.
    """
    parser = argparse.ArgumentParser(description="PCB Solder Defect Detector")

    parser.add_argument(
        '--mode', type=str, choices=['single', 'simulate'], default='single',
        help="Execution mode: 'single' for one inspection, 'simulate' for a continuous loop.",
    )
    parser.add_argument(
        '--image', type=str, default=None,
        help="Path to an image file (single mode only). If omitted, captures from the live camera.",
    )
    parser.add_argument(
        '--sim_time', type=float, default=None,
        help="Total simulation duration in seconds. If omitted, runs until Ctrl+C.",
    )
    parser.add_argument(
        '--mean', type=float, default=0.0,
        help="Mean inter-plate wait time in seconds (Gaussian). 0 = maximum speed.",
    )
    parser.add_argument(
        '--deviation', type=float, default=0.0,
        help="Standard deviation of the inter-plate wait time in seconds.",
    )
    parser.add_argument(
        '--print-xml', action='store_true',
        help="Pretty-print the XML report to stdout after each detection.",
    )
    parser.add_argument(
        '--visualize', action='store_true',
        help="Show a live OpenCV window with bounding boxes overlaid on each inspected plate.",
    )
    args = parser.parse_args()

    # ── Initialisation ──────────────────────────────────────────────────────
    try:
        system = Application(visualize=args.visualize)
    except Exception as e:
        print(f"Failed to initialize Application: {e}")
        return

    # ── Single mode ─────────────────────────────────────────────────────────
    if args.mode == 'single':
        if args.image:
            result = system.process_from_path(args.image)
            print_xml_if_requested(result, args.print_xml)
        else:
            result = system.process_live_camera()
            print_xml_if_requested(result, args.print_xml)

        if args.visualize:
            print("\n[Visualization Enabled] Press any key in the image window to exit...")
            system.wait_for_key()

    # ── Simulate mode ────────────────────────────────────────────────────────
    elif args.mode == 'simulate':
        simulate_dir = os.path.join(project_root, "data", "simulate")
        print(f"\n--- Entering Simulation Mode ---")
        print(f"Reading base images from: {simulate_dir}")

        if not os.path.exists(simulate_dir):
            print(f"Simulation directory not found: {simulate_dir}")
            return

        # Collect all supported image formats from the simulation dataset
        valid_extensions = ('*.jpg', '*.jpeg', '*.png')
        image_files = []
        for ext in valid_extensions:
            image_files.extend(glob.glob(os.path.join(simulate_dir, ext)))

        image_files.sort()

        if not image_files:
            print(f"No images found in {simulate_dir}")
            return

        if args.sim_time is not None:
            print(f"Starting {args.sim_time}-second simulation with {len(image_files)} base images.")
        else:
            print(f"Starting indefinite simulation with {len(image_files)} base images. Press Ctrl+C to stop.")

        if args.mean > 0:
            print(f"Gaussian cadence: mean={args.mean}s, deviation={args.deviation}s\n")
        else:
            print("Maximum speed mode (no cadence delay).\n")

        total_images = 0
        overall_start_time = time.time()
        processing_times = []

        try:
            # Cycle through the dataset indefinitely; sim_time acts as the exit condition
            for img_path in itertools.cycle(image_files):

                # Check elapsed time before processing each new plate
                if args.sim_time is not None:
                    if (time.time() - overall_start_time) >= args.sim_time:
                        print(f"\nSimulation time ({args.sim_time}s) reached.")
                        break

                start_time = time.time()

                print(f"\n[Sim] Processing augmented image from: {img_path}")
                pcb_img = system.camera.get_image_from_file(img_path)
                apply_random_augmentation(pcb_img)

                # Name the output XML with an '_aug' suffix to distinguish
                # augmented results from original single-capture reports
                result = system.process_pcb_image(
                    pcb_img,
                    custom_name=f"{os.path.splitext(os.path.basename(img_path))[0]}_aug",
                )
                print_xml_if_requested(result, args.print_xml)

                proc_time = result.get('processing_time_s', 0.0)
                if proc_time > 0:
                    processing_times.append(proc_time)

                total_images += 1

                # Compute the remaining wait time after subtracting inference cost
                elapsed_proc = time.time() - start_time
                if args.mean > 0:
                    target_sleep = random.gauss(args.mean, args.deviation)
                    sleep_time = max(0.1, target_sleep - elapsed_proc)
                    print(f"Waiting for next plate... ({sleep_time:.2f}s)")
                    system.wait(sleep_time)
                else:
                    # In maximum-speed mode, pump the UI event loop for one tick
                    system.wait(0)

        except KeyboardInterrupt:
            print("\nSimulation aborted by user.")

        # ── Report generation ────────────────────────────────────────────────
        print("\nGenerating Simulation Report...")
        if processing_times:
            total_elapsed = time.time() - overall_start_time
            fps = total_images / total_elapsed
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)

            print("\n--- Simulation Speed Statistics ---")
            print(f"Total images processed: {total_images}")
            print(f"Total time elapsed:     {total_elapsed:.2f} seconds")
            print(f"Speed:                  {fps:.2f} FPS")
            print(f"Avg processing time:    {avg_time * 1000:.2f} ms")

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
                f.write(f"Average Processing Time: {avg_time * 1000:.2f} ms\n")
                f.write(f"Max Processing Time: {max_time * 1000:.2f} ms\n")
                f.write(f"Min Processing Time: {min_time * 1000:.2f} ms\n")

            print(f"\nSimulation report saved to: {report_filename}")
        else:
            print("No images were processed. No report generated.")


if __name__ == "__main__":
    main()
