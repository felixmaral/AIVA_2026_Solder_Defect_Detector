import os
from ultralytics import YOLO

def evaluate_model(weights_path: str, yaml_path: str) -> None:
    """
    Loads a trained YOLO model and evaluates its performance on the test split.
    
    Args:
        weights_path (str): Path to the optimized model weights (.pt file).
        yaml_path (str): Path to the dataset YAML configuration file.
    """
    if not os.path.exists(weights_path):
        print(f"Error: Model weights not found at {weights_path}")
        return
        
    model = YOLO(weights_path)
    
    print("Initiating evaluation on the test subset...")
    metrics = model.val(
        data=yaml_path,
        split='test',
        project=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs'),
        name='sdd_evaluation',
        exist_ok=True
    )
    
    print("Evaluation successful. Results saved to the project directory.")

if __name__ == "__main__":
    # Standard output paths based on the training configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    TRAINED_WEIGHTS = os.path.join(base_dir, "logs", "sdd_grayscale_training", "weights", "best.pt")
    YAML_CONFIG = os.path.join(base_dir, "dataset_yolo_grayscale", "dataset.yaml")
    
    evaluate_model(TRAINED_WEIGHTS, YAML_CONFIG)