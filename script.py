import os
import csv
from datetime import datetime
import glob
import sys

from mtz_gurobi import solve_mtz_gurobi
from mtz_cplex import solve_mtz_cplex
from mtz_cbc import solve_mtz_cbc
from gg_gurobi import solve_gg_gurobi
from gg_cplex import solve_gg_cplex
from gg_cbc import solve_gg_cbc

# ==========================================
# 1. CONFIGURACIÓN GLOBAL
# ==========================================

# Rutas de las carpetas con archivos .atsp
DIR_MUY_PEQUENAS = "./instancias/muy_pequeñas"
DIR_PEQUENAS = "./instancias/pequeñas" 
DIR_MEDIANAS = "./instancias/medianas"
DIR_GRANDES  = "./instancias/grandes"

# Configuración de ejecución
TIEMPO_LIMITE_SEC = 3600
ARCHIVO_RESULTADOS = "resultados_atsp_tsplib.csv"

# --- NUEVO: VARIABLE DE DEBUG ---
# Si es True, imprime resumen de la matriz tras parsear
DEBUG_PARSE = True 

# ==========================================
# 3. PARSER TSPLIB (.atsp) Y UTILS
# ==========================================

def leer_atsp(ruta_archivo):
    """
    Parsea un archivo con formato TSPLIB ATSP.
    Maneja EDGE_WEIGHT_FORMAT: FULL_MATRIX
    """
    dimension = 0
    matriz = []
    
    try:
        with open(ruta_archivo, 'r') as f:
            lines = f.readlines()

        # 1. Leer Metadatos
        start_reading_data = False
        raw_numbers = []

        for line in lines:
            line = line.strip()
            if line == "EOF": break
                
            if line.startswith("DIMENSION"):
                parts = line.split(":")
                dimension = int(parts[1].strip())
                
            elif line.startswith("EDGE_WEIGHT_SECTION"):
                start_reading_data = True
                continue
            
            if start_reading_data:
                tokens = line.split()
                for token in tokens:
                    # Validar que sea número (maneja negativos si los hubiera)
                    if token.lstrip('-').isdigit():
                        raw_numbers.append(int(token))

        # 2. Validaciones y Construcción
        if dimension == 0:
            raise ValueError("No se encontró DIMENSION.")
        
        expected_size = dimension * dimension
        
        # Ajuste robusto de datos
        if len(raw_numbers) > expected_size:
             raw_numbers = raw_numbers[:expected_size]
        elif len(raw_numbers) < expected_size:
             raise ValueError(f"Datos incompletos: {len(raw_numbers)}/{expected_size}")

        # Convertir lista plana a Matriz NxN
        for i in range(dimension):
            fila = raw_numbers[i * dimension : (i + 1) * dimension]
            matriz.append(fila)

        # En formato .atsp el óptimo no viene en el archivo
        total_distance = -1.0 

        return dimension, matriz, total_distance

    except Exception as e:
        print(f"Error parseando {ruta_archivo}: {e}")
        return 0, [], -1.0

def imprimir_resumen_instancia(nombre, n, matriz):
    """Imprime un resumen visual estilo numpy si DEBUG_PARSE es True."""
    size = n * n
    print(f"\n[DEBUG] Instancia: {nombre}")
    print(f"        Nodos: {n}")
    print(f"        Tamaño Matriz: {size} elementos")
    print(f"        Vista Previa Matriz:")

    def fmt_row(row):
        # Formatea una fila mostrando solo inicio y fin si es muy larga
        if len(row) > 6:
            return f"[{', '.join(map(str, row[:3]))}, ..., {', '.join(map(str, row[-3:]))}]"
        return str(row)

    if n > 6:
        # Imprimir primeras 3 filas
        for i in range(3):
            print(f"          {fmt_row(matriz[i])}")
        print("          ...")
        # Imprimir últimas 3 filas
        for i in range(n-3, n):
            print(f"          {fmt_row(matriz[i])}")
    else:
        # Imprimir todo si es pequeña
        for row in matriz:
            print(f"          {str(row)}")
    print("-" * 40)

# ==========================================
# 4. GESTIÓN DE CSV Y RESULTADOS
# ==========================================

def inicializar_csv_resultados():
    encabezados = [
        "InstanceID",      # Nombre del archivo sin extensión
        "Grupo",           # Pequeña, Mediana, Grande
        "NumNodos",
        "Matrix_Size",     # NUEVO CAMPO
        "Benchmark_Optimum", 
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
# 5. ORQUESTADOR PRINCIPAL
# ==========================================

def obtener_archivos_de_carpeta(carpeta):
    patron = os.path.join(carpeta, "*.atsp")
    archivos = glob.glob(patron)
    archivos.sort()
    return archivos

def ejecutar_flujo():
    inicializar_csv_resultados()
    
    archivos_mypeq = obtener_archivos_de_carpeta(DIR_MUY_PEQUENAS)
    archivos_peq = obtener_archivos_de_carpeta(DIR_PEQUENAS)
    archivos_med = obtener_archivos_de_carpeta(DIR_MEDIANAS)
    archivos_gra = obtener_archivos_de_carpeta(DIR_GRANDES)

    cola_trabajo = []
    for f in archivos_mypeq: cola_trabajo.append((f, "VerySmall"))
    for f in archivos_peq: cola_trabajo.append((f, "Small"))
    for f in archivos_med: cola_trabajo.append((f, "Medium"))
    for f in archivos_gra: cola_trabajo.append((f, "Big"))

    print(f"--- Iniciando procesamiento de {len(cola_trabajo)} archivos ATSP ---")
    if DEBUG_PARSE:
        print("--- MODO DEBUG ACTIVADO: Se mostrarán detalles de matrices ---")

    for ruta_archivo, grupo_etiqueta in cola_trabajo:
        # 1. Obtener ID limpio (sin extensión .atsp)
        nombre_completo = os.path.basename(ruta_archivo)
        instance_id = os.path.splitext(nombre_completo)[0] # NUEVO: Elimina .atsp
        
        print(f"\n> Procesando: {instance_id} ({grupo_etiqueta})")
        
        # 2. Leer Instancia
        n_nodos, matriz_dist, benchmark = leer_atsp(ruta_archivo)
        
        if n_nodos == 0:
            print("  [SKIP] Error en lectura de archivo.")
            continue

        # 3. Calcular tamaño de matriz
        matrix_size = n_nodos * n_nodos # NUEVO: Cantidad total de elementos

        # 4. Debug Print (Si está activado)
        if DEBUG_PARSE:
            imprimir_resumen_instancia(instance_id, n_nodos, matriz_dist)
        else:
            print(f"  Nodos: {n_nodos} | Matrix Size: {matrix_size}")

        # 5. Definir Experimentos
        experimentos = [
            ("MTZ", "Gurobi", solve_mtz_gurobi),
            ("MTZ", "CPLEX",  solve_mtz_cplex),
            # ("MTZ", "CBC", solve_mtz_cbc),
            ("GG",  "Gurobi", solve_gg_gurobi),
            ("GG",  "CPLEX",  solve_gg_cplex)
            # ("GG", "CBC", solve_gg_cbc)
        ]

        # 6. Ejecutar Solvers
        for mod_name, solv_name, func_solver in experimentos:
            print(f"    Ejecutando {mod_name} - {solv_name}...", end=" ", flush=True)
            
            try:
                res = func_solver(n_nodos, matriz_dist, TIEMPO_LIMITE_SEC)
                print(f"OK. (Status: {res.get('Status')})")
                
                fila = {
                    "InstanceID": instance_id, # ID limpio
                    "Grupo": grupo_etiqueta,
                    "NumNodos": n_nodos,
                    "Matrix_Size": matrix_size, # NUEVO
                    "Benchmark_Optimum": benchmark, 
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
                print(f"ERROR CRÍTICO: {e}")

    print(f"\n--- Fin del proceso. Resultados guardados en {ARCHIVO_RESULTADOS} ---")

if __name__ == "__main__":
    # Verificación de carpetas
    for d in [DIR_PEQUENAS, DIR_MEDIANAS, DIR_GRANDES]:
        if not os.path.exists(d):
            print(f"Advertencia: La carpeta {d} no existe.")
    
    ejecutar_flujo()
