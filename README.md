# AIVA_2026: Sistema de Inspección de Soldadura por Visión Artificial

Este proyecto implementa un sistema de visión artificial diseñado para dotar de percepción autónoma a un brazo robótico en la detección de defectos en circuitos impresos (PCB). El software identifica con precisión interrupciones de continuidad y la ausencia de puntos de soldadura en entornos de producción. Para garantizar un rendimiento óptimo en la Raspberry Pi del actuador, la lógica de visión, desarrollada originalmente en Python, se encapsula en una biblioteca nativa en C, facilitando su integración directa en el flujo de control del robot.

## Modos de Ejecución para Simulación del Sistema

El sistema cuenta con tres modos de ejecución diseñados para cubrir desde la captura unitaria hasta pruebas de estrés exhaustivas. Puedes seleccionarlos al ejecutar `src/main.py` utilizando el parámetro `--mode`:

1. **Modo Single (`--mode single`)**:
   Captura y procesa una imagen específica si se le pasa el argumento `--image <ruta>`.

2. **Modo Simulación (`--mode simulate`)**:
   Procesa un lote completo de imágenes almacenadas en `data/simulate/`.
   - Si no se especifica cadencia, se ejecuta a máxima velocidad para calcular los FPS reales del motor YOLO, generando un reporte de rendimiento en `reports/simulate/`.
   - Si se especifica el argumento `--sim_time <segundos>`, espera el tiempo exacto indicado entre imagen e imagen, emulando la velocidad de la cadena de soldaduras.

3. **Prueba de Estrés 24H (`--mode simulate_24h`)**:
   Diseñado para pruebas de robustez infinitas sin necesidad de hardware físico real.
   - Itera de forma cíclica sobre el dataset, aplicando *data augmentation* aleatorio (rotaciones, volteos) en memoria para asegurar una entrada variable y continua.
   - Simula los tiempos de llegada de las placas usando una distribución Gaussiana alrededor de la media definida por `--sim_time` (por defecto 5s).
   - Registra métricas de rendimiento y genera automáticamente un informe estadístico detallado (`Max/Min/Avg Processing Time`) en la carpeta `reports/stress_tests/` cuando el operador aborta la simulación (`Ctrl+C`).

## Integración Programática (API)
El motor de visión está diseñado para integrarse fácilmente en el código Python de la cadena de soldadura del robot de inspección. Solo se necesita instanciar la clase `SolderDefectDetector` una vez (para cargar el modelo en memoria y la interfaz de cámara) y procesar las imágenes sobre la marcha:

```python
from src.solder_defect_detector import SolderDefectDetector

# Inicializa la cámara y carga el modelo en memoria
detector = SolderDefectDetector()

# Dentro del bucle del robot, cuando la placa está en la posición calibrada para el robot y toma la imagen, se ejecuta:
resultado = detector.process_from_path("data/simulate/Muestra_017.jpg")

print(f"Detectados {resultado['detection_count']} defectos en {resultado['processing_time_ms']:.2f} ms")
print(f"Reporte XML generado en: {resultado['xml_path']}")
```

## Objetivo

* **Detección Automática:** Identificar fallos de soldadura definidos como líneas que deberían estar unidas pero carecen de soldadura.
* **Optimización de Costes:** Evitar falsos negativos para evitar circuitos inservibles.
* **Integración en Tiempo Real:** Procesar cada placa en un tiempo máximo de 10 segundos para no interrumpir el flujo de funcionamiento de 24 horas del robot.
* **Sistema Semi-supervisado:** Proporcionar un índice de confianza junto a las coordenadas. Si la confianza es baja, el sistema permitirá una revisión manual para decidir la acción del robot.
* **Salida de Datos:** Devolver las coordenadas de la ubicación, ancho y alto (bounding box mínimo) de las partes a soldar y generar un archivo XML con la información.

## Tecnologías Utilizadas

* **Algoritmos de Visión:** Python.
* **Lenguaje de Inferencia:** C.
* **Hardware de Control:** Raspberry Pi 5.
* **Captura de Imagen:** Cámara del robot con iluminación LED integrada.
* **Formato de Imagen:** JPG.

## Especificaciones de la Arquitectura del Sistema

La arquitectura separa las responsabilidades de captura de hardware, representación de datos y lógica de inferencia.

* **Captura de hardware:** Interfaces unificadas para interactuar con los sensores (Raspberry Pi 5 Camera).

* **Representación de datos:** Estructuras optimizadas que implementan evaluación perezosa para almacenar datos crudos y consolidar resultados.

* **Lógica de inferencia:** Aislamiento estricto del modelo predictivo para facilitar su actualización sin alterar el flujo principal.

A continuación se muestra el diagrama UML:

![UML_Diagram](https://github.com/felixmaral/AIVA_2026_Solder_Defect_Detector/blob/docs/fm/%231-readme-introductorio/media/SolderDefect%20Detection-2026-03-13-115107.svg)

## Descripción de Clases

### 1. Clases de Datos

#### `SolderDefect`

Representa la unidad atómica de una detección realizada por el modelo de visión.

* **Responsabilidad:** Almacenar las coordenadas espaciales (bounding box) y el nivel de certeza de una anomalía específica en la placa.

* **Atributos:** Coordenadas de la esquina superior izquierda (`top_left_x`, `top_left_y`), dimensiones de la caja (`width`, `height`) y la probabilidad asignada por el modelo (`confidence`).

* **Método clave:** `to_xml_string()` para auto-serializarse en un fragmento XML.

#### `PCBImage`

Actúa como contenedor inteligente para los datos crudos de la imagen.

* **Responsabilidad:** Encapsular el array de bytes de la imagen capturada y proporcionar acceso controlado a sus propiedades físicas. Implementa evaluación perezosa (lazy evaluation) para evitar costes computacionales de decodificación hasta que sea estrictamente necesario.

* **Atributos:** Buffer de bytes (`_image_data`), ruta opcional (`_filepath`) y metadatos cacheados (`_height`, `_width`).

* **Métodos clave:** `_calculate_dimensions()` (método interno de decodificación), `get_resolution()`, `get_size_bytes()`.

#### `DetectionResult`

Estructura de agregación que consolida el resultado completo de una inferencia.

* **Responsabilidad:** Agrupar múltiples instancias de `SolderDefect` asociadas a una única `PCBImage` y gestionar la exportación final de los datos.

* **Atributos:** Una lista de objetos `SolderDefect`.

* **Métodos clave:** `add_defect()` para poblar la lista durante el ciclo de predicción, y `to_xml()` para generar el reporte final formateado.

### 2. Clases de Interfaz y Procesamiento

#### `Camera`

Abstracción de la capa de hardware físico (Raspberry Pi Camera Module 3 / HQ).

* **Responsabilidad:** Proveer métodos unificados para la obtención de frames, independientemente de si provienen del flujo de video en vivo o de archivos locales para depuración.

* **Métodos clave:** `get_real_time_image()` (interactúa con la cámara real) y `get_image_from_file()`. Ambos métodos instancian y retornan objetos `PCBImage`.

#### `Detector`

Motor principal de inferencia.

* **Responsabilidad:** Ejecutar el modelo predictivo sobre una imagen dada y traducir las salidas del tensor en estructuras de datos manejables.

* **Método clave:** `detect(image: PCBImage)`.

## Flujo de Ejecución (Inferencia)

1. **Captura:** El orquestador principal (`main.py`) invoca a la instancia de `Camera` mediante `get_real_time_image()`. La cámara captura el frame y lo encapsula retornando un objeto `PCBImage`.

2. **Análisis:** El orquestador pasa este objeto `PCBImage` al método `detect()` de la instancia `Detector`.

3. **Procesamiento Interno:**

   * El `Detector` inicializa un objeto `DetectionResult` vacío.

   * El modelo decodifica la `PCBImage` y realiza la inferencia matricial.

   * Por cada anomalía localizada, el `Detector` crea un objeto `SolderDefect` y lo inserta en `DetectionResult` mediante `add_defect()`.

4. **Retorno:** Finalizada la inferencia, `detective()` retorna el objeto `DetectionResult` consolidado al orquestador.

5. **Exportación:** El orquestador invoca `to_xml()` sobre el `DetectionResult` para obtener el string final del reporte, listo para ser registrado en log o transmitido por red.

## Evaluación del Sistema

El desarrollo se apoya en un dataset inicial de 116 imágenes de ejemplo. Se realizarán pruebas unitarias sobre el núcleo del algoritmo para validar:

1. La correcta detección de los fallos de soldadura.
2. La precisión de las coordenadas devueltas.
3. El cumplimiento de los tiempos de ejecución (<10s).
4. La estimación del umbral de confianza minimizando la tasa de Falsos Negativos (Fallos de Soldadura no detectados)

## Contribución y Flujo de Trabajo

Este repositorio se utiliza para gestionar las tareas del proyecto con fecha límite del 1 de mayo. 
* **Gestión de Tareas:** Todas las funcionalidades se registran como **issues** en GitHub, indicando el tiempo previsto de desarrollo.
* **Control de Versiones:** Se trabaja con ramas independientes para cada funcionalidad o corrección.
* **Trazabilidad:** Cada commit debe ir acompañado del número de la issue a la que se imputa el trabajo para mantener un historial claro para el supervisor.

## Convenciones de Control de Versiones

Para garantizar la trazabilidad y el orden en el desarrollo del sistema de inspección, el equipo debe adherirse a las siguientes normas para la creación de ramas y mensajes de commit.

### 1. Nomenclatura de Ramas

Toda nueva rama creada en el repositorio debe identificar claramente su propósito, el desarrollador asignado y el ticket asociado.

**Estructura:**
`tipo/iniciales/numero_issue-descripcion_corta`

**Definición de Prefijos (tipo):**
* **feat**: Nueva funcionalidad (ej. algoritmo de visión en C, preprocesamiento de imágenes).
* **fix**: Corrección de errores o fallos en el código existente.
* **test**: Creación, actualización o modificación de pruebas unitarias.
* **docs**: Modificaciones exclusivas en el README o en la carpeta de documentación (`docs/`).
* **refactor**: Reestructuración del código que no altera su comportamiento externo ni añade funcionalidades.

**Ejemplos de uso:**
* `feat/ag/#1-preprocesamiento-jpg` (El desarrollador "AG" trabaja en la funcionalidad descrita en el Issue #1).
* `fix/cm/#2-error-memoria-detectar` (El desarrollador "CM" soluciona un fallo de memoria documentado en el Issue #2).

### 2. Nomenclatura de Commits

El historial del repositorio debe mantenerse limpio y estandarizado. Los mensajes de commit se basarán en la convención de *Conventional Commits* para asegurar la vinculación automática con los issues de GitHub.

**Estructura:**
`tipo(#numero_issue): descripción en imperativo`

**Reglas de aplicación:**
* El `tipo` debe coincidir con los prefijos definidos en la nomenclatura de ramas.
* La descripción debe redactarse en modo imperativo (ej. "añadir", "corregir", "implementar", no "añadido" ni "añadiendo").

**Ejemplos de uso:**
* `feat(#1): implementar filtro gaussiano para limpieza de ruido`
* `fix(#2): liberar puntero de memoria en metodo detectivesco`

## Licencia

Este software está protegido por derechos de autor (copyright). Todos los derechos están reservados a JLVision. sQueda estrictamente prohibida la reproducción, distribución o modificación del software sin el consentimiento expreso y por escrito de los titulares de los derechos.

## Contacto

Para consultas sobre el desarrollo o reporte de incidencias, utilizar el sistema de **GitHub Issues** de este repositorio.