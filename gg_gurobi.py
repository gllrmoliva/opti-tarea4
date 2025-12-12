import gurobipy as gp
from gurobipy import GRB

def solve_gg_gurobi(num_nodos, matriz_distancias, tiempo_limite):
    """
    Resuelve el ATSP usando la formulación GG (Gavras-Graves) con Gurobi.
    Esta es una formulación de flujo de una mercancía (Single Commodity Flow).
    """
    try:
        with gp.Env(empty=True) as env:
            env.setParam("OutputFlag", 0)
            env.start()
            with gp.Model("ATSP_GG", env=env) as m:
                
                # --- Parámetros ---
                m.setParam('TimeLimit', tiempo_limite)
                m.setParam('MIPGap', 0.0)

                # --- Datos ---
                n = num_nodos
                N = range(n)
                # Arcos válidos (excluyendo bucles i==j)
                arcos = [(i, j) for i in N for j in N if i != j]

                # --- Variables ---
                
                # x[i,j] = 1 si se viaja de i a j
                x = m.addVars(arcos, vtype=GRB.BINARY, name="x")
                
                # g[i,j] = flujo que pasa por el arco (i,j). 
                # Cota máxima posible es n-1 (salida del depósito)
                g = m.addVars(arcos, vtype=GRB.CONTINUOUS, lb=0, ub=n-1, name="g")

                # --- Función Objetivo ---
                m.setObjective(
                    gp.quicksum(matriz_distancias[i][j] * x[i,j] for i, j in arcos),
                    GRB.MINIMIZE
                )

                # --- Restricciones ---

                # 1. Assignment (Grado Salida = 1)
                m.addConstrs(
                    (gp.quicksum(x[i,j] for j in N if i != j) == 1 for i in N),
                    name="OutDegree"
                )

                # 2. Assignment (Grado Entrada = 1)
                m.addConstrs(
                    (gp.quicksum(x[i,j] for i in N if i != j) == 1 for j in N),
                    name="InDegree"
                )

                # 3. Conservación de Flujo (Gavras-Graves)
                # Para cada nodo i (excepto el 0), el flujo neto (Entra - Sale) debe ser 1 (su demanda)
                # Sum(g_ji) - Sum(g_ij) = 1   para i in {1..n-1}
                m.addConstrs(
                    (gp.quicksum(g[j,i] for j in N if j != i) - 
                     gp.quicksum(g[i,j] for j in N if j != i) == 1 
                     for i in range(1, n)),
                    name="FlowConservation"
                )
                
                # Nota: No es estrictamente necesario poner la restricción para el nodo 0 
                # si las demás se cumplen y el total es consistente, pero la lógica implicita es:
                # Salida de 0 - Entrada a 0 = n - 1.

                # 4. Vinculación y Capacidad (Linking Constraints)
                # Si x_ij = 0, entonces g_ij = 0.
                # Si x_ij = 1, g_ij <= n - 1.
                m.addConstrs(
                    (g[i,j] <= (n - 1) * x[i,j] for i, j in arcos),
                    name="Linking_Capacity"
                )

                # --- Ejecución ---
                m.optimize()

                # --- Recopilación de Resultados ---
                status_code = m.Status
                status_map = {2: "Optimal", 3: "Infeasible", 9: "TimeLimit", 11: "Interrupted"}
                status_str = status_map.get(status_code, f"Code_{status_code}")

                obj_val = -1.0
                mip_gap = 100.0
                best_bound = 0.0

                if m.SolCount > 0:
                    obj_val = m.ObjVal
                    mip_gap = m.MIPGap * 100
                
                try:
                    best_bound = m.ObjBound
                except AttributeError:
                    pass

                return {
                    "NumVars": m.NumVars,
                    "NumConstrs": m.NumConstrs,
                    "TimeSeconds": m.Runtime,
                    "MIPGap": mip_gap,
                    "BestBound": best_bound,
                    "ObjectiveValue": obj_val,
                    "Status": status_str
                }

    except gp.GurobiError as e:
        print(f"    [Gurobi Error]: {e}")
        return {
            "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
            "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": -1.0,
            "Status": "Error_Gurobi"
        }
    except Exception as e:
        print(f"    [Error General]: {e}")
        return {
            "NumVars": 0, "NumConstrs": 0, "TimeSeconds": 0.0,
            "MIPGap": 100.0, "BestBound": 0.0, "ObjectiveValue": -1.0,
            "Status": "Error_Exception"
        }