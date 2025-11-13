# HOCR Table Reconstruction
---

Este proyecto consiste en reconstruir estructuras de tablas a partir de archivos HOCR (HTML-based OCR output). El script principal utiliza lógica de clustering de IA para analizar la geometría (`x`, `y`) de las líneas de texto detectadas por el OCR y volver a ensamblarlas en una cuadrícula CSV bidimensional.

## **Dependencias:**


Las bibliotecas principales necesarias se enumeran en `requirements.txt`.

  * **pandas:** Para la manipulación de datos y la exportación final a CSV.
  * **beautifulsoup4:** Para un parseo eficiente del archivo HOCR.
  * **scikit-learn:** Para el algoritmo de clustering DBSCAN, que es el núcleo de la lógica de reconstrucción.


## **Motivacion**

El desafío consiste en procesar los resultados de un motor de OCR, proporcionados en formato `.hocr`.

Los documentos de entrada son Balances Financieros con diferentes diseños, y el archivo `.hocr` proporciona el texto crudo y las coordenadas de cada palabra y línea. La motivación principal no es realizar el OCR, sino reconstruir la estructura de la tabla original (incluyendo sus jerarquías y tabulaciones) a partir de esta información geométrica proporcionada en los archivos `.hocr`.

##  **Descripcion de los archivos**

El repositorio está estructurado para separar la lógica del script, los datos de entrada y los resultados.

  * **`main.py`**: Se encarga de encontrar todos los archivos `.hocr` en el directorio de datos, llamar a la función de procesamiento para cada uno y guardar los resultados en la carpeta de `outputs`.
  * **`src/ocr_hocr_table/hocr_to_csv.py`**: Contiene toda la lógica central del proyecto.
      * `parse_hocr_to_df()`: Una función auxiliar que lee el archivo `.hocr` usando BeautifulSoup y extrae la información de las etiquetas `ocr_line`.
      * `mi_funcion_ocr()`: La función principal requerida por la prueba. Toma las rutas de entrada/salida y los hiperparámetros de clustering, y ejecuta todo el proceso de IA para reconstruir la tabla.
  * **`data/hOCR/`**: Contiene los archivos `.hocr` de entrada que se van a procesar.
  * **`data/pdf/`**: Contiene los archivos PDF originales, que se proporcionan únicamente como referencia visual. El script no los utiliza.
  * **`data/outputs/`**: Contiene los archivos `.csv` finales reconstruidos.
  * **`requirements.txt`**: El archivo de dependencias del proyecto.



## Cómo Ejecutar el Proyecto
 
Para procesar todos los archivos `.hocr` ubicados en `data/hOCR/` y generar los CSV en `data/outputs/`:

1.  Se debe tener un entorno virtual activado y las dependencias instaladas.
2.  Desde la raíz del proyecto, simplemente ejecuta:
    ```bash
    python main.py
    ```
3.  El script imprimirá el progreso en la consola y los archivos `.csv` aparecerán en `data/outputs/`.

### Detalles Técnicos y Metodología

El desafío principal era que los documentos tenían diferentes alineaciones y jerarquías (tabulaciones). El enfoque de la solución evolucionó para resolver esto:

1.  **Intento Fallido (Qué no funcionó):** Leer las etiquetas `ocrx_word` (palabras individuales). Esto destruía la cohesión de los conceptos. Por ejemplo, "Efectivo y equivalentes de efectivo" se convertía en 5 tokens separados, lo que hacía imposible la reconstrucción.

2.  **Primera Mejora (Qué funcionó):** Cambiar el parseo para leer solo las etiquetas `ocr_line` (líneas lógicas). Esto nos dio tokens cohesivos como `"Efectivo y equivalentes de efectivo"`, lo cual fue el primer gran avance.

3.  **Segundo Intento Fallido:** Se intentó agrupar las columnas usando el centro horizontal (`x_center`) de cada `ocr_line`. Esto falló porque las líneas en la misma columna, pero con diferentes longitudes de texto, tienen centros diferentes. El resultado fue un CSV con los datos de una misma columna esparcidos en "escalera".

4.  **Solución Final (El Método Exitoso):** La solución final es un proceso de clustering de `DBSCAN` en dos pasos:

      * **Paso 1 (Filas):** Se aplica `DBSCAN` sobre la coordenada `y_center` de todas las `ocr_line`. Esto agrupa todas las líneas que están en la misma fila horizontal, usando un `eps_y` (tolerancia vertical) pequeño.
      * **Paso 2 (Columnas):** Se aplica `DBSCAN` sobre la coordenada `x0` (la posición *inicial* horizontal) de todas las `ocr_line`. Este fue el descubrimiento clave:
          * Al agrupar por `x0` (inicio), todos los conceptos con la misma tabulación (ej. `x0=353`) se agrupan en una columna, mientras que sus encabezados (ej. `x0=306`) se agrupan en una columna separada.
          * El hiperparámetro `eps_x` (tolerancia horizontal) es el más crítico. Un valor pequeño (ej. 30) es muy estricto y captura las diferentes tabulaciones, creando más columnas que preservan la jerarquía del documento.

**Resultados:** El script produce un "CSV geométrico" que representa fielmente la cuadrícula 2D del documento original, incluyendo las columnas vacías creadas por la sangría. Este resultado es la base para un post-procesamiento semántico.