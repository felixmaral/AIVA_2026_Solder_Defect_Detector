# AIVA_2026: Sistema de Inspección de Soldadura por Visión Artificial

Este proyecto implementa un sistema de visión artificial diseñado para dotar de percepción autónoma a un brazo robótico en la detección de defectos en circuitos impresos (PCB). El software identifica con precisión interrupciones de continuidad y la ausencia de puntos de soldadura en entornos de producción. Para garantizar un rendimiento óptimo en la Raspberry Pi del actuador, la lógica de visión, desarrollada originalmente en Python, se encapsula en una biblioteca nativa en C, facilitando su integración directa en el flujo de control del robot.

---

## Instalación

Para configurar el entorno virtual e instalar todas las dependencias automáticamente en la Raspberry Pi, ejecuta:

```bash
source install.sh
```

El script crea el entorno `.venv`, instala PyTorch (CPU), OpenCV y Ultralytics sin dependencias redundantes, y activa el entorno listo para usar.

> Para entornos de desarrollo o CI, instala las dependencias de producción con:
> ```bash
> pip install -r requirements_prod.txt
> ```

---

## Integración Programática (API)

El motor de visión está diseñado para integrarse sin fricción en el software de control del brazo robótico, soportando tanto entornos Python nativos como sistemas industriales en C/C++.

### Integración en C / C++ (Recomendado para Controladores)

Para utilizar la API en C, se ha creado un *wrapper* nativo que encapsula toda la complejidad de Python. Solo necesitas incluir la cabecera y llamar a las funciones:

```c
#include "src/c_bindings/solder_defect.h"

int main() {
    // 1. Inicializa la cámara y el modelo (cámara 0, salida por defecto, sin GUI)
    ApplicationHandle* app = application_create(0, NULL, 0);

    // 2. Procesa la placa en la posición de inspección
    DetectionResultInfo result = application_process_from_path(app, "data/simulate/Muestra_017.jpg");

    // 3. Toma la decisión del robot
    if (result.success && result.detection_count > 0) {
        printf("Placa defectuosa — enviando a soldadura\n");
    } else {
        printf("Placa correcta — avanzando a la siguiente etapa\n");
    }

    // 4. Libera recursos al apagar la máquina
    application_destroy(app);
    return 0;
}
```

> Para compilar la librería `.so`, entra a `src/c_bindings/` y ejecuta `make`.

### Integración en Python

Si el orquestador del robot corre directamente en Python, puedes instanciar la clase `Application` directamente:

```python
from src.application import Application

# Inicializa la cámara y carga el modelo en memoria (una sola vez)
detector = Application()

# Dentro del bucle del robot, evalúa cada placa:
resultado = detector.process_from_path("data/simulate/Muestra_017.jpg")

print(f"Detectados {resultado['detection_count']} defectos en {resultado['processing_time_ms']:.2f} ms")
print(f"Reporte XML generado en: {resultado['xml_path']}")
```

---

## Modos de Simulación

El sistema cuenta con dos modos de ejecución accesibles desde `src/main.py` mediante el parámetro `--mode`, diseñados para cubrir desde inspecciones unitarias hasta pruebas de rendimiento continuas.

### Modo Single (`--mode single`)

Captura y procesa una imagen concreta. Si se omite `--image`, captura un frame de la cámara física.

```bash
python -m src.main --mode single --image data/simulate/Muestra_017.jpg
```

### Modo Simulación (`--mode simulate`)

Procesa cíclicamente las imágenes de `data/simulate/`, aplicando *data augmentation* aleatorio (rotaciones, volteos) en memoria para simular la variabilidad real de la línea de producción.

```bash
# Máxima velocidad — mide los FPS reales del motor YOLO
python -m src.main --mode simulate

# Cadencia Gaussiana — emula la velocidad real de la cadena (media 5s ± 2s)
python -m src.main --mode simulate --mean 5.0 --deviation 2.0

# Simulación acotada en tiempo — para pruebas en CI o validaciones rápidas
python -m src.main --mode simulate --sim_time 60

# Con visualización en pantalla
python -m src.main --mode simulate --visualize
```

Al terminar (por tiempo agotado o `Ctrl+C`), se genera automáticamente un informe de rendimiento (`Max/Min/Avg Processing Time`, FPS) en `reports/simulate/`.

---

## Arquitectura del Sistema

La arquitectura separa estrictamente las responsabilidades de captura de hardware, representación de datos y lógica de inferencia.

- **Captura de hardware:** Interfaces unificadas para interactuar con los sensores (Raspberry Pi 5 Camera).
- **Representación de datos:** Estructuras optimizadas con evaluación perezosa para almacenar datos crudos y consolidar resultados.
- **Lógica de inferencia:** Aislamiento estricto del modelo predictivo para facilitar su actualización sin alterar el flujo principal.

A continuación se muestra el diagrama UML:

![UML_Diagram](https://github.com/felixmaral/AIVA_2026_Solder_Defect_Detector/blob/docs/fm/%231-readme-introductorio/media/SolderDefect%20Detection-2026-03-13-115107.svg)

### Descripción de Clases

#### 1. Clases de Datos

**`PCBImage`**
Contenedor inteligente para los datos crudos de la imagen. Implementa evaluación perezosa (*lazy evaluation*): el buffer de bytes solo se decodifica cuando se accede a sus propiedades físicas (`width`, `height`). Métodos clave: `get_resolution()`, `get_size_bytes()`.

**`SolderDefect`**
Unidad atómica de una detección. Almacena las coordenadas del *bounding box* (`top_left_x`, `top_left_y`, `width`, `height`) y la confianza del modelo. Se auto-serializa mediante `to_xml_string()`.

**`DetectionResult`**
Estructura de agregación que consolida todas las detecciones de una inspección. Método clave: `to_xml()` para generar el reporte XML completo.

#### 2. Clases de Interfaz y Procesamiento

**`Camera`**
Abstracción de la capa de hardware (Raspberry Pi Camera Module 3 / HQ). Proporciona `get_real_time_image()` para captura en vivo y `get_image_from_file()` para depuración desde disco. Ambos devuelven objetos `PCBImage`.

**`Detector`**
Motor de inferencia YOLO. Ejecuta el modelo predictivo sobre un `PCBImage` y traduce las salidas del tensor en objetos `SolderDefect`. Método clave: `detect(image: PCBImage) → DetectionResult`.

#### 3. Clase Orquestadora

**`Application`** (`src/application.py`)
Fachada principal y único punto de entrada para cualquier sistema externo (Python o C). Coordina el ciclo completo: inicializar `Camera` y `Detector`, procesar la imagen, generar el XML y mostrar resultados opcionalmente.

| Método | Descripción |
|---|---|
| `process_from_path(image_path)` | Procesa una imagen desde disco |
| `process_live_camera()` | Captura un frame de la cámara física y lo procesa |
| `process_pcb_image(pcb_image)` | Procesa un `PCBImage` ya cargado (útil para pipelines personalizados) |
| `wait(delay_s)` | Pausa entre placas manteniendo la ventana de visualización activa |

Retorna siempre un diccionario con `xml_path`, `detection_count` y `processing_time_ms`.

### Flujo de Ejecución

```
Camera.get_real_time_image()
    └─► PCBImage (bytes crudos)
            └─► Detector.detect(pcb_image)
                    └─► DetectionResult
                            ├─► SolderDefect × N
                            └─► to_xml() → reporte XML
```

---

## Objetivo

- **Detección automática:** Identificar fallos de soldadura (interrupciones de continuidad, ausencia de puntos de soldadura).
- **Optimización de costes:** Minimizar falsos negativos para evitar circuitos inservibles en producción.
- **Integración en tiempo real:** Procesar cada placa en menos de 10 segundos para no interrumpir el flujo del robot.
- **Sistema semi-supervisado:** Proporcionar un índice de confianza junto a las coordenadas; si es bajo, el sistema permite revisión manual.
- **Salida de datos:** Generar un archivo XML con el *bounding box* de cada defecto detectado.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Algoritmos de visión | Python + Ultralytics YOLO |
| Binding de control | C (librería compartida `.so`) |
| Hardware de control | Raspberry Pi 5 |
| Captura de imagen | Cámara CSI con iluminación LED integrada |
| Formato de imagen | JPEG |

---

## Convenciones de Control de Versiones

### Nomenclatura de Ramas

`tipo/iniciales/numero_issue-descripcion_corta`

| Prefijo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de errores |
| `test` | Tests unitarios |
| `docs` | Documentación |
| `refactor` | Reestructuración sin cambio de comportamiento |

**Ejemplos:** `feat/ag/#1-preprocesamiento-jpg` · `fix/cm/#2-error-memoria-detectar`

### Nomenclatura de Commits

`tipo(#numero_issue): descripción en imperativo`

**Ejemplos:** `feat(#1): implementar filtro gaussiano para limpieza de ruido` · `fix(#2): liberar puntero de memoria en método detect`

---

## Licencia

Este software está protegido por derechos de autor (copyright). Todos los derechos están reservados a JLVision. Queda estrictamente prohibida la reproducción, distribución o modificación del software sin el consentimiento expreso y por escrito de los titulares de los derechos.

## Contacto

Para consultas sobre el desarrollo o reporte de incidencias, utilizar el sistema de **GitHub Issues** de este repositorio.