from docplex.mp.model import Model

def solve_mtz_cplex(num_nodos, matriz_distancias, tiempo_limite):
    """
    Resuelve el ATSP usando la formulación MTZ con CPLEX.
    """
    try:
        # 1. Crear el modelo
        mdl = Model(name='ATSP_MTZ')
        
        # --- Parámetros del Solver ---
        # Definir tiempo límite (en segundos)
        mdl.parameters.timelimit = tiempo_limite
        # Definir Gap relativo al 0% para buscar el óptimo
        mdl.parameters.mip.tolerances.mipgap = 0.0
        # Silenciar la salida por consola
        mdl.context.solver.log_output = False 

        # --- Datos ---
        n = num_nodos
        N = range(n)
        N_not_0 = range(1, n) # Nodos excluyendo el origen (0)

        # --- Variables ---
        # x[i,j] = 1 si arco (i,j) es usado. 
        # Creamos una lista de tuplas para los arcos válidos (i != j)
        arcos = [(i, j) for i in N for j in N if i != j]
        x = mdl.binary_var_dict(arcos, name='x')

        # u[i] = orden de visita del nodo i (1 <= u <= n-1)
        u = mdl.continuous_var_dict(N_not_0, lb=1, ub=n-1, name='u')

        # --- Función Objetivo (Minimizar distancia) ---
        mdl.minimize(mdl.sum(matriz_distancias[i][j] * x[i, j] for i, j in arcos))

        # --- Restricciones ---

        # 1. Grado de Salida: Salir de cada nodo i exactamente una vez
        mdl.add_constraints(
            (mdl.sum(x[i, j] for j in N if i != j) == 1 for i in N),
            names="OutDegree"
        )

        # 2. Grado de Entrada: Entrar a cada nodo j exactamente una vez
        mdl.add_constraints(
            (mdl.sum(x[i, j] for i in N if i != j) == 1 for j in N),
            names="InDegree"
        )

        # 3. Eliminación de Subtours (MTZ)
        # u_i - u_j + (n-1)x_ij <= n-2  para i,j != 0, i!=j
        mdl.add_constraints(
            (u[i] - u[j] + (n - 1) * x[i, j] <= n - 2 
             for i in N_not_0 for j in N_not_0 if i != j),
            names="MTZ_Subtour"
        )

        # --- Ejecución ---
        # clean_before_solve=True asegura reiniciar estados previos si se reusara el objeto
        solucion = mdl.solve(clean_before_solve=True)

        # --- Recopilación de Resultados ---
        
        # Obtener detalles de la ejecución
        details = mdl.solve_details
        
        status_str = str(details.status) # Ej: "integer optimal solution"
        
        # Valores por defecto si no se encuentra solución
        obj_val = -1.0
        mip_gap = 100.0
        best_bound = 0.0
        
        if solucion:
            obj_val = solucion.objective_value
            # CPLEX devuelve el gap como fracción (0.05), lo pasamos a % (5.0)
            mip_gap = details.mip_relative_gap * 100 
            best_bound = details.best_bound
        else:
            # Si no hay solución, intentar recuperar al menos la cota
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