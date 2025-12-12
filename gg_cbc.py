from mip import Model, xsum, minimize, BINARY, CONTINUOUS, OptimizationStatus, CBC
import time

def solve_gg_cbc(num_nodos, matriz_distancias, tiempo_limite):
    """
    Resuelve el ATSP usando la formulación GG (Gavras-Graves) con CBC.
    """
    try:
        m = Model(solver_name=CBC)
        m.verbose = 0
        m.max_seconds = tiempo_limite
        
        n = num_nodos
        N = range(n)
        
        # --- Variables ---
        # x[i][j]: binaria (ruta)
        x = [[m.add_var(var_type=BINARY, name=f'x_{i}_{j}') for j in N] for i in N]
        
        # g[i][j]: continua (flujo), 0 <= g <= n-1
        g = [[m.add_var(var_type=CONTINUOUS, lb=0, ub=n-1, name=f'g_{i}_{j}') for j in N] for i in N]

        # --- Función Objetivo ---
        m.objective = minimize(
            xsum(matriz_distancias[i][j] * x[i][j] for i in N for j in N if i != j)
        )

        # --- Restricciones ---

        # 1. Grado de Salida = 1
        for i in N:
            m += xsum(x[i][j] for j in N if j != i) == 1

        # 2. Grado de Entrada = 1
        for j in N:
            m += xsum(x[i][j] for i in N if i != j) == 1

        # 3. Conservación de Flujo (Gavras-Graves)
        # Para cada nodo cliente i (1..n-1): Entrada - Salida = 1
        for i in range(1, n):
            flujo_entrante = xsum(g[j][i] for j in N if j != i)
            flujo_saliente = xsum(g[i][j] for j in N if j != i)
            m += (flujo_entrante - flujo_saliente == 1)

        # 4. Vinculación y Capacidad (Linking Constraints)
        # g_ij <= (n-1) * x_ij
        for i in N:
            for j in N:
                if i != j:
                    m += g[i][j] <= (n - 1) * x[i][j]

        # --- Ejecución ---
        start_time = time.time()
        status = m.optimize()
        run_time = time.time() - start_time

        # --- Recopilación de Resultados ---
        status_map = {
            OptimizationStatus.OPTIMAL: "Optimal",
            OptimizationStatus.FEASIBLE: "Feasible",
            OptimizationStatus.NO_SOLUTION_FOUND: "NoSolution",
            OptimizationStatus.INFEASIBLE: "Infeasible",
            OptimizationStatus.INT_INFEASIBLE: "Infeasible",
            OptimizationStatus.UNBOUNDED: "Unbounded",
            OptimizationStatus.ERROR: "Error"
        }
        status_str = status_map.get(status, f"Code_{status}")

        obj_val = -1.0
        mip_gap = 100.0
        best_bound = 0.0

        if m.num_solutions > 0:
            obj_val = m.objective_value
            best_bound = m.objective_bound
            if abs(obj_val) > 1e-9:
                mip_gap = abs(best_bound - obj_val) / abs(obj_val) * 100
            else:
                mip_gap = 0.0
        else:
            best_bound = m.objective_bound

        if best_bound is None: best_bound = 0.0

        return {
            "NumVars": m.num_cols,
            "NumConstrs": m.num_rows,
            "TimeSeconds": run_time,
            "MIPGap": mip_gap,
            "BestBound": best_bound,
            "ObjectiveValue": obj_val,
            "Status": status_str
        }

    except Exception as e:
        print(f"    [CBC Error]: {e}")
        return {
            "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
            "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": -1.0,
            "Status": "Error_CBC"
        }