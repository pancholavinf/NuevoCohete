import numpy as np
import copy  # Necesario para copias profundas


# -----------------------------------------------------------------
# --- CLASE DE CONFIGURACIÓN PRINCIPAL (Sin cambios) ---
# -----------------------------------------------------------------
class ConfigSim:
    def __init__(self):
        self.periodo = 4000
        self.num_calc = 1000
        self.max_step = 0.5
        self.m0 = 5600.0
        self.x0 = 6371000.0
        self.y0 = 0.0
        self.z0 = 0.0
        self.vx0 = 0.0
        self.vy0 = 1000.0
        self.vz0 = 0.0
        self.m1 = 20.0
        self.tsep1 = 2.0
        self.xl0 = 384_400_000.0
        self.yl0 = 0.0
        self.zl0 = 0.0
        self.velxL0 = 0.0
        self.velyL0 = 1022.0
        self.velzL0 = 0.0
        self.num_encendidos = 3
        self.data_encendidos = []
        self.description = "Configuración de simulación base"

    def add_encendido(self, tstart, tend, thrust, Isp, theta, beta):
        if len(self.data_encendidos) < 5:
            self.data_encendidos.append([tstart, tend, thrust, Isp, theta, beta])

    def fill_empty_burns(self):
        while len(self.data_encendidos) < 5:
            placeholder_start = self.periodo + 1000.0 + len(self.data_encendidos) * 10
            self.data_encendidos.append([placeholder_start, 1.0, 0.0, 0.0, 0.0, 0.0])

    def generate_description(self):
        desc = "=== Configuración de Simulación (Objeto) ===\n"
        desc += "\n--- Parámetros de Simulación ---\n"
        desc += f"Periodo: {self.periodo} s\nNúmero de cálculos: {self.num_calc}\nMáximo Step: {self.max_step}\n"
        desc += "\n--- Parámetros de Estado Inicial del Cohete (PIC) ---\n"
        desc += f"Masa inicial (m0): {self.m0} kg\n"
        desc += f"Posición inicial (x,y,z): ({self.x0}, {self.y0}, {self.z0}) m\n"
        desc += f"Velocidad inicial (vx,vy,vz): ({self.vx0}, {self.vy0}, {self.vz0}) m/s\n"
        desc += f"Masa primera etapa (m1): {self.m1} kg\n"
        desc += f"Tiempo separación 1ra etapa (tsep1): {self.tsep1} s\n"
        desc += "\n--- Parámetros de Estado Inicial del Cuerpo Secundario (PIL) ---\n"
        desc += f"Posición inicial (xl,yl,zl): ({self.xl0}, {self.yl0}, {self.zl0}) m\n"
        desc += f"Velocidad inicial (vxl,vyl,vzl): ({self.velxL0}, {self.velyL0}, {self.velzL0}) m/s\n"
        desc += f"\n--- Parámetros de Encendidos (Total Activos: {self.num_encendidos}) ---\n"
        for i in range(self.num_encendidos):
            burn = self.data_encendidos[i]
            desc += f"\n--- Encendido {i} ---\n"
            desc += f"  Tiempo de inicio: {burn[0]} s\n  Duración: {burn[1]} s\n"
            desc += f"  Empuje (Thrust): {burn[2]} N\n  Impulso Específico (Isp): {burn[3]} s\n"
            desc += f"  Ángulos (theta, beta): ({burn[4]}, {burn[5]}) deg\n"
        self.description = desc
        return desc


# -----------------------------------------------------------------
# --- FUNCIONES DE CONFIGURACIÓN (Sin cambios) ---
# -----------------------------------------------------------------

def get_input_with_default(prompt, default_value, data_type=float):
    try:
        user_input = input(f"{prompt} (default = {default_value}):\n--> ")
        if user_input == "":
            return default_value
        else:
            return data_type(user_input)
    except ValueError:
        print(f"Entrada inválida. Usando el valor por defecto: {default_value}")
        return default_value


def config():
    config_obj = ConfigSim()
    print(f"\n=== Parametros de simulacion ===\n")
    config_obj.periodo = get_input_with_default("Ingrese el periodo de simulacion [s]", config_obj.periodo, int)
    config_obj.num_calc = get_input_with_default("Ingrese el numero de calculos en periodo", config_obj.num_calc, int)
    config_obj.max_step = get_input_with_default("Ingrese el maximo de step", config_obj.max_step, float)
    print(f"\n=== Parametros de estado inicial del cohete ===\n")
    config_obj.m0 = get_input_with_default("Ingrese la masa inicial del cohete [kg]", config_obj.m0, float)
    config_obj.x0 = get_input_with_default("Ingrese la posicion inicial en x [m]", config_obj.x0, float)
    config_obj.y0 = get_input_with_default("Ingrese la posicion inicial en y [m]", config_obj.y0, float)
    config_obj.z0 = get_input_with_default("Ingrese la posicion inicial en z [m]", config_obj.z0, float)
    config_obj.vx0 = get_input_with_default("Ingrese la velocidad inicial en x [m/s]", config_obj.vx0, float)
    config_obj.vy0 = get_input_with_default("Ingrese la velocidad inicial en y [m/s]", config_obj.vy0, float)
    config_obj.vz0 = get_input_with_default("Ingrese la velocidad inicial en z [m/s]", config_obj.vz0, float)
    config_obj.m1 = get_input_with_default("Ingrese la masa de la primera etapa [kg]", config_obj.m1, float)
    config_obj.tsep1 = get_input_with_default("Ingrese el tiempo de separación de la 1ra etapa [s]", config_obj.tsep1,
                                              float)
    print(f"\n=== Parametros de los distintos encendidos ===\n")
    config_obj.num_encendidos = get_input_with_default("Ingrese el numero de encendidos (maximo 5)",
                                                       config_obj.num_encendidos, int)
    config_obj.data_encendidos = []
    last_tend = 0.0
    default_burns = {
        0: {'tend': 35.1, 'thrust': 300000.0, 'Isp': 365.6, 'theta': 90.0, 'beta': 0.0},
        1: {'tstart': 280.0, 'tend': 16.1, 'thrust': 630000.0, 'Isp': 450.0, 'theta': 90.0, 'beta': 90.0},
        2: {'tstart': 430.0, 'tend': 4.2, 'thrust': 297970.0, 'Isp': 700.0, 'theta': 90.0, 'beta': 300.0}
    }
    for i in range(config_obj.num_encendidos):
        print(f"\n--- Parametros del encendido {i} ---\n")
        defaults = default_burns.get(i, {})
        if i == 0:
            tstart = 0.0
            tend = get_input_with_default(f"Ingrese duracion del encendido {i} [s]", defaults.get('tend', 10.0), float)
        else:
            suggested_tstart = defaults.get('tstart', last_tend + 10.0)
            tstart = get_input_with_default(f"Ingrese tiempo de inicio del encendido {i} [s]", suggested_tstart, float)
            tend = get_input_with_default(f"Ingrese duracion del encendido {i} [s]", defaults.get('tend', 10.0), float)
        thrust = get_input_with_default(f"Ingrese potencia (Thrust) del encendido {i} [N]", defaults.get('thrust', 0.0),
                                        float)
        Isp = get_input_with_default(f"Ingrese Impulso Específico (Isp) del encendido {i} [s]",
                                     defaults.get('Isp', 0.0), float)
        theta = get_input_with_default(f"Ingrese angulo theta del encendido {i} [deg]", defaults.get('theta', 0.0),
                                       float)
        beta = get_input_with_default(f"Ingrese angulo beta del encendido {i} [deg]", defaults.get('beta', 0.0), float)
        config_obj.add_encendido(tstart, tend, thrust, Isp, theta, beta)
        last_tend = tstart + tend
    config_obj.fill_empty_burns()
    config_obj.generate_description()
    return config_obj


def test_config():
    config_obj = ConfigSim()
    config_obj.periodo = 2000
    config_obj.num_calc = 1000
    config_obj.max_step = 0.5
    config_obj.m0 = 1000.0
    config_obj.x0 = 6_357_000.0
    config_obj.y0 = 0.0
    config_obj.z0 = 0.0
    config_obj.vx0 = 0.0
    config_obj.vy0 = 0.0
    config_obj.vz0 = 0.0
    config_obj.m1 = 20.0
    config_obj.tsep1 = 2.0
    config_obj.num_encendidos = 3
    config_obj.data_encendidos = []
    config_obj.add_encendido(tstart=0.0, tend=35.1, thrust=300000.0, Isp=365.61, theta=90.0, beta=0.0)
    config_obj.add_encendido(tstart=280.0, tend=16.1, thrust=630000.0, Isp=450.0, theta=90.0, beta=90.0)
    config_obj.add_encendido(tstart=430.0, tend=4.2, thrust=297970.0, Isp=700.0, theta=90.0, beta=300.0)
    config_obj.fill_empty_burns()
    config_obj.generate_description()
    config_obj.description = "=== Configuración de TEST Automático ===\n" + config_obj.description
    return config_obj



def config_from_sim_silent(time0, base_sim_obj, duration=None):
    """
    Crea un ConfigSim a partir de un estado de una simulación anterior
    SIN solicitar input al usuario (para optimizadores automáticos).
    
    Args:
        time0 (int): Índice del estado inicial.
        base_sim_obj: Objeto de simulación base.
        duration (float, optional): Duración de la nueva fase. Si es None, usa default (llegada a Luna).
    """
    config_obj = ConfigSim()

    # 1. Cargar estado
    try:
        config_obj.x0 = base_sim_obj.posx[time0]
        config_obj.y0 = base_sim_obj.posy[time0]
        config_obj.z0 = base_sim_obj.posz[time0]
        config_obj.vx0 = base_sim_obj.velx[time0]
        config_obj.vy0 = base_sim_obj.vely[time0]
        config_obj.vz0 = base_sim_obj.velz[time0]
        config_obj.m0 = base_sim_obj.mass[time0]
        config_obj.xl0 = base_sim_obj.poslx[time0]
        config_obj.yl0 = base_sim_obj.posly[time0]
        config_obj.zl0 = base_sim_obj.poslz[time0]
        config_obj.velxL0 = base_sim_obj.vellx[time0]
        config_obj.velyL0 = base_sim_obj.velly[time0]
        config_obj.velzL0 = base_sim_obj.vellz[time0]
        config_obj.m1 = 0.0
        config_obj.tsep1 = 0.0
    except IndexError:
        print(f"Error: Índice {time0} fuera de rango.")
        return None
    except Exception as e:
        print(f"Error al cargar estado: {e}")
        return None

    # 2. Configuración por defecto
    if duration is not None:
        config_obj.periodo = float(duration)
        # Ajustar num_calc para mantener resolución decente
        # step ~ 1s a 10s
        config_obj.num_calc = max(100, int(config_obj.periodo / 10.0))
        config_obj.max_step = 60.0
    else:
        config_obj.periodo = 400000.0  # Default viaje
        config_obj.num_calc = 2000
        config_obj.max_step = 200.0
    
    # 3. Sin encendidos iniciales (el optimizador los agregará)
    config_obj.num_encendidos = 0
    config_obj.data_encendidos = []
    config_obj.fill_empty_burns()
    
    config_obj.generate_description()
    config_obj.description = f"=== Config Silenciosa (base='{base_sim_obj.name}', t_idx={time0}) ===\n" + config_obj.description
    return config_obj


def config_from_sim(time0, base_sim_obj):

    """
    Crea un NUEVO ConfigSim a partir de un estado de una simulación anterior
    y PREGUNTA al usuario por los nuevos parámetros de vuelo.
    """
    config_obj = ConfigSim()

    # 1. Cargar estado desde la simulación base
    try:
        config_obj.x0 = base_sim_obj.posx[time0]
        config_obj.y0 = base_sim_obj.posy[time0]
        config_obj.z0 = base_sim_obj.posz[time0]
        config_obj.vx0 = base_sim_obj.velx[time0]
        config_obj.vy0 = base_sim_obj.vely[time0]
        config_obj.vz0 = base_sim_obj.velz[time0]
        config_obj.m0 = base_sim_obj.mass[time0]
        config_obj.xl0 = base_sim_obj.poslx[time0]
        config_obj.yl0 = base_sim_obj.posly[time0]
        config_obj.zl0 = base_sim_obj.poslz[time0]
        config_obj.velxL0 = base_sim_obj.vellx[time0]
        config_obj.velyL0 = base_sim_obj.velly[time0]
        config_obj.velzL0 = base_sim_obj.vellz[time0]
        config_obj.m1 = 0.0
        config_obj.tsep1 = 0.0
    except IndexError:
        print(f"Error: El tiempo (índice) {time0} está fuera del rango de la simulación base.")
        return None
    except Exception as e:
        print(f"Error al cargar datos desde la simulación base: {e}")
        return None

    # 2. Solicitud de los nuevos parámetros de simulación
    print(f"\n=== Ingrese los nuevos Parametros de Simulacion (desde t={time0}) ===")
    config_obj.periodo = int(input(f"Ingrese el nuevo periodo de simulacion [s] (int):\n--> "))
    config_obj.num_calc = int(input(f"Ingrese el nuevo numero de calculos en periodo (int):\n--> "))
    config_obj.max_step = float(input(f"Ingrese el nuevo maximo de step (float):\n--> "))

    # 3. Configuración de los nuevos encendidos
    print(f"\n=== Configuracion de Encendidos para la Nueva Fase ===")
    config_obj.num_encendidos = int(input(f"Ingrese el numero de encendidos (maximo 5):\n--> "))
    config_obj.data_encendidos = []

    for i in range(config_obj.num_encendidos):
        print(f"\n--- Parametros del nuevo encendido {i} ---\n")
        if i == 0:
            tstart = 0.0
            print("El tiempo de inicio del primer encendido se ha fijado en 0.0 s.")
            tend = float(input(f"Ingrese la duracion del encendido {i} [s] (float):\n--> "))
        else:
            tstart = float(input(f"Ingrese el tiempo de inicio del encendido {i} [s] (float):\n--> "))
            tend = float(input(f"Ingrese la duracion del encendido {i} [s] (float):\n--> "))
        thrust = float(input(f"Ingrese la potencia del encendido {i} [N] (float):\n--> "))
        Isp = float(input(f"Ingrese el Impulso Específico (Isp) del encendido {i} [s] (float):\n--> "))
        theta = float(input(f"Ingrese el angulo theta de disparo del encendido {i} [deg] (float):\n--> "))
        beta = float(input(f"Ingrese el angulo beta de disparo del encendido {i} [deg] (float):\n--> "))
        config_obj.add_encendido(tstart, tend, thrust, Isp, theta, beta)

    # 4. Finalizar y retornar
    config_obj.fill_empty_burns()
    config_obj.generate_description()

    # [MODIFICADO] La descripción ahora es más genérica
    desc_prefix = f"=== Plantilla Iterativa (base='{base_sim_obj.name}', t_idx={time0}) ===\n"
    config_obj.description = desc_prefix + config_obj.description
    return config_obj


def config_manual():
    config_obj = ConfigSim()
    config_obj.periodo = 8000
    config_obj.num_calc = 2000
    config_obj.max_step = 0.5
    config_obj.m0 = 9000.0
    config_obj.x0 = 6371000.0
    config_obj.y0 = 0.0
    config_obj.z0 = 0.0
    config_obj.vx0 = 0.0
    config_obj.vy0 = 1000.0
    config_obj.vz0 = 0.0
    config_obj.m1 = 100.0
    config_obj.tsep1 = 2.0
    config_obj.xl0 = 384_400_000.0
    config_obj.yl0 = 0.0
    config_obj.zl0 = 0.0
    config_obj.velxL0 = 0.0
    config_obj.velyL0 = 1022.0
    config_obj.velzL0 = 0.0
    config_obj.num_encendidos = 2
    config_obj.data_encendidos = []
    config_obj.add_encendido(tstart=0.0, tend=60.0, thrust=450000.0, Isp=500.0, theta=90.0, beta=0.0)
    config_obj.add_encendido(tstart=580.0, tend=27.5, thrust=500000.0, Isp=600.0, theta=90.0, beta=90.0)
    config_obj.fill_empty_burns()
    config_obj.generate_description()
    config_obj.description = "=== Configuración Manual (Predefinida) ===\n" + config_obj.description
    return config_obj


def config_high_dv_orbit():
    """
    Configuración predefinida: Órbita circular a 100 km de altura.
    Alta capacidad de Delta-V (mucha masa de combustible).
    """
    config_obj = ConfigSim()
    config_obj.periodo = 6000 # Un par de orbitas
    config_obj.num_calc = 1500
    config_obj.max_step = 0.5
    
    # --- Parámetros de Órbita ---
    # Altura 100 km
    r_orbit = 6371000.0 + 100000.0 
    # Velocidad circular v = sqrt(mu / r) -> mu_earth approx 3.986e14
    v_orbit = np.sqrt(3.986004418e14 / r_orbit) 
    
    config_obj.x0 = r_orbit
    config_obj.y0 = 0.0
    config_obj.z0 = 0.0
    
    config_obj.vx0 = 0.0
    config_obj.vy0 = v_orbit
    config_obj.vz0 = 0.0
    
    # --- Parámetros del Cohete (High Delta-V) ---
    # Masa total alta, con mucha proporción de combustible
    # Supongamos 20 toneladas con estructura muy eficiente
    config_obj.m0 = 20000.0 
    config_obj.m1 = 1000.0 # Masa seca (cascarón) baja
    config_obj.tsep1 = 999999.0 # No separar etapa en esta simulación simple
    
    # --- Parámetros de la Luna (Estándar) ---
    config_obj.xl0 = 384_400_000.0
    config_obj.yl0 = 0.0
    config_obj.zl0 = 0.0
    config_obj.velxL0 = 0.0
    config_obj.velyL0 = 1022.0
    config_obj.velzL0 = 0.0
    
    # --- Encendidos ---
    # Iniciamos SIN encendidos (coasting en órbita)
    config_obj.num_encendidos = 0
    config_obj.data_encendidos = []
    config_obj.fill_empty_burns()
    
    config_obj.generate_description()
    config_obj.description = "=== Configuración: Órbita 100km (High Delta-V) ===\n" + config_obj.description
    return config_obj


def config_400km_moon_plane():
    """
    Configuración predefinida: Órbita circular a 400 km de altura.
    Plano de la Luna (z=0).
    """
    config_obj = ConfigSim()
    config_obj.periodo = 6000  # Un par de orbitas
    config_obj.num_calc = 1500
    config_obj.max_step = 0.5

    # --- Parámetros de Órbita ---
    # Altura 400 km
    r_orbit = 6371000.0 + 400000.0
    # Velocidad circular v = sqrt(mu / r)
    v_orbit = np.sqrt(3.986004418e14 / r_orbit)

    config_obj.x0 = r_orbit
    config_obj.y0 = 0.0
    config_obj.z0 = 0.0

    config_obj.vx0 = 0.0
    config_obj.vy0 = v_orbit
    config_obj.vz0 = 0.0

    # --- Parámetros del Cohete ---
    config_obj.m0 = 5600.0
    config_obj.m1 = 20.0
    config_obj.tsep1 = 999999.0

    # --- Parámetros de la Luna (Estándar) ---
    config_obj.xl0 = 384_400_000.0
    config_obj.yl0 = 0.0
    config_obj.zl0 = 0.0
    config_obj.velxL0 = 0.0
    config_obj.velyL0 = 1022.0
    config_obj.velzL0 = 0.0

    # --- Encendidos ---
    # Sin encendidos (órbita estable)
    config_obj.num_encendidos = 0
    config_obj.data_encendidos = []
    config_obj.fill_empty_burns()

    config_obj.generate_description()
    config_obj.description = "=== Configuración: Órbita 400km (Plano Luna) ===\n" + config_obj.description
    return config_obj


# -----------------------------------------------------------------
# --- LÓGICA DE LOTES REFACTORIZADA ---
# -----------------------------------------------------------------

def _configure_batch_sweep():
    """
    Función auxiliar interna. Pregunta al usuario QUÉ parámetro variar y
    en QUÉ rango.

    Retorna (param_name, param_loc, values_to_sweep) o (None, None, None)
    """
    print("\n--- Configuración del Parámetro a Variar ---")

    PIC_params = ["m0", "x0", "y0", "z0", "vx0", "vy0", "vz0", "m1", "tsep1",
                  "xl0", "yl0", "zl0", "velxL0", "velyL0", "velzL0",
                  "periodo", "num_calc", "max_step"]
    ENC_params = ["tstart", "tend", "thrust", "Isp", "theta", "beta"]

    param_name = ""
    param_loc = None

    try:
        param_type = int(input(
            "\n¿Qué tipo de parámetro desea variar?\n1. Parámetro General (PIC, PIL, Sim)\n2. Parámetro de Encendido\n--> "))

        if param_type == 1:
            print("\nParámetros Generales disponibles:")
            for i, p in enumerate(PIC_params):
                print(f"  {i}. {p}")
            choice = int(input("Seleccione el número del parámetro: "))
            if 0 <= choice < len(PIC_params):
                param_name = PIC_params[choice]
                param_loc = ("PIC", param_name)
            else:
                raise ValueError("Índice de parámetro fuera de rango.")

        elif param_type == 2:
            burn_index = int(input("¿Qué número de encendido (0-4) desea modificar?\n--> "))
            if not (0 <= burn_index <= 4):
                raise ValueError("Índice de encendido fuera de rango (debe ser 0-4).")
            print(f"\nParámetros del Encendido {burn_index} disponibles:")
            for i, p in enumerate(ENC_params):
                if burn_index == 0 and p == "tstart":
                    print(f"  {i}. {p} (No se puede variar)")
                else:
                    print(f"  {i}. {p}")
            choice = int(input("Seleccione el número del parámetro: "))
            if not (0 <= choice < len(ENC_params)):
                raise ValueError("Índice de parámetro de encendido fuera de rango.")
            param_name_short = ENC_params[choice]
            if burn_index == 0 and param_name_short == "tstart":
                raise ValueError("Error: tstart del encendido 0 está fijado en 0.0.")
            param_name = f"Encendido_{burn_index}_{param_name_short}"
            param_loc = ("ENC", burn_index, choice)

        else:
            raise ValueError("Tipo de parámetro no válido.")

        print(f"\nParámetro seleccionado: {param_name}")
        start_val = float(input("Ingrese el valor INICIAL para el barrido: "))
        end_val = float(input("Ingrese el valor FINAL para el barrido: "))
        num_steps = 10

        values_to_sweep = np.linspace(start_val, end_val, num_steps)

        print(f"\nSe generarán {num_steps} configuraciones variando '{param_name}'.")
        print("Valores a simular:")
        print(np.round(values_to_sweep, 3))

        confirm = input("¿Desea continuar? (s/n): ").strip().lower()
        if confirm != 's':
            print("Operación cancelada.")
            return None, None, None  # Cancelar

        return param_name, param_loc, values_to_sweep

    except ValueError as e:
        print(f"Entrada inválida: {e}. Cancelando lote.")
        return None, None, None
    except Exception as e:
        print(f"Un error inesperado ocurrió: {e}. Cancelando lote.")
        return None, None, None


def config_batch():
    """
    Crea un lote de simulaciones desde CERO.
    """
    print("\n======================================")
    print("=== Configuración de Simulación por Lotes ===")
    print("======================================")

    print("\nSeleccione la configuración 'plantilla' para el lote:")
    print("1. Configuración Manual (Paso a paso)")
    print("2. Configuración Predefinida (config_manual)")
    print("3. Configuración de Test (test_config)")

    base_config_obj = None
    try:
        base_choice = int(input("--> "))
        if base_choice == 1:
            base_config_obj = config()
        elif base_choice == 2:
            base_config_obj = config_manual()
            print("...Usando 'config_manual' como plantilla.")
        elif base_choice == 3:
            base_config_obj = test_config()
            print("...Usando 'test_config' como plantilla.")
        else:
            raise ValueError("Opción no válida.")
    except Exception as e:
        print(f"Error al seleccionar la plantilla: {e}")
        return []

    param_name, param_loc, values_to_sweep = _configure_batch_sweep()
    if param_name is None:
        return []

    list_of_configs = []
    for i, val in enumerate(values_to_sweep):
        mod_config_obj = copy.deepcopy(base_config_obj)

        if param_loc[0] == "PIC":
            setattr(mod_config_obj, param_loc[1], val)
        elif param_loc[0] == "ENC":
            mod_config_obj.data_encendidos[param_loc[1]][param_loc[2]] = val

        desc_prefix = f"=== LOTE {i + 1}/{len(values_to_sweep)}: {param_name} = {val:.4e} ===\n"
        mod_config_obj.generate_description()
        mod_config_obj.description = desc_prefix + mod_config_obj.description

        list_of_configs.append(mod_config_obj)

    print(f"Se han generado {len(list_of_configs)} configuraciones de lote.")
    return list_of_configs


def config_batch_from_template(base_config_obj):
    """
    Crea un lote de simulaciones usando una PLANTILLA ya existente.
    """
    print("\n===========================================")
    print("=== Configuración de Lote desde Plantilla ===")
    print("===========================================")
    print("La simulación que acaba de configurar se usará como plantilla.")

    param_name, param_loc, values_to_sweep = _configure_batch_sweep()
    if param_name is None:
        return []

    list_of_configs = []
    for i, val in enumerate(values_to_sweep):
        mod_config_obj = copy.deepcopy(base_config_obj)

        if param_loc[0] == "PIC":
            setattr(mod_config_obj, param_loc[1], val)
        elif param_loc[0] == "ENC":
            mod_config_obj.data_encendidos[param_loc[1]][param_loc[2]] = val

        desc_prefix = f"=== LOTE {i + 1}/{len(values_to_sweep)}: {param_name} = {val:.4e} ===\n"
        # Preserva la descripción base (que incluye "Iterativa desde...")
        mod_config_obj.description = desc_prefix + base_config_obj.description

        list_of_configs.append(mod_config_obj)

    print(f"Se han generado {len(list_of_configs)} configuraciones de lote iterativo.")
    return list_of_configs