import gurobipy as gp
from gurobipy import GRB
from gurobi_setup import create_env

def solve_mtz_gurobi(num_nodos, matriz_distancias, tiempo_limite):
    """
    Resuelve el ATSP usando la formulación MTZ con Gurobi.
    """
    try:
        # Crear entorno y modelo
        # Usamos 'with' o dispose() para liberar licencias al terminar
        with create_env() as env:
            env.setParam("OutputFlag", 0)  # Silenciar log en consola
            env.start()
            with gp.Model("ATSP_MTZ", env=env) as m:
                
                # --- Parámetros del Solver ---
                m.setParam('TimeLimit', tiempo_limite)
                m.setParam('MIPGap', 0.0)  # Buscar el óptimo global (0%)
                
                # --- Datos ---
                n = num_nodos
                N = range(n)
                N_not_0 = range(1, n) # Nodos excluyendo el origen (0)

                # --- Variables ---
                # x[i,j] = 1 si arco (i,j) es usado
                x = m.addVars(n, n, vtype=GRB.BINARY, name="x")
                
                # u[i] = orden de visita del nodo i (1 <= u <= n-1)
                u = m.addVars(N_not_0, vtype=GRB.CONTINUOUS, lb=1, ub=n-1, name="u")

                # --- Función Objetivo (Minimizar distancia) ---
                # Se excluyen los bucles i==j
                m.setObjective(
                    gp.quicksum(matriz_distancias[i][j] * x[i,j] 
                                for i in N for j in N if i != j),
                    GRB.MINIMIZE
                )

                # --- Restricciones ---
                
                # 1. Grado de Salida: Salir de cada nodo i exactamente una vez
                m.addConstrs(
                    (gp.quicksum(x[i,j] for j in N if j != i) == 1 for i in N),
                    name="OutDegree"
                )

                # 2. Grado de Entrada: Entrar a cada nodo j exactamente una vez
                m.addConstrs(
                    (gp.quicksum(x[i,j] for i in N if i != j) == 1 for j in N),
                    name="InDegree"
                )

                # 3. Eliminación de Subtours (MTZ)
                # Restricción: u_i - u_j + (n-1)x_ij <= n-2  para i,j != 0, i!=j
                m.addConstrs(
                    (u[i] - u[j] + (n - 1) * x[i,j] <= n - 2 
                     for i in N_not_0 for j in N_not_0 if i != j),
                    name="MTZ_Subtour"
                )

                # --- Ejecución ---
                m.optimize()

                # --- Recopilación de Resultados ---
                
                # Mapeo de status numérico a texto
                status_code = m.Status
                status_map = {
                    2: "Optimal",
                    3: "Infeasible",
                    9: "TimeLimit",
                    11: "Interrupted"
                }
                status_str = status_map.get(status_code, f"Code_{status_code}")

                # Valores seguros si no se encontró solución entera
                obj_val = -1.0
                mip_gap = 100.0
                best_bound = 0.0

                if m.SolCount > 0:
                    obj_val = m.ObjVal
                    mip_gap = m.MIPGap * 100  # Convertir a porcentaje (ej: 0.05 -> 5.0)
                
                # Intentar obtener cota inferior (BestBound) incluso si no hay solución factible
                try:
                    best_bound = m.ObjBound
                except AttributeError:
                    pass # Puede pasar si el modelo es infactible o hubo error antes

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
