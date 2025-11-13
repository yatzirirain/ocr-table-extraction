import pandas as pd
from bs4 import BeautifulSoup
from sklearn.cluster import DBSCAN
from pathlib import Path

# FUNCIÓN DE PARSEO------------------------------------------------------

def parse_hocr_to_df(hocr_path: Path) -> pd.DataFrame:
    """
    Parsea un archivo HOCR y extrae los elementos 'ocr_line'.

    :param hocr_path: La ruta al archivo .hocr de entrada.
    :type hocr_path: pathlib.Path
    :return: DataFrame donde cada fila es una 'ocr_line'.
             Incluye columnas: ['text', 'x0', 'y0', 'x1', 'y1',
             'y_center', 'x_center'].
             Retorna un DataFrame vacío si no se encuentran líneas.
    :rtype: pd.DataFrame
    """
    with open(hocr_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    tokens = []
    
    # Buscar todos los elementos 'ocr_line', que representan líneas de texto completas.
    lines = soup.find_all('span', class_='ocr_line') 
    
    for line in lines:
        title = line.get('title', '')
        
        # Obtener el texto completo de la línea, eliminando espacios en blanco.
        text = line.get_text().strip()
        if not text: # Omitir líneas que están vacías.
            continue
            
        try:
            # Extraer las coordenadas del Bounding Box (bbox) del 'title'
            bbox_str = title.split(';')[0].split('bbox ')[1]
            x0, y0, x1, y1 = [int(p) for p in bbox_str.split()]
            
            # Almacenar el token con sus coordenadas y centros calculados.
            tokens.append({
                'text': text, # Texto completo de la línea
                'x0': x0,
                'y0': y0,
                'x1': x1,
                'y1': y1,
                'y_center': (y0 + y1) / 2, # Centro vertical para clustering de filas
                'x_center': (x0 + x1) / 2  # Centro horizontal (informativo)
            })
        except Exception:
            # Omitir cualquier línea que no tenga un formato de 'bbox' válido.
            continue 

    # Devolver DF vacío si no se parseó nada
    if not tokens:
        return pd.DataFrame() 
        
    # Devolver el DataFrame ordenado por posición vertical.
    return pd.DataFrame(tokens).sort_values(by='y_center')



# FUNCIÓN DE PROCESAMIENTO---------------------------------------------------

def mi_funcion_ocr(hocr_path: Path, output_csv_path: Path, eps_y: int = 10, eps_x: int = 30):
    """
    Reconstruye una cuadrícula CSV a partir de un HOCR usando clustering DBSCAN.

    El proceso aplica clustering en dos ejes para crear la cuadrícula:
    1.  Clustering Vertical (Filas): Agrupa líneas ('ocr_line') en filas
        basándose en su 'y_center' (centro vertical).
    2.  Clustering Horizontal (Columnas): Agrupa líneas en columnas
        basándose en su 'x0' (posición inicial horizontal).

    :param hocr_path: Ruta al archivo .hocr de entrada.
    :type hocr_path: pathlib.Path
    :param output_csv_path: Ruta donde se guardará el .csv de salida.
    :type output_csv_path: pathlib.Path
    :param eps_y: Hiperparámetro 'epsilon' de DBSCAN para el eje Y.
                  Define la distancia vertical máxima para que dos
                  líneas se consideren de la misma fila.
    :type eps_y: int
    :param eps_x: Hiperparámetro 'epsilon' de DBSCAN para el eje X.
                  Define la distancia horizontal máxima (basada en 'x0')
                  para que dos líneas se consideren de la misma columna.

    :type eps_x: int
    """
    
    
    # Conversion del archivo HOCR a un DataFrame de 'ocr_line' tokens.
    print(f"Parseando {hocr_path.name}...")
    df = parse_hocr_to_df(hocr_path)
    if df.empty:
        print(f"No se encontraron líneas en {hocr_path.name}.")
        return

    # Clustering Vertical (Filas)

    dbscan_y = DBSCAN(eps=eps_y, min_samples=1)
    df['row_id'] = dbscan_y.fit_predict(df[['y_center']])

    # Clustering Horizontal (Columnas)
    df = df.sort_values(by='x0') 
    
    # Inicializa DBSCAN para el eje X con el 'epsilon' (tolerancia) proveído.
    dbscan_x = DBSCAN(eps=eps_x, min_samples=1)
    
    # Asigna un 'col_id' a cada línea basándose en su 'x0'.
    df['col_id'] = dbscan_x.fit_predict(df[['x0']])

    # --- Paso 4: Reconstrucción de la Cuadrícula ---
    print("Reconstruyendo tabla...")
    
    # Ordenar por fila, columna y 'x0'
    df = df.sort_values(by=['row_id', 'col_id', 'y0', 'x0'])
    
    # Agrupa por cada celda única (row_id, col_id) y une el texto.
    cell_groups = df.groupby(['row_id', 'col_id'])['text'].apply(' '.join)
    
    # Pivota los 'col_id' a columnas de DataFrame, creando la cuadrícula 2D.
    grid_df = cell_groups.unstack(level='col_id')
    
    # Limpia los nombres de los ejes para un CSV más limpio.
    grid_df = grid_df.rename_axis(None, axis=1).rename_axis(None, axis=0)
    
    # Guardar el Resultado en un CSV.
    grid_df.to_csv(output_csv_path, index=False, header=True, encoding='utf-8-sig')
    print(f"Tabla guardada en {output_csv_path}")