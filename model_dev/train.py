import os
from ultralytics import YOLO
from dataset import prepare_yolo_dataset, generate_yaml_config

def train_model(yaml_path: str) -> None:
    """
    Initializes the YOLO architecture and executes the training pipeline.
    Applies real-time data augmentation.
    
    Args:
        yaml_path (str): Path to the dataset YAML configuration file.
    """
    model = YOLO('yolo11n.pt')
    
    model.train(
        data=yaml_path,
        epochs=100,
        imgsz=640,
        batch=16,
        project='/kaggle/working/',
        name='sdd_grayscale_training',
        patience=20,
        cache=True,
        workers=2,
        exist_ok=True,
        degrees=15.0,  
        fliplr=0.5,    
        flipud=0.5     
    )

if __name__ == "__main__":
    INPUT_DIR = "/kaggle/input/datasets/felixmartinezalonso/sdd-solderdefects/SDD.coco/train"
    JSON_FILE = os.path.join(INPUT_DIR, "_annotations.coco.json")
    WORK_DIR = "/kaggle/working/dataset_yolo_grayscale"
    
    if os.path.exists(JSON_FILE):
        class_names = prepare_yolo_dataset(JSON_FILE, INPUT_DIR, WORK_DIR)
        yaml_config_path = generate_yaml_config(WORK_DIR, class_names)
        
        print("Data processing complete. Starting model training...")
        train_model(yaml_config_path)
    else:
        print(f"Critical Error: Annotation file not found at {JSON_FILE}")