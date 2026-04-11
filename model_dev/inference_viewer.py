import os
import cv2
import argparse
from ultralytics import YOLO

def run_interactive_inference(weights_path: str, images_dir: str) -> None:
    """
    Carga un modelo YOLO entrenado y abre una ventana interactiva de OpenCV para 
    evaluar visualmente las imágenes de un directorio. La navegación se controla mediante el teclado.
    
    Args:
        weights_path (str): Ruta absoluta a los pesos entrenados de YOLO (archivo .pt).
        images_dir (str): Ruta absoluta al directorio que contiene las imágenes de prueba.
    """
    if not os.path.exists(weights_path):
        print(f"Error: No se encontró el archivo de pesos en {weights_path}")
        return
        
    if not os.path.exists(images_dir):
        print(f"Error: No se encontró el directorio de imágenes en {images_dir}")
        return

    # Inicialización del modelo YOLO
    model = YOLO(weights_path)
    
    # Filtrado y ordenación de archivos de imagen válidos
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(valid_extensions)]
    image_files.sort()
    
    total_images = len(image_files)
    if total_images == 0:
        print("Error: No se encontraron imágenes válidas en el directorio especificado.")
        return

    print("Visor de inferencia interactivo iniciado.")
    print("Controles:")
    print("  - Flecha Derecha (o 'D'): Siguiente imagen")
    print("  - Flecha Izquierda (o 'A'): Imagen anterior")
    print("  - ESC o 'Q': Salir del visor")

    current_index = 0
    window_name = "YOLO Inference Evaluation"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        file_name = image_files[current_index]
        image_path = os.path.join(images_dir, file_name)
        
        # Carga de la imagen
        img = cv2.imread(image_path)
        if img is None:
            print(f"Advertencia: No se pudo leer la imagen {file_name}. Omitiendo.")
            current_index = min(current_index + 1, total_images - 1)
            continue
            
        # Preprocesamiento: Conversión a escala de grises y retorno a 3 canales
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_input = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        
        # Ejecución de la inferencia
        results = model.predict(source=img_input, conf=0.25, verbose=False)
        annotated_frame = results[0].plot()
        
        # Superposición de la interfaz de usuario: Estado del progreso
        text_overlay = f"Imagen {current_index + 1}/{total_images}: {file_name}"
        cv2.putText(annotated_frame, text_overlay, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow(window_name, annotated_frame)
        
        # Captura de eventos del teclado
        key = cv2.waitKeyEx(0)
        
        # Condición de salida: ESC (27) o 'q'/'Q'
        if key == 27 or key == ord('q') or key == ord('Q'):
            break
            
        # Siguiente imagen: Flecha derecha o 'd'/'D'
        elif key in (2555904, 63235, 83, ord('d'), ord('D')):
            if current_index < total_images - 1:
                current_index += 1
                
        # Imagen anterior: Flecha izquierda o 'a'/'A'
        elif key in (2424832, 63234, 81, ord('a'), ord('A')):
            if current_index > 0:
                current_index -= 1

    # Liberación de recursos
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Configuración de los argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Ejecuta inferencia interactiva de YOLO sobre un directorio de imágenes.")
    parser.add_argument(
        "--weights", 
        type=str, 
        required=True, 
        help="Ruta al archivo de pesos entrenados de YOLO (.pt)."
    )
    parser.add_argument(
        "--images_dir", 
        type=str, 
        required=True, 
        help="Ruta al directorio que contiene las imágenes de prueba."
    )
    
    args = parser.parse_args()
    
    run_interactive_inference(args.weights, args.images_dir)