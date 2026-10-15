import numpy as np
from scipy.integrate import solve_ivp
# Se importa ConfigSim para el type hinting (ayuda a detectar errores)
from new_sim import ConfigSim
import time  # [NOTA] Importado para la sección de pruebas, si la reactivas
import traceback  # [NOTA] Importado para depuración avanzada en calc_sim

# --- Constantes Físicas ---
G = 6.67430e-11  # Constante de gravitación universal (N m^2 / kg^2)
M_earth = 5.972e24  # Masa de la Tierra (kg)
R_earth = 6378137.0  # Radio medio de la Tierra (m)
mu_earth = G * M_earth  # Parámetro gravitacional de la Tierra

M_moon = 7.342e22  # Masa de la Luna (kg)
R_moon = 1.7374e6  # Radio medio de la Luna (m)
mu_moon = G * M_moon  # Parámetro gravitacional de la Luna


# --- Funciones Auxiliares ---

def get_thrust_vector(t, config: ConfigSim, current_mass):
    """
    Calcula el vector de empuje en el tiempo 't' para todos los encendidos.
    El empuje se define en el sistema de coordenadas inercial.
    """
    total_thrust_vector = np.array([0.0, 0.0, 0.0])

    # [CORREGIDO] Iteramos sobre el número de encendidos ACTIVOS
    for i in range(config.num_encendidos):
        # [CORREGIDO] Accedemos a los datos de encendido por índice numérico
        burn = config.data_encendidos[i]

        t_start = burn[0]
        # [CORREGIDO] El índice 1 es la DURACIÓN, no el t_end
        t_end = burn[0] + burn[1]

        if t_start <= t < t_end:
            thrust_magnitude = burn[2]
            # Isp = burn[3] # No se usa para el vector de empuje
            theta_deg = burn[4]
            beta_deg = burn[5]

            # Convertir ángulos a radianes
            theta_rad = np.radians(theta_deg)
            beta_rad = np.radians(beta_deg)

            # z = r * cos(theta)
            # x = r * sin(theta) * cos(beta)
            # y = r * sin(theta) * sin(beta)

            thrust_x = thrust_magnitude * np.sin(theta_rad) * np.cos(beta_rad)
            thrust_y = thrust_magnitude * np.sin(theta_rad) * np.sin(beta_rad)
            thrust_z = thrust_magnitude * np.cos(theta_rad)

            total_thrust_vector += np.array([thrust_x, thrust_y, thrust_z])

    return total_thrust_vector


def get_mass_flow_rate(t, config: ConfigSim):
    """
    Calcula el flujo de masa total para todos los encendidos activos.
    """
    g0 = 9.80665  # Gravedad estándar a nivel del mar
    total_mass_flow = 0.0

    # [CORREGIDO] Iteramos sobre el número de encendidos ACTIVOS
    for i in range(config.num_encendidos):
        # [CORREGIDO] Accedemos a los datos de encendido por índice numérico
        burn = config.data_encendidos[i]

        t_start = burn[0]
        t_end = burn[0] + burn[1]  # El índice 1 es la DURACIÓN
        thrust_magnitude = burn[2]
        Isp = burn[3]

        # [CORREGIDO] Añadida comprobación de Isp > 0 para evitar división por cero
        if t_start <= t < t_end and Isp > 0:
            total_mass_flow -= (thrust_magnitude / (g0 * Isp))  # Es negativo porque se pierde masa

    return total_mass_flow


def equations_of_motion(t, y, config: ConfigSim):
    """
    Define las ecuaciones diferenciales de movimiento para el cohete y la Luna.
    y = [rx, ry, rz, vx, vy, vz, m, xL, yL, zL, vxL, vyL, vzL]
    """
    # Desempaquetar el vector de estado
    rx, ry, rz, vx, vy, vz, m, xL, yL, zL, vxL, vyL, vzL = y

    # --- Cohete ---
    r_mag = np.sqrt(rx ** 2 + ry ** 2 + rz ** 2)
    # Aceleración gravitacional de la Tierra sobre el cohete
    ax_g_earth = -mu_earth * rx / r_mag ** 3
    ay_g_earth = -mu_earth * ry / r_mag ** 3
    az_g_earth = -mu_earth * rz / r_mag ** 3

    # Vector de posición del cohete respecto a la Luna
    r_rocket_to_moon_x = rx - xL
    r_rocket_to_moon_y = ry - yL
    r_rocket_to_moon_z = rz - zL
    r_rocket_to_moon_mag = np.sqrt(r_rocket_to_moon_x ** 2 + r_rocket_to_moon_y ** 2 + r_rocket_to_moon_z ** 2)

    # Evitar división por cero si el cohete está (improbablemente) en el centro de la Luna
    if r_rocket_to_moon_mag == 0:
        ax_g_moon, ay_g_moon, az_g_moon = 0.0, 0.0, 0.0
    else:
        # Aceleración gravitacional de la Luna sobre el cohete
        ax_g_moon = -mu_moon * r_rocket_to_moon_x / r_rocket_to_moon_mag ** 3
        ay_g_moon = -mu_moon * r_rocket_to_moon_y / r_rocket_to_moon_mag ** 3
        az_g_moon = -mu_moon * r_rocket_to_moon_z / r_rocket_to_moon_mag ** 3

    # Aceleración del empuje
    thrust_vector = get_thrust_vector(t, config, m)
    # [CORREGIDO] Aseguramos que la masa no sea cero para evitar división por cero
    if m > 0:
        ax_thrust, ay_thrust, az_thrust = thrust_vector / m
    else:
        ax_thrust, ay_thrust, az_thrust = 0.0, 0.0, 0.0
        m = 1e-6  # Evitar que la masa sea cero en el integrador

    # Flujo de masa
    dm_dt = get_mass_flow_rate(t, config)

    # Manejo de Staging (Recomendación: Usar eventos de solve_ivp para esto)
    # Esta implementación es numéricamente inestable
    if config.m1 > 0 and t >= config.tsep1 and m > (config.m0 - config.m1):
        dm_dt -= config.m1 / 0.1  # Simulación de separación (inestable)
        if m < (config.m0 - config.m1):
            dm_dt = get_mass_flow_rate(t, config)  # Volver al flujo normal

    # Ecuaciones de movimiento del cohete
    drx_dt, dry_dt, drz_dt = vx, vy, vz
    dvx_dt = ax_g_earth + ax_g_moon + ax_thrust
    dvy_dt = ay_g_earth + ay_g_moon + ay_thrust
    dvz_dt = az_g_earth + az_g_moon + az_thrust

    # --- Luna ---
    r_moon_mag = np.sqrt(xL ** 2 + yL ** 2 + zL ** 2)
    # Aceleración gravitacional de la Tierra sobre la Luna
    if r_moon_mag == 0:
        axL_g_earth, ayL_g_earth, azL_g_earth = 0.0, 0.0, 0.0
    else:
        axL_g_earth = -mu_earth * xL / r_moon_mag ** 3
        ayL_g_earth = -mu_earth * yL / r_moon_mag ** 3
        azL_g_earth = -mu_earth * zL / r_moon_mag ** 3

    # Ecuaciones de movimiento de la Luna
    dxL_dt, dyL_dt, dzL_dt = vxL, vyL, vzL
    dvxL_dt = axL_g_earth
    dvyL_dt = ayL_g_earth
    dvzL_dt = azL_g_earth

    return [drx_dt, dry_dt, drz_dt, dvx_dt, dvy_dt, dvz_dt, dm_dt,
            dxL_dt, dyL_dt, dzL_dt, dvxL_dt, dvyL_dt, dvzL_dt]


def calc_sim(config: ConfigSim):
    """
    Ejecuta la simulación de trayectoria basada en la configuración dada.

    [CORREGIDO] Retorna la tupla estándar de 17 elementos que
    main.py, archivo_new.py y grf_data.py esperan.
    """
    # Generar la descripción por si no se hizo
    config.generate_description()

    # --- [CORRECCIÓN DE TYPO] ---
    # El vector de estado inicial 'y0' debe coincidir
    # con los nombres de atributos de la clase ConfigSim
    y0 = [config.x0, config.y0, config.z0,
          config.vx0, config.vy0, config.vz0,
          config.m0,
          config.xl0, config.yl0, config.zl0,
          config.velxL0, config.velyL0, config.velzL0]  # <-- Nombres corregidos
    # --- [FIN CORRECCIÓN] ---

    # Tiempo de simulación
    t_span = (0.0, config.periodo)
    t_eval = np.linspace(0.0, config.periodo, config.num_calc)

    try:
        # Resolver las ecuaciones diferenciales
        sol = solve_ivp(
            lambda t, y: equations_of_motion(t, y, config),
            t_span,
            y0,
            t_eval=t_eval,
            rtol=1e-8,  # Tolerancia relativa
            atol=1e-8,  # Tolerancia absoluta
            max_step=config.max_step  # Paso máximo de tiempo
        )

        if not sol.success:
            print(f"[ERROR] La simulación (solve_ivp) falló: {sol.message}")
            return None

        # Desempaquetar resultados
        tout = sol.t
        x, y, z = sol.y[0], sol.y[1], sol.y[2]
        vx, vy, vz = sol.y[3], sol.y[4], sol.y[5]
        mass = sol.y[6]
        xL, yL, zL = sol.y[7], sol.y[8], sol.y[9]
        vxL, vyL, vzL = sol.y[10], sol.y[11], sol.y[12]

        # --- [BLOQUE CORREGIDO: PREPARAR DATOS DE RETORNO] ---

        # 1. Calcular altitud (requerido por main.py y archivo_new.py)
        alt_tierra_km = (np.sqrt(x ** 2 + y ** 2 + z ** 2) - R_earth) / 1000.0

        # 2. Extraer lista de ángulos (requerido por main.py y archivo_new.py)
        # main.py espera una lista de [theta, beta] por CADA encendido (hasta 5)
        # para poder unirlos correctamente en 'craft_sim_results'
        ang = [[burn[4], burn[5]] for burn in config.data_encendidos]

        # 3. Extraer la descripción (requerido por main.py y archivo_new.py)
        desc = config.description

        # --- [FIN BLOQUE CORREGIDO] ---

        # (Se elimina el cálculo post-simulación de ax, ay, az,
        # ya que grf_data.py los calcula por su cuenta si los necesita)

        # [CORREGIDO] Retornar la tupla de 17 elementos estándar
        return (tout, x, y, z, vx, vy, vz, mass, alt_tierra_km,
                xL, yL, zL, vxL, vyL, vzL, ang, desc)

    except Exception as e:
        print(f"Error fatal durante la simulación (calc_sim): {e}")
        # Imprimir un traceback más detallado para depuración
        traceback.print_exc()
        return None

# [NOTA] Las funciones 'craft_sim_results' y el bloque
# 'if __name__ == "__main__":' han sido eliminados de este archivo
# porque 'main.py' contiene la versión principal de esa lógica
# y las pruebas deben ejecutarse desde el menú principal.