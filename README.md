# AIVA_2026: Sistema de Inspección de Soldadura por Visión Artificial

Este proyecto implementa un sistema de visión artificial diseñado para dotar de percepción autónoma a un brazo robótico en la detección de defectos en circuitos impresos (PCB). El software identifica con precisión interrupciones de continuidad y la ausencia de puntos de soldadura en entornos de producción. Para garantizar un rendimiento óptimo en la Raspberry Pi del actuador, la lógica de visión, desarrollada originalmente en Python, se encapsula en una biblioteca nativa en C, facilitando su integración directa en el flujo de control del robot.

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

## Especificaciones de la Interfaz (C)

El sistema se diseñará para ser invocado desde el software del robot (escrito en C) mediante la siguiente firma de función:

`int* detectar(char *filename, char *xml_file)`

Esta función procesará la imagen capturada y devolverá un puntero con las coordenadas y dimensiones de los defectos encontrados, además de generar el reporte en formato XML.

## Pruebas del Sistema

El desarrollo se apoya en un dataset inicial de 116 imágenes de ejemplo. Se realizarán pruebas unitarias sobre el núcleo del algoritmo para validar:
1. La correcta detección de los fallos de soldadura.
2. La precisión de las coordenadas devueltas.
3. El cumplimiento de los tiempos de ejecución (<10s).
4. La minimización de FN

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

Este software está protegido por derechos de autor (copyright). Todos los derechos están reservados a VisioTech AI. Queda estrictamente prohibida la reproducción, distribución o modificación del software sin el consentimiento expreso y por escrito de los titulares de los derechos.

## Contacto

Para consultas sobre el desarrollo o reporte de incidencias, utilizar el sistema de **GitHub Issues** de este repositorio.