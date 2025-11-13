import sys
from pathlib import Path

# CONFIGURACIÓN

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from src.ocr_hocr_table.hocr_to_csv import mi_funcion_ocr

# DEFINICIÓN DE RUTAS 
DATA_DIR = ROOT_DIR / 'data'
HOCR_DIR = DATA_DIR / 'hOCR' 
OUTPUT_DIR = DATA_DIR / 'outputs'

def run_processing():
    """
    Script principal que busca archivos HOCR y los procesa.
    """
    print("Iniciando procesamiento de HOCR...")
    

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hocr_files = list(HOCR_DIR.glob('*.hocr'))
    
    if not hocr_files:
        print(f"Error: No se encontraron archivos .hocr en {HOCR_DIR}")
        return

    print(f"Se encontraron {len(hocr_files)} archivos para procesar.")

    # Iterar y procesar cada archivo
    for hocr_file_path in hocr_files:

        file_stem = hocr_file_path.stem  # "1C_5"
        base_name = file_stem.split('_')[0] # "1C"
        
        output_csv_name = f"{base_name}.csv"
        output_csv_path = OUTPUT_DIR / output_csv_name
        

        try:

            mi_funcion_ocr(
                hocr_path=hocr_file_path,
                output_csv_path=output_csv_path,
                eps_y=10, # Tolerancia vertical (para filas)
                eps_x=30  # Tolerancia horizontal (para columnas/jerarquía)
            )
        except Exception as e:
            print(f"--- ERROR procesando {hocr_file_path.name}: {e} ---")

    print("\nProceso completado.")

if __name__ == "__main__":
    run_processing()