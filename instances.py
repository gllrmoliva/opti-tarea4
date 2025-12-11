import pandas as pd
import os

CARPETAS = {
    'pequeñas': (20, 49),
    'medianas': (50, 79),
    'grandes': (80, 100)
}
DATASET = 'dataset.csv' 

def procesar_instancias(archivo_entrada):

    # Crear las carpetas si no existen
    for carpeta in CARPETAS.keys():
        os.makedirs(carpeta, exist_ok=True)
        print(f"Directorio verificado/creado: {carpeta}")

    print(f"\nLeyendo archivo: {archivo_entrada}...")
    
    try:
        df = pd.read_csv(archivo_entrada)
    except FileNotFoundError:
        print("Error: No se encontró el archivo de entrada. Verifica el nombre.")
        return

    contadores = {'pequeñas': 0, 'medianas': 0, 'grandes': 0, 'ignoradas': 0}

    # Iterar sobre cada fila del DataFrame
    for index, row in df.iterrows():
        num_nodos = row['num_cities']
        instance_id = row['instance_id']
        
        carpeta_destino = None

        # Clasificar según el número de nodos
        if CARPETAS['pequeñas'][0] <= num_nodos <= CARPETAS['pequeñas'][1]:
            carpeta_destino = 'pequeñas'
        elif CARPETAS['medianas'][0] <= num_nodos <= CARPETAS['medianas'][1]:
            carpeta_destino = 'medianas'
        elif CARPETAS['grandes'][0] <= num_nodos <= CARPETAS['grandes'][1]:
            carpeta_destino = 'grandes'
        
        if carpeta_destino:
            # Crear nombre de archivo, ej: instance_0.csv
            nombre_archivo = f"instance_{instance_id}.csv"
            ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
            
            # Guardar esa fila específica como un nuevo CSV (manteniendo el header)
            # df.iloc[[index]] selecciona la fila como un DataFrame
            df.iloc[[index]].to_csv(ruta_completa, index=False)
            contadores[carpeta_destino] += 1
        else:
            # Instancias que caen fuera de los rangos (ej: 55 nodos, 150 nodos, etc.)
            contadores['ignoradas'] += 1

    # Resumen final
    print("\n--- Proceso Terminado ---")
    print(f"Instancias guardadas en 'pequeñas' (17-50): {contadores['pequeñas']}")
    print(f"Instancias guardadas en 'medianas' (60-120): {contadores['medianas']}")
    print(f"Instancias guardadas en 'grandes' (200-400): {contadores['grandes']}")
    print(f"Instancias ignoradas (fuera de rango): {contadores['ignoradas']}")

# --- Ejecución ---
procesar_instancias(DATASET)