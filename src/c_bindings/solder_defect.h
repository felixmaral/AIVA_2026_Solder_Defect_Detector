#ifndef SOLDER_DEFECT_H
#define SOLDER_DEFECT_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ApplicationHandle ApplicationHandle;

typedef struct {
    char xml_path[512];
    double processing_time_ms;
    int detection_count;
    int success; // 1 si fue exitoso, 0 si falló
} DetectionResultInfo;

/**
 * Inicializa el intérprete de Python, añade el directorio raíz al path
 * y crea una instancia de la clase Application.
 *
 * @param camera_index Índice de la cámara física.
 * @param output_dir Directorio donde guardar los XML (puede ser NULL para usar el default).
 * @param visualize Si es 1, activa la interfaz gráfica (cv2). 0 la desactiva.
 * @return Un puntero opaco a la instancia de Python, o NULL si hubo un error.
 */
ApplicationHandle* application_create(int camera_index, const char* output_dir, int visualize);

/**
 * Procesa una imagen física guardada en el disco.
 * 
 * @param app Puntero devuelto por application_create.
 * @param image_path Ruta a la imagen (ej: "data/simulate/Muestra_017.jpg").
 * @return Una estructura DetectionResultInfo con los resultados de la inferencia.
 */
DetectionResultInfo application_process_from_path(ApplicationHandle* app, const char* image_path);

/**
 * Captura una imagen directamente de la cámara y la procesa.
 * 
 * @param app Puntero devuelto por application_create.
 * @return Una estructura DetectionResultInfo con los resultados de la inferencia.
 */
DetectionResultInfo application_process_live_camera(ApplicationHandle* app);

/**
 * Libera la instancia de Application y cierra el intérprete de Python.
 * 
 * @param app Puntero devuelto por application_create.
 */
void application_destroy(ApplicationHandle* app);

#ifdef __cplusplus
}
#endif

#endif // SOLDER_DEFECT_H
