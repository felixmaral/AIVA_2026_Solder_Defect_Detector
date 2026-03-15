import os
import json
import yaml
import random
import cv2

def prepare_yolo_dataset(json_path: str, images_path: str, output_path: str, 
                         train_ratio: float = 0.86, val_ratio: float = 0.07) -> list:
    """
    Converts COCO annotations to YOLO format, applies grayscale transformation,
    and splits the dataset into Train, Validation, and Test subsets.
    
    Args:
        json_path (str): Absolute path to the JSON annotation file.
        images_path (str): Absolute path to the source images directory.
        output_path (str): Target working directory for the processed dataset.
        train_ratio (float): Dataset proportion allocated for training.
        val_ratio (float): Dataset proportion allocated for validation.
        
    Returns:
        list: Extracted class names mapped to YOLO indices (base 0).
    """
    subsets = ['train', 'val', 'test']
    for sub in subsets:
        os.makedirs(os.path.join(output_path, f'images/{sub}'), exist_ok=True)
        os.makedirs(os.path.join(output_path, f'labels/{sub}'), exist_ok=True)
        
    with open(json_path, 'r') as f:
        coco_data = json.load(f)
        
    used_ids = sorted(list(set([ann['category_id'] for ann in coco_data['annotations']])))
    class_map = {original_id: new_id for new_id, original_id in enumerate(used_ids)}
    
    name_dict = {cat['id']: cat['name'] for cat in coco_data['categories']}
    class_names = [name_dict[original_id] for original_id in used_ids]
    
    annotations_by_image = {}
    for ann in coco_data['annotations']:
        img_id = ann['image_id']
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)
        
    images = coco_data['images']
    random.seed(42)
    random.shuffle(images)
    
    train_limit = int(len(images) * train_ratio)
    val_limit = train_limit + int(len(images) * val_ratio)
    
    splits = {
        'train': images[:train_limit],
        'val': images[train_limit:val_limit],
        'test': images[val_limit:]
    }
    
    def process_subset(subset_imgs: list, subset_name: str) -> None:
        """
        Executes image transformation and coordinate normalization per dataset split.
        """
        for img_info in subset_imgs:
            file_name = img_info['file_name']
            img_id = img_info['id']
            img_width = float(img_info['width'])
            img_height = float(img_info['height'])
            
            src_img = os.path.join(images_path, file_name)
            dst_img = os.path.join(output_path, 'images', subset_name, file_name)
            
            if not os.path.exists(src_img):
                continue
                
            img = cv2.imread(src_img)
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_final = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(dst_img, img_final)
            
            txt_name = os.path.splitext(file_name)[0] + '.txt'
            txt_path = os.path.join(output_path, 'labels', subset_name, txt_name)
            
            with open(txt_path, 'w') as f:
                if img_id in annotations_by_image:
                    for ann in annotations_by_image[img_id]:
                        bbox = [float(coord) for coord in ann['bbox']]
                        yolo_class = class_map[ann['category_id']]
                        
                        x_center = (bbox[0] + bbox[2] / 2) / img_width
                        y_center = (bbox[1] + bbox[3] / 2) / img_height
                        w = bbox[2] / img_width
                        h = bbox[3] / img_height
                        
                        f.write(f"{yolo_class} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")

    for split_name, split_data in splits.items():
        process_subset(split_data, split_name)
    
    return class_names

def generate_yaml_config(output_path: str, class_names: list) -> str:
    """
    Creates the dataset.yaml configuration file required for YOLO training.
    
    Args:
        output_path (str): Root directory of the processed dataset.
        class_names (list): Ordered list of class string labels.
        
    Returns:
        str: Absolute path to the generated YAML file.
    """
    config = {
        'path': output_path,
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'nc': len(class_names),
        'names': class_names
    }
    
    yaml_path = os.path.join(output_path, 'dataset.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
    return yaml_path