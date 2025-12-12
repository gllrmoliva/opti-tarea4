import os
import gurobipy as gp
from dotenv import load_dotenv

# ==========================================
# 0. Creación de entorno
# ==========================================

def create_env():
    """
    Decide si utilizar licencia WLS o licencia local. Se hizo así debido a que
    uno de los integrantes tiene solo ordenador de escritorio.
    """
    # Si existen variables WLS, usar WLS; si no, usar licencia local
    if all(v in os.environ for v in ['GRB_WLSACCESSID', 'GRB_WLSSECRET', 'GRB_LICENSEID']):
        env = gp.Env(empty=True)
        env.setParam('WLSAccessID', os.environ['GRB_WLSACCESSID'])
        env.setParam('WLSSecret', os.environ['GRB_WLSSECRET'])
        env.setParam('LicenseID', int(os.environ['GRB_LICENSEID']))
        return env
    else:
        # usa la licencia local (offline)
        print("Se ha seleccionado la licencia OFFLINE")
        return gp.Env()

