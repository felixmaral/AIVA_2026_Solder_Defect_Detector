import numpy as np
import sys
import time
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score

# Configuración de rutas
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.core.pcb_image import PCBImage
from src.vision.detector import Detector

# Constantes de evaluación
MODEL_PATH = str(ROOT_DIR / "model_dev" / "weights" / "best.pt")
IMAGES_PATH = ROOT_DIR / "evaluation" / "SDD.yolo26" / "train" / "images"
LABELS_PATH = ROOT_DIR / "evaluation" / "SDD.yolo26" / "train" / "labels"
IOU_THRESHOLD = 0.50
CONF_THRESHOLD = 0.35

def calculate_iou(box1, box2):
    x_left, y_top = max(box1[0], box2[0]), max(box1[1], box2[1])
    x_right, y_bottom = min(box1[2], box2[2]), min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    return intersection_area / float(area1 + area2 - intersection_area)

def evaluate():
    detector = Detector(weights_path=MODEL_PATH, conf_threshold=CONF_THRESHOLD)
    tp, fp, fn = 0, 0, 0
    ious_log, times_log = [], []
    safety_threshold = 0.0

    img_files = [f for f in IMAGES_PATH.glob('*') if f.suffix in ('.jpg', '.png', '.jpeg')]
    y_true_roc, y_scores_roc = [], []
    datos_por_placa = []
    
    for img_path in img_files:
        with open(img_path, 'rb') as f:
            image_bytes = f.read()
        
        pcb_image = PCBImage(image_data=image_bytes, filepath=str(img_path))
        w, h = pcb_image.get_width(), pcb_image.get_height()

        base_name = img_path.stem
        label_file = next(LABELS_PATH.glob(f"{base_name}*.txt"), None)
        
        gt_boxes = []
        if label_file:
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) == 5:
                        _, xc, yc, bw, bh = map(float, parts)
                        gt_boxes.append([(xc - bw/2) * w, (yc - bh/2) * h, (xc + bw/2) * w, (yc + bh/2) * h])

        start_time = time.time()
        detection_result = detector.detect(pcb_image)
        times_log.append(time.time() - start_time)

        pred_boxes = [[d.top_left_x, d.top_left_y, d.top_left_x + d.width, d.top_left_y + d.height] for d in detection_result.defects]
        confidences = [d.confidence for d in detection_result.defects]

        matched_gt = set()
        is_hit_list = [] # Esta lista tendrá el mismo tamaño que pred_boxes

        for p_box in pred_boxes:
            best_iou, best_gt_idx = 0, -1
            for i, g_box in enumerate(gt_boxes):
                if i in matched_gt: continue
                iou = calculate_iou(p_box, g_box)
                if iou > best_iou:
                    best_iou, best_gt_idx = iou, i
            
            if best_iou >= IOU_THRESHOLD:
                is_hit_list.append(True)
                matched_gt.add(best_gt_idx)
                tp += 1
                ious_log.append(best_iou)
            else:
                is_hit_list.append(False)
                fp += 1

        fn += (len(gt_boxes) - len(matched_gt))
        y_true_roc.extend([1 if h else 0 for h in is_hit_list])
        y_scores_roc.extend(confidences)

        # Guardamos la información sincronizada por placa
        datos_por_placa.append({
            'preds': confidences,
            'is_hit': is_hit_list,
            'has_gt': len(gt_boxes) > 0,
            'num_gt': len(gt_boxes)
        })

    # Estadísticas y gráficas
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    results_path = ROOT_DIR / "evaluation" / "results"
    results_path.mkdir(parents=True, exist_ok=True)

    # Lógica de costes
    C_PLACA, C_RETRABAJO, C_FALLO_CRITICO = 500, -15, -2000
    umbrales_test = np.linspace(1.0, 0.0, 100)
    coste_por_umbral = []

    for u in umbrales_test:
        ahorro_total = 0
        for placa in datos_por_placa:
            indices_u = [i for i, conf in enumerate(placa['preds']) if conf >= u]
            num_aciertos = sum([1 for i in indices_u if placa['is_hit'][i]])
            num_fps = len(indices_u) - num_aciertos
            
            ahorro_total += (num_fps * C_RETRABAJO)

            if placa['has_gt']:
                # La placa no es defectuosa si detecta todos los fallos de la placa
                if num_aciertos >= placa['num_gt']:
                    ahorro_total += C_PLACA
                else:
                    ahorro_total += C_FALLO_CRITICO
        
        coste_por_umbral.append(ahorro_total / 100.0)

    # Graficar impacto económico
    plt.figure(figsize=(8, 6))
    plt.plot(umbrales_test, coste_por_umbral, color='purple', lw=2)
    idx_max = np.argmax(coste_por_umbral)
    plt.scatter(umbrales_test[idx_max], coste_por_umbral[idx_max], color='red', s=100, zorder=5,
                label=f'Punto óptimo: {umbrales_test[idx_max]:.2f} ({coste_por_umbral[idx_max]:.2f}€)')
    plt.xlabel('Umbral de confianza')
    plt.ylabel('Beneficio neto estimado (€)')
    plt.title('Optimización económica por placa')
    plt.gca().invert_xaxis()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.savefig(results_path / "cost_curve.png")

    # Curva precision-recall (P-R)
    if len(y_true_roc) > 0:
        precision_points, recall_points, _ = precision_recall_curve(y_true_roc, y_scores_roc)
        avg_precision = average_precision_score(y_true_roc, y_scores_roc)

        plt.figure(figsize=(8, 6))
        plt.plot(recall_points, precision_points, color='blue', lw=2, label=f'AP = {avg_precision:.4f}')
        plt.fill_between(recall_points, precision_points, alpha=0.2, color='blue', step='post')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Curva Precision-Recall (P-R)')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend(loc='lower left')
        plt.savefig(results_path / "precision_recall_curve.png")

    # Bloque de estadísticas
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # TPR y FNR
    tpr = recall
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0
    
    # Contraste de hipótesis (H0: acierto < 90%)
    p_val = stats.binomtest(tp, tp + fp + fn, p=0.90, alternative='greater').pvalue

    # Pre-cálculo de eficiencia y umbral de seguridad
    fp_per_image = fp / len(img_files) if img_files else 0
    if y_true_roc:
        _, tpr_roc, thresholds = roc_curve(y_true_roc, y_scores_roc)
        idx_100 = np.where(tpr_roc >= 1.0)[0][0]
        safety_threshold = thresholds[idx_100]

    # Impresión
    print("\n" + "="*45)
    print("       INSPECTION SYSTEM PERFORMANCE")
    print("="*45)
    print(f"Detecciones: TP: {tp} | FP: {fp} | FN: {fn}")
    print(f"Métricas:    Prec: {precision:.4f} | Rec: {recall:.4f} | F1: {f1:.4f}")
    print(f"Tasas:       TPR: {tpr:.4f} | FNR: {fnr:.4f} | FPR: {fp_per_image:.2f} FP/img")
    print(f"Mean IoU: {np.mean(ious_log):.4f}" if ious_log else "IoU: N/A")
    print(f"Tiempo medio: {np.mean(times_log):.4f}s (Max: {max(times_log):.4f}s)")
    print(f"P-Valor (Garantía 90%): {p_val:.4f}")
    if y_true_roc:
        print(f"Umbral máximo para Recall 100%: {safety_threshold:.4f}")
    print(f"Eficiencia operativa: {fp_per_image:.2f} falsas alarmas por imagen")
    print("="*45)
    
    # Información adicional de gráficas (rutas de guardado)
    if y_true_roc:
        print(f"Gráfica ROC guardada en: {results_path / 'roc_curve.png'}")
        print(f"Gráfica P-R guardada en: {results_path / 'precision_recall_curve.png'}")
        print(f"Gráfica de verdaderos positivos guardada en: {results_path / 'true_positives_curve.png'}")
        print(f"Gráfica económica guardada en: {results_path / 'cost_curve.png'}")

if __name__ == "__main__":
    evaluate()