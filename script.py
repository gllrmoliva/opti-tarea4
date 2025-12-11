import pandas as pd
import os
import csv
import ast
from datetime import datetime

from mtz_gurobi import solve_mtz_gurobi
from mtz_cplex import solve_mtz_cplex

# ==========================================
# 1. CONFIGURACIÓN GLOBAL (IDs de Instancias)
# ==========================================
# Selecciona los IDs que quieres correr (deben existir en las carpetas)
# PEQUEÑAS_IDS = [20, 11, 1, 9]
# MEDIANAS_IDS = [0, 7, 8]
# GRANDES_IDS = [3, 4, 2]
PEQUEÑAS_IDS = [20, 11]
MEDIANAS_IDS = []
GRANDES_IDS = []

TIEMPO_LIMITE_SEC = 3600
ARCHIVO_RESULTADOS = "resultados_atsp.csv"
CARPETAS_DATA = ["pequeñas", "medianas", "grandes"]

# ==========================================
# 2. PLACEHOLDERS DE SOLVERS
# ==========================================
# def solve_mtz_gurobi(num_nodos, matriz_distancias, tiempo_limite):
#     return {
#         "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
#         "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": 0.0,
#         "Status": "NOT_IMPLEMENTED"
#     }

# def solve_mtz_cplex(num_nodos, matriz_distancias, tiempo_limite):
#     return {
#         "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
#         "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": 0.0,
#         "Status": "NOT_IMPLEMENTED"
#     }

def solve_gg_gurobi(num_nodos, matriz_distancias, tiempo_limite):
    return {
        "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
        "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": 0.0,
        "Status": "NOT_IMPLEMENTED"
    }

def solve_gg_cplex(num_nodos, matriz_distancias, tiempo_limite):
    return {
        "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
        "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": 0.0,
        "Status": "NOT_IMPLEMENTED"
    }

# ==========================================
# 3. FUNCIONES AUXILIARES
# ==========================================

def buscar_archivo_instancia(instance_id):
    nombre_archivo = f"instance_{instance_id}.csv"
    for carpeta in CARPETAS_DATA:
        ruta = os.path.join(carpeta, nombre_archivo)
        if os.path.exists(ruta):
            return ruta, carpeta
    return None, None

def leer_datos_instancia(ruta_archivo):
    """
    Lee el CSV y retorna:
    - num_cities (int)
    - distance_matrix (list of lists)
    - total_distance (float) -> NUEVO CAMPO
    """
    df = pd.read_csv(ruta_archivo)
    row = df.iloc[0]
    
    num_cities = int(row['num_cities'])
    
    # Convertir string de matriz a lista de listas
    distance_matrix_str = row['distance_matrix']
    distance_matrix = ast.literal_eval(distance_matrix_str)
    
    # Extraer la mejor distancia conocida (Benchmark)
    # Si por alguna razón no existe, ponemos -1.0
    total_distance = float(row.get('total_distance', -1.0))
    
    return num_cities, distance_matrix, total_distance

def inicializar_csv_resultados():
    encabezados = [
        "InstanceID",
        "Grupo",
        "NumNodos",
        "Matrix_Size",           # NUEVO: Cantidad de elementos en la matriz
        "Original_Total_Distance", # NUEVO: Benchmark del dataset
        "Modelo",
        "Solver",
        "NumVars",
        "NumConstrs",
        "TimeSeconds",
        "MIPGap_Percent",
        "BestBound",
        "ObjectiveValue",
        "Status",
        "Timestamp"
    ]
    
    with open(ARCHIVO_RESULTADOS, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(encabezados)

def guardar_fila_resultado(datos_fila):
    with open(ARCHIVO_RESULTADOS, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(datos_fila.keys()))
        writer.writerow(datos_fila)

# ==========================================
# 4. LOOP PRINCIPAL
# ==========================================

def ejecutar_flujo():
    inicializar_csv_resultados()
    
    todas_las_instancias = [
        (pid, "Pequeña") for pid in PEQUEÑAS_IDS
    ] + [
        (mid, "Mediana") for mid in MEDIANAS_IDS
    ] + [
        (gid, "Grande") for gid in GRANDES_IDS
    ]

    print(f"--- Iniciando procesamiento ---")

    for instance_id, grupo_etiqueta in todas_las_instancias:
        print(f"\n> Procesando Instancia ID: {instance_id} ({grupo_etiqueta})")
        
        ruta, _ = buscar_archivo_instancia(instance_id)
        if not ruta:
            print(f"  [ERROR] Archivo no encontrado. Saltando...")
            continue
            
        try:
            # 1. Leer datos incluyendo el total_distance original
            n_nodos, matriz_dist, dist_original = leer_datos_instancia(ruta)
            
            # 2. Calcular tamaño de la matriz (elementos totales)
            # Asumimos matriz cuadrada n x n
            matriz_size = len(matriz_dist) * len(matriz_dist[0]) if matriz_dist else 0
            
            print(f"  Nodos: {n_nodos} | Benchmark: {dist_original} | Tamaño Matriz: {matriz_size}")
            
        except Exception as e:
            print(f"  [ERROR] Lectura de datos: {e}")
            continue

        experimentos = [
            ("MTZ", "Gurobi", solve_mtz_gurobi),
            ("MTZ", "CPLEX",  solve_mtz_cplex),
            ("GG",  "Gurobi", solve_gg_gurobi),
            ("GG",  "CPLEX",  solve_gg_cplex)
        ]

        for mod_name, solv_name, func_solver in experimentos:
            print(f"    Ejecutando {mod_name} - {solv_name}...", end=" ")
            
            try:
                res = func_solver(n_nodos, matriz_dist, TIEMPO_LIMITE_SEC)
                print("OK.")
                
                fila = {
                    "InstanceID": instance_id,
                    "Grupo": grupo_etiqueta,
                    "NumNodos": n_nodos,
                    "Matrix_Size": matriz_size,             # NUEVO
                    "Original_Total_Distance": dist_original, # NUEVO
                    "Modelo": mod_name,
                    "Solver": solv_name,
                    "NumVars": res.get("NumVars"),
                    "NumConstrs": res.get("NumConstrs"),
                    "TimeSeconds": res.get("TimeSeconds"),
                    "MIPGap_Percent": res.get("MIPGap"),
                    "BestBound": res.get("BestBound"),
                    "ObjectiveValue": res.get("ObjectiveValue"),
                    "Status": res.get("Status"),
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                guardar_fila_resultado(fila)
                
            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\n--- Fin. Resultados en {ARCHIVO_RESULTADOS} ---")

if __name__ == "__main__":
    ejecutar_flujo()