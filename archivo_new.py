import numpy as np
import os

LOG_DIR = "log_simulaciones"
KEYS_FILE = os.path.join(LOG_DIR, "Nombres_Sim.txt")


def get_next_sim_name():
    """
    Encuentra el siguiente nombre de archivo de simulación disponible
    (ej. sim_run_034, sim_run_035, ...).
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    try:
        with open(KEYS_FILE, "r") as f:
            keys = f.read().splitlines()

        if not keys:
            return "sim_run_000"

        last_key = keys[-1]
        last_num = int(last_key.split('_')[-1])
        next_num = last_num + 1

        return f"sim_run_{next_num:03d}"

    except FileNotFoundError:
        return "sim_run_000"
    except Exception as e:
        print(f"Error al obtener el nombre de la simulación: {e}. Usando 'sim_run_tmp'.")
        return "sim_run_tmp"


def guardar_simulacion(result_list):
    """
    Guarda los datos de la simulación (lista de 17 elementos) en un archivo .npz
    y retorna el nombre de la simulación guardada.
    """
    if not isinstance(result_list, list) or len(result_list) < 17:
        print(f"Error al guardar: Se esperaba una lista de 17 elementos, se recibieron {len(result_list)}.")
        return None  # <-- [MODIFICADO] Retorna None en caso de error

    try:
        (tout, x, y, z, vx, vy, vz, mass, alt_tierra_km,
         xL, yL, zL, vxL, vyL, vzL, ang, desc) = result_list
    except ValueError as e:
        print(f"Error al desempaquetar la lista de resultados: {e}.")
        return None  # <-- [MODIFICADO] Retorna None en caso de error

    sim_name = get_next_sim_name()
    file_path = os.path.join(LOG_DIR, sim_name)

    try:
        np.savez(
            file_path,
            name=sim_name,
            description=desc,
            position_x=x,
            position_y=y,
            position_z=z,
            velocity_x=vx,
            velocity_y=vy,
            velocity_z=vz,
            mass=mass,
            alt_tierra_km=alt_tierra_km,
            L_pos_x=xL,
            L_pos_y=yL,
            L_pos_z=zL,
            L_vel_x=vxL,
            L_vel_y=vyL,
            L_vel_z=vzL,
            time=tout,
            ang=np.array(ang, dtype=object)
        )

        with open(KEYS_FILE, "a") as f:
            f.write(f"{sim_name}\n")

        print(f"Simulación guardada exitosamente como: {sim_name}.npz")

        # --- [NUEVO] ---
        # Retorna el nombre para que 'main' pueda usarlo en la leyenda.
        return sim_name
        # ---------------

    except Exception as e:
        print(f"Error al guardar el archivo .npz: {e}")
        return None  # <-- [MODIFICADO] Retorna None en caso de error