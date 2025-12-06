import os
import gurobipy as gp
from gurobipy import GRB


def create_env():
    """
    Decide si utilizar licencia WLS o licencia local.
    """
    # Si existen variables WLS, usar WLS; si no, usar licencia local
    if all(v in os.environ for v in ['GRB_WLSACCESSID', 'GRB_WLSSECRET', 'GRB_LICENSEID']):
        print("Se ha seleccionado la licencia WLS")
        env = gp.Env(empty=True)
        env.setParam('WLSAccessID', os.environ['GRB_WLSACCESSID'])
        env.setParam('WLSSecret', os.environ['GRB_WLSSECRET'])
        env.setParam('LicenseID', int(os.environ['GRB_LICENSEID']))
        env.start()
        return env
    else:
        # usa la licencia local (offline)
        print("Se ha seleccionado la licencia OFFLINE")
        return gp.Env()


def solve_mtz(instance, env, time_limit=3600, mip_gap=0.0):
    pass
 

def solve_gg(instance, env, time_limit=3600, mip_gap=0.0):
    pass


if __name__ == "__main__":
    # aquí espacio para testear
    pass