# Model Development (model_dev)

Este directorio contiene los scripts y utilidades para la preparacion de datos, entrenamiento y evaluacion del modelo YOLO utilizado en la deteccion de defectos de soldadura.

## Modulos Principales

### 1. dataset.py
Script encargado del procesamiento de datos. Transforma las anotaciones de formato COCO a formato YOLO. Ademas, convierte las imagenes a escala de grises (manteniendo una estructura de 3 canales requerida por YOLO) y divide automaticamente el conjunto de datos en subconjuntos de entrenamiento (train), validacion (val) y prueba (test). Genera el archivo `dataset.yaml`.

### 2. train.py
Orquesta el pipeline de entrenamiento.
- **Uso:** `python train.py`
- Llama internamente a `dataset.py` para preparar los datos antes de entrenar.
- Entrena la red YOLOv11 aplicando tecnicas de data augmentation.
- Guarda los modelos resultantes (como `best.pt`) dentro del directorio `logs/`.

### 3. evaluate.py
Script para medir el rendimiento del modelo entrenado.
- **Uso:** `python evaluate.py`
- Carga los pesos del modelo optimizado (`best.pt`).
- Ejecuta una evaluacion formal sobre el subconjunto de prueba (`test`) que no fue visto durante el entrenamiento.
- Almacena las metricas de rendimiento (matrices de confusion, curvas PR) en el directorio `logs/sdd_evaluation/`.

### 4. inference_viewer.py
Herramienta visual para probar el modelo cualitativamente.
- **Uso:** `python inference_viewer.py --weights ruta_al_modelo.pt --images_dir ruta_a_imagenes`
- Abre una ventana interactiva utilizando OpenCV.
- Permite navegar por las imagenes con las flechas del teclado (o teclas 'A' y 'D') visualizando las cajas delimitadoras predichas por el modelo en tiempo real.

## Directorios Clave

- **datasets/**: Directorio que debe contener las imagenes crudas y el archivo `_annotations.coco.json`.
- **logs/**: Carpeta donde YOLO almacena automaticamente los pesos entrenados y las metricas de evaluacion. Se ignora en el control de versiones.
- **dataset_yolo_grayscale/**: Directorio de trabajo temporal generado por `dataset.py` con las imagenes y etiquetas en la estructura estricta que exige YOLO.
- **weights/**: Directorio donde se puede colocar el mejor modelo (`best.pt`) final para que el sistema principal (`src/main.py`) lo consuma en produccion.
