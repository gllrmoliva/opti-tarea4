from docplex.mp.model import Model

def solve_gg_cplex(num_nodos, matriz_distancias, tiempo_limite):
    """
    Resuelve el ATSP usando la formulación GG (Gavras-Graves) con CPLEX.
    """
    try:
        # 1. Crear el modelo
        mdl = Model(name='ATSP_GG')

        # --- Parámetros del Solver ---
        mdl.parameters.timelimit = tiempo_limite
        mdl.parameters.mip.tolerances.mipgap = 0.0
        mdl.context.solver.log_output = False

        # --- Datos ---
        n = num_nodos
        N = range(n)
        # Lista de arcos válidos (tuplas i,j donde i != j)
        arcos = [(i, j) for i in N for j in N if i != j]

        # --- Variables ---
        
        # x[i,j] = 1 si se viaja de i a j (Variable Binaria)
        x = mdl.binary_var_dict(arcos, name='x')

        # g[i,j] = flujo de carga en el arco (i,j) (Variable Continua)
        # La carga máxima posible es n-1 (al salir del depósito)
        g = mdl.continuous_var_dict(arcos, lb=0, ub=n-1, name='g')

        # --- Función Objetivo ---
        mdl.minimize(mdl.sum(matriz_distancias[i][j] * x[i, j] for i, j in arcos))

        # --- Restricciones ---

        # 1. Grado de Salida = 1
        mdl.add_constraints(
            (mdl.sum(x[i, j] for j in N if i != j) == 1 for i in N),
            names="OutDegree"
        )

        # 2. Grado de Entrada = 1
        mdl.add_constraints(
            (mdl.sum(x[i, j] for i in N if i != j) == 1 for j in N),
            names="InDegree"
        )

        # 3. Conservación de Flujo (Gavras-Graves)
        # Para todo nodo i en {1, ..., n-1} (clientes):
        # (Flujo que entra) - (Flujo que sale) = 1 (Demanda de 1 unidad)
        mdl.add_constraints(
            (mdl.sum(g[j, i] for j in N if j != i) - 
             mdl.sum(g[i, j] for j in N if j != i) == 1 
             for i in range(1, n)),
            names="FlowConservation"
        )

        # 4. Vinculación y Capacidad (Linking Constraints)
        # El flujo g_ij solo puede ser positivo si el arco x_ij está activo.
        # Además, g_ij no puede superar la capacidad máxima (n-1).
        mdl.add_constraints(
            (g[i, j] <= (n - 1) * x[i, j] for i, j in arcos),
            names="Linking_Capacity"
        )

        # --- Ejecución ---
        solucion = mdl.solve(clean_before_solve=True)

        # --- Recopilación de Resultados ---
        details = mdl.solve_details
        status_str = str(details.status)

        obj_val = -1.0
        mip_gap = 100.0
        best_bound = 0.0

        if solucion:
            obj_val = solucion.objective_value
            mip_gap = details.mip_relative_gap * 100
            best_bound = details.best_bound
        else:
            best_bound = details.best_bound

        return {
            "NumVars": mdl.number_of_variables,
            "NumConstrs": mdl.number_of_constraints,
            "TimeSeconds": details.time,
            "MIPGap": mip_gap,
            "BestBound": best_bound,
            "ObjectiveValue": obj_val,
            "Status": status_str
        }

    except Exception as e:
        print(f"    [CPLEX Error]: {e}")
        return {
            "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
            "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": -1.0,
            "Status": "Error_CPLEX"
        }