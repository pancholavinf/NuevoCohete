import numpy as np
from new_sim import ConfigSim
from modelo_3d import R_earth, mu_earth

def find_moon_intercept(base_config, r_target=None):
    """
    Calcula el encendido necesario para elevar el apogeo hasta la distancia 
    objetivo (default: Luna aprox 384,400 km), desde la posición y estado ACTUAL.
    
    NO asume que estamos en el perigeo. Resuelve numéricamente la velocidad
    requerida manteniendo la dirección de velocidad actual (quemado tangencial).
    """
    print("\n=== CALCULADORA TLI (SOLVER NUMÉRICO) ===")
    
    # Objetivo: Apogeo
    if r_target is not None:
        r_apogee_target = float(r_target)
        print(f"Objetivo de Apogeo personalizado: {r_apogee_target/1000:.1f} km")
    else:
        r_apogee_target = 384_400_000.0
        print(f"Objetivo de Apogeo por defecto (Luna Mean): {r_apogee_target/1000:.1f} km")

    print("Calculando maniobra...")

    # Data inicial
    r_vec = np.array([base_config.x0, base_config.y0, base_config.z0])
    v_vec = np.array([base_config.vx0, base_config.vy0, base_config.vz0])
    
    r_mag = np.linalg.norm(r_vec)
    v_mag = np.linalg.norm(v_vec)
    
    if r_mag < R_earth:
        print("[ERROR] El cohete está bajo la superficie terrestre.")
        return None
        
    if v_mag == 0:
        print("[ERROR] Velocidad cero, no se puede definir dirección tangencial.")
        return None

    # Objetivo: Apogeo = Distancia Luna
    r_apogee_target = 384_400_000.0 
    
    # Dirección de quemado: Tangencial (progrado)
    v_dir = v_vec / v_mag
    
    # Función para calcular apogeo dado una magnitud de velocidad v
    # manteniendo la posicion r y la dirección v_dir constantes.
    def get_apogee(vel_scalar):
        # Estado de prueba
        v_test = v_dir * vel_scalar
        v_sq = vel_scalar**2
        
        # Energía específica
        # epsilon = v^2/2 - mu/r
        specific_energy = (v_sq / 2.0) - (mu_earth / r_mag)
        
        if specific_energy >= 0:
            return float('inf') # Escape o parabólica
            
        # Semieje mayor
        # a = -mu / 2*epsilon
        a = -mu_earth / (2.0 * specific_energy)
        
        # Excentricidad
        # e = sqrt(1 + 2*epsilon*h^2 / mu^2)
        # h = |r x v|
        h_vec = np.cross(r_vec, v_test)
        h_sq = np.dot(h_vec, h_vec)
        
        term = 1.0 + (2.0 * specific_energy * h_sq) / (mu_earth**2)
        if term < 0: term = 0 # Error numérico chiquito
        e = np.sqrt(term)
        
        # Apogeo = a(1+e)
        r_a = a * (1.0 + e)
        return r_a

    # Solver (Bisección simple)
    # Buscamos v tal que get_apogee(v) = r_apogee_target
    
    # Límites
    v_low = 0.0
    v_high = np.sqrt(2.0 * mu_earth / r_mag) * 0.999 # Justo debajo de escape
    
    # Check rápido
    if get_apogee(v_mag) >= r_apogee_target:
        print("[AVISO] La órbita actual ya alcanza o supera la distancia lunar.")
        delta_v = 0.0
        v_final = v_mag
    else:
        # Búsqueda
        found = False
        for _ in range(50): # 50 iteraciones es suficiente precisión
            v_mid = (v_low + v_high) / 2.0
            apo = get_apogee(v_mid)
            
            if apo < r_apogee_target:
                # Necesitamos más velocidad
                v_low = v_mid
            else:
                # Nos pasamos (o es infinito)
                v_high = v_mid
                
            if abs(apo - r_apogee_target) < 1000.0: # 1km precisión
                found = True
                break
        
        v_final = v_high # Usamos el high para asegurar llegar
        delta_v = v_final - v_mag

    print(f"Velocidad actual: {v_mag:.2f} m/s")
    print(f"Velocidad requerida: {v_final:.2f} m/s")
    print(f"Delta-V necesario: {delta_v:.2f} m/s")
    
    # Calculo de Orientación (Theta/Beta del vector v actual/progrado)
    # Theta (Zenit / Latitud esférica desde Z): arccos(vz / v_mag)
    theta_rad = np.arccos(v_dir[2])
    # Beta (Azimut plano XY): arctan2(vy, vx)
    beta_rad = np.arctan2(v_dir[1], v_dir[0])
    
    theta_deg = np.degrees(theta_rad)
    beta_deg = np.degrees(beta_rad)
    if beta_deg < 0: beta_deg += 360.0
        
    print(f"Orientación de disparo (Tangencial): Theta={theta_deg:.2f}°, Beta={beta_deg:.2f}°")

    # Calculo Propelente (Tsiolkovsky)
    thrust = 500000.0  # N
    Isp = 450.0  # s
    g0 = 9.80665
    
    m0 = base_config.m0
    mf = m0 / np.exp(delta_v / (Isp * g0))
    m_prop_needed = m0 - mf
    
    mass_flow = thrust / (g0 * Isp)
    duration = m_prop_needed / mass_flow
    
    print(f"Masa propelente estimada: {m_prop_needed:.2f} kg")
    print(f"Duración de encendido estimada: {duration:.2f} s")
    
    # --- DIAGNÓSTICO FINAL ---
    # Recalcular elementos orbitales con la velocidad final para mostrar al usuario
    v_vec_final = v_dir * v_final
    specific_energy_final = (v_final**2 / 2.0) - (mu_earth / r_mag)
    if specific_energy_final < 0:
        a_final = -mu_earth / (2.0 * specific_energy_final)
        h_vec = np.cross(r_vec, v_vec_final)
        h_sq = np.dot(h_vec, h_vec)
        e_final = np.sqrt(1.0 + (2.0 * specific_energy_final * h_sq) / (mu_earth**2))
        
        r_apogee_final = a_final * (1.0 + e_final)
        r_perigee_final = a_final * (1.0 - e_final)
        
        print(f"\n--- Diagnóstico de Órbita Resultante ---")
        print(f"Apogeo Esperado: {r_apogee_final/1000:.1f} km (Target: {r_apogee_target/1000:.0f} km)")
        print(f"Perigeo Esperado: {r_perigee_final/1000:.1f} km")
        print(f"Excentricidad: {e_final:.4f}")
        print(f"Semieje mayor (a): {a_final/1000:.1f} km")
    else:
        print("\n--- Diagnóstico: Trayectoria de Escape/Parabólica ---")
    
    return {
        'tstart': 0.0,
        'tend': duration,
        'thrust': thrust,
        'Isp': Isp,
        'theta': theta_deg,
        'beta': beta_deg,
        'mass_needed': m_prop_needed,
        'delta_v': delta_v
    }


def calculate_loi(sim_obj):
    """
    Calcula el encendido necesario para Inserción Orbital Lunar (LOI).
    1. Busca el punto de máxima cercanía a la Luna (Perilunio).
    2. Calcula el vector de velocidad relativa.
    3. Calcula el Delta-V para circularizar a esa altura.
    """
    print("\n=== CALCULADORA LOI (LUNAR ORBIT INSERTION) ===")
    
    # 1. Encontrar Perilunio
    # Calcular distancia en todos los puntos
    # sim_obj.posx es un array de posiciones X del cohete
    # sim_obj.poslx es un array de posiciones X de la Luna
    
    # Diferencias
    dx = sim_obj.posx - sim_obj.poslx
    dy = sim_obj.posy - sim_obj.posly
    dz = sim_obj.posz - sim_obj.poslz
    
    dist_sq = dx**2 + dy**2 + dz**2
    min_dist_idx = np.argmin(dist_sq)
    min_dist = np.sqrt(dist_sq[min_dist_idx])
    
    print(f"Perilunio encontrado en t_idx={min_dist_idx}")
    print(f"Distancia mínima a la Luna: {min_dist/1000:.2f} km")
    
    # Validar esfera de influencia (aproximada ~66,000 km, pero damos margen)
    # [MODIFICADO] Si se llama desde el optimizador, no queremos input() bloqueante.
    # Asumimos que si sim_obj tiene un atributo 'silent' es True, evitamos inputs.
    is_silent = getattr(sim_obj, 'silent', False)

    if min_dist > 50000000.0: # 50,000 km
        print("[ADVERTENCIA] El punto más cercano está muy lejos de la Luna.")
        print("La circularización resultará en una órbita extremadamente alta.")
        if not is_silent:
            if input("¿Continuar de todos modos? (s/n): ").lower() != 's':
                return None
        else:
            # En modo silencioso (optimizador), si está muy lejos, descartamos (return None)
            return None

    # 2. Estado Relativo en Perilunio
    # Posición relativa vector
    r_rel_vec = np.array([dx[min_dist_idx], dy[min_dist_idx], dz[min_dist_idx]])
    
    # Velocidad absoluta cohete vs luna
    vx_rel = sim_obj.velx[min_dist_idx] - sim_obj.vellx[min_dist_idx]
    vy_rel = sim_obj.vely[min_dist_idx] - sim_obj.velly[min_dist_idx]
    vz_rel = sim_obj.velz[min_dist_idx] - sim_obj.vellz[min_dist_idx]
    v_rel_vec = np.array([vx_rel, vy_rel, vz_rel])
    
    v_rel_mag = np.linalg.norm(v_rel_vec)
    
    print(f"Velocidad relativa en Perilunio: {v_rel_mag:.2f} m/s")
    
    # 3. Velocidad Circular Objetivo
    # v_circ = sqrt(mu_moon / r)
    from modelo_3d import mu_moon
    
    v_circ = np.sqrt(mu_moon / min_dist)
    print(f"Velocidad circular requerida: {v_circ:.2f} m/s")
    
    # 4. Delta-V (Retrograde Burn)
    # Asumimos que queremos frenar para igualar v_circ.
    # El vector de velocidad actual es v_rel_vec.
    # El vector objetivo tiene magnitud v_circ y dirección v_rel_vec (tangencial).
    # O sea, solo cambiamos la magnitud.
    
    delta_v = v_circ - v_rel_mag
    # delta_v será negativo si vamos muy rápido (hiperbola/parabola) y tenemos que frenar.
    
    print(f"Delta-V necesario: {delta_v:.2f} m/s")
    
    if delta_v > 0:
        print("[INFO] La velocidad actual es MENOR a la circular. Se requiere acelerar (posiblemente órbita elíptica sub-circular?).")
        # Esto pasa si ya fuimos capturados y el apolunio está lejos, o si estamos cayendo lento.
    
    # 5. Parametros de Quemado
    # Dirección: Tangencial. Si delta_v < 0, es "retrograde" (opuesto a velocidad).
    # Si delta_v > 0, es "prograde" (a favor de velocidad).
    
    # Abs delta_v para Tsiolkovsky
    abs_dv = abs(delta_v)
    
    # Orientación del vector velocidad
    if v_rel_mag == 0:
        # Caso patológico
        return None
        
    # Vector unitario velocidad
    v_hat = v_rel_vec / v_rel_mag
    
    # Vector de empuje
    # Si delta_v es negativo (frenar), empujamos EN CONTRA del movimiento -> Thrust vector opposite to V -> same direction as -V?
    # NO. El motor empuja hacia "adelante" del cohete. Si queremos frenar, orientamos el cohete hacia ATRAS (retrogrado).
    # Theta/Beta definen hacia dónde apunta la tobera (y por tanto el empuje).
    # Si queremos aplicar fuerza F opuesta a V: F = -k * V.
    # Entonces el empuje va en dirección -V.
    
    target_thrust_dir = v_hat if delta_v > 0 else -v_hat
    
    # Calcular Theta/Beta de target_thrust_dir
    # Theta (Zenit / Latitud esférica desde Z): arccos(vz / mag)
    theta_rad = np.arccos(target_thrust_dir[2]) # target_thrust_dir es unitario
    # Beta (Azimut plano XY): arctan2(vy, vx)
    beta_rad = np.arctan2(target_thrust_dir[1], target_thrust_dir[0])
    
    theta_deg = np.degrees(theta_rad)
    beta_deg = np.degrees(beta_rad)
    if beta_deg < 0: beta_deg += 360.0
    
    print(f"Orientación de quemado ({'Retrogrado' if delta_v < 0 else 'Progrado'}): Theta={theta_deg:.2f}°, Beta={beta_deg:.2f}°")
    
    # Tsiolkovsky
    thrust = 500000.0  # N
    Isp = 450.0  # s
    g0 = 9.80665
    
    m0 = sim_obj.mass[min_dist_idx]
    mf = m0 / np.exp(abs_dv / (Isp * g0))
    m_prop_needed = m0 - mf
    
    mass_flow = thrust / (g0 * Isp)
    duration = m_prop_needed / mass_flow
    
    print(f"Masa propelente: {m_prop_needed:.2f} kg")
    print(f"Duración: {duration:.2f} s")

    return {
        'time_idx': min_dist_idx, # Indice donde ocurre el evento
        'tstart': 0.0, # Relativo a la nueva fase que empezará en time_idx
        'tend': duration,
        'thrust': thrust,
        'Isp': Isp,
        'theta': theta_deg,
        'beta': beta_deg,
        'delta_v': delta_v,
        'min_dist': min_dist # [MODIFICADO] Agregado para el optimizador
    }


# --- CLASES Y FUNCIONES DE OPTIMIZACIÓN ---

class SimResultWrapper:
    """Wrapper para hacer compatible la tupla de calc_sim con calculate_loi."""
    def __init__(self, res_tuple):
        self.tout = res_tuple[0]
        self.posx = res_tuple[1]
        self.posy = res_tuple[2]
        self.posz = res_tuple[3]
        self.velx = res_tuple[4]
        self.vely = res_tuple[5]
        self.velz = res_tuple[6]
        self.mass = res_tuple[7]
        # Skip alt
        self.poslx = res_tuple[9]
        self.posly = res_tuple[10]
        self.poslz = res_tuple[11]
        self.vellx = res_tuple[12]
        self.velly = res_tuple[13]
        self.vellz = res_tuple[14]
        
        self.silent = True # Flag para evitar inputs


def find_approximate_launch_window(base_sim_obj, duration_seconds=6000):
    """
    Escanea la órbita actual (base_sim_obj) para encontrar el índice de tiempo
    donde la geometría Tierra-Cohete-Luna es óptima para una transferencia Hohmann.
    
    Heurística:
    1. Estimar tiempo de vuelo (TOF) Hohmann.
    2. Para cada punto de la órbita de parking:
       - Predecir posición futura de la Luna en t + TOF.
       - El punto óptimo de quema (Perigeo Transferencia) debe estar
         OPUESTO (180 grados) a la posición futura de la Luna (Apogeo Transferencia).
    """
    print("\n[HEURISTICA] Escaneando órbita para ventana de lanzamiento aproximada...")
    
    from modelo_3d import mu_earth, mu_moon
    
    t_base = base_sim_obj.tout
    
    # Validar que tengamos datos suficientes
    if len(t_base) < 10:
        return 0
        
    start_time = t_base[0]
    end_time_limit = start_time + duration_seconds
    
    # 1. Estimar TOF Hohmann (aprox)
    # r_park approx (usamos el primer punto)
    r_vec = np.array([base_sim_obj.posx[0], base_sim_obj.posy[0], base_sim_obj.posz[0]])
    r_park = np.linalg.norm(r_vec)
    r_moon_orbit = 384400000.0
    
    a_trans = (r_park + r_moon_orbit) / 2.0
    period_trans = 2 * np.pi * np.sqrt(a_trans**3 / mu_earth)
    tof_hohmann = period_trans / 2.0
    
    print(f"[HEURISTICA] TOF estimado: {tof_hohmann:.0f} s ({tof_hohmann/3600:.1f} h)")
    
    # 2. Escanear
    best_idx = 0
    min_angle_error = float('inf')
    
    # Paso de escaneo (no necesitamos ir segundo a segundo para la heurística)
    # Escaneamos cada ~60s o cada 10 indices
    step = 10 
    
    for i in range(0, len(t_base), step):
        t_now = t_base[i]
        if t_now > end_time_limit:
            break
            
        # Posición actual del cohete
        r_rocket = np.array([base_sim_obj.posx[i], base_sim_obj.posy[i], base_sim_obj.posz[i]])
        norm_r = np.linalg.norm(r_rocket)
        if norm_r == 0: continue
        
        # Posición actual de la Luna y velocidad angular estimada
        r_moon = np.array([base_sim_obj.poslx[i], base_sim_obj.posly[i], base_sim_obj.poslz[i]])
        v_moon = np.array([base_sim_obj.vellx[i], base_sim_obj.velly[i], base_sim_obj.vellz[i]]) # Asumiendo que tenemos vellx...
        
        # Si no tenemos velocidad de la luna (depende de la simulación), estimamos
        # Asumiendo órbita circular simple de la Luna si faltan datos, pero new_sim suele guardarlos.
        # Fallback: Omega promedio
        omega_moon_avg = 2.6617e-6 # rad/s
        
        # Predecir angulo de la luna en futuro
        # Vector actual de luna
        # Rotamos el vector r_moon en el plano orbital (aprox XY) por omega * TOF
        
        # Angulo actual Luna en plano XY
        angle_moon_now = np.arctan2(r_moon[1], r_moon[0])
        angle_moon_future = angle_moon_now + omega_moon_avg * tof_hohmann
        
        # Posición unitaria predicha de la Luna (solo dirección importa)
        # Asumimos plano XY dominante
        dir_moon_future = np.array([np.cos(angle_moon_future), np.sin(angle_moon_future), 0.0])
        
        # Dirección del cohete actual (unitario)
        dir_rocket = r_rocket / norm_r
        # Queremos que dir_rocket sea opuesto a dir_moon_future
        # Es decir, dot(dir_rocket, dir_moon_future) debe ser -1
        # O equivalentemente, el ángulo entre ellos debe ser 180 deg
        
        # Calculamos "Desviación de 180 grados"
        # Dot product: cos(theta)
        dot_val = np.dot(dir_rocket, dir_moon_future)
        # Queremos dot_val cerca de -1
        
        # Error = distancia a -1
        # O ángulo absoluto a 180
        # error score: cuanto más bajo mejor
        # dot = -1 => error = 0
        # dot = 1 => error = 2
        score = dot_val + 1.0 
        
        if score < min_angle_error:
            min_angle_error = score
            best_idx = i
            
    print(f"[HEURISTICA] Mejor ventana detectada @ T={t_base[best_idx]:.1f}s (Score={min_angle_error:.4f})")
    
    return best_idx






    print(f"[HEURISTICA] Mejor ventana detectada @ T={t_base[best_idx]:.1f}s (Score={min_angle_error:.4f})")
    
    return best_idx


def calculate_encounter_prediction(sim_obj, time_index, is_stand_alone=False):
    """
    Calcula los parámetros de predicción de encuentro lunar siguiendo estrictamente
    los pasos definidos por el usuario.
    
    Retorna un diccionario con todos los valores calculados.
    """
    if is_stand_alone:
        # Si es un objeto DataWrapper o similar
        r_ship_vec = np.array([sim_obj.posx[time_index], sim_obj.posy[time_index], sim_obj.posz[time_index]])
        v_ship_vec = np.array([sim_obj.velx[time_index], sim_obj.vely[time_index], sim_obj.velz[time_index]])
        r_moon_vec = np.array([sim_obj.poslx[time_index], sim_obj.posly[time_index], sim_obj.poslz[time_index]])
    else:
        # Si es el objeto de Simulación normal
        # Verificamos si es una tupla o objeto
        try:
             # Intento de acceso directo (objeto)
            r_ship_vec = np.array([sim_obj.posx[time_index], sim_obj.posy[time_index], sim_obj.posz[time_index]])
            v_ship_vec = np.array([sim_obj.velx[time_index], sim_obj.vely[time_index], sim_obj.velz[time_index]])
            r_moon_vec = np.array([sim_obj.poslx[time_index], sim_obj.posly[time_index], sim_obj.poslz[time_index]])
        except:
             # Si es tupla (tout, x, y, z...)
            r_ship_vec = np.array([sim_obj[1][time_index], sim_obj[2][time_index], sim_obj[3][time_index]])
            v_ship_vec = np.array([sim_obj[4][time_index], sim_obj[5][time_index], sim_obj[6][time_index]])
            r_moon_vec = np.array([sim_obj[9][time_index], sim_obj[10][time_index], sim_obj[11][time_index]])

    # Constantes
    from modelo_3d import mu_earth
    
    # 1. Definición de Geometría
    r1 = np.linalg.norm(r_ship_vec)      # Radio Inicial
    
    # [MODIFICACION] Radio Final ajustado para orbita de 100km (No centro)
    # r2_center = dist luna. 
    # r2_target = r2_center - (R_Moon + 100km)
    # Asumimos llegada por el "lado interno" (periapsis de transferencia < dist luna)
    
    r_moon_dist = np.linalg.norm(r_moon_vec)
    R_moon_radius = 1737100.0
    h_orbit_target = 1000000.0 # 1000 km
    
    r2 = r_moon_dist - (R_moon_radius + h_orbit_target)
    
    if r2 < r1:
        # Fallback por si la luna esta extrañamente cerca (improbable)
        r2 = r_moon_dist 

    a = (r1 + r2) / 2.0                  # Semieje mayor
    
    # 2. Cálculo Tiempo de Vuelo (TOF)
    # Periodo 2P = 2*pi * sqrt(a^3 / mu)
    periodo_completo = 2 * np.pi * np.sqrt(a**3 / mu_earth)
    tof = periodo_completo / 2.0
    
    # 3. Predicción Posición Lunar (Lead Angle)
    # Omega Luna (circular approximation)
    omega_luna = np.sqrt(mu_earth / (r2**3)) # rad/s
    
    # Angulo de barrido (lo que se mueve la luna durante el TOF)
    delta_theta_rad = omega_luna * tof
    delta_theta_deg = np.degrees(delta_theta_rad)
    
    # Angulo de fase al encendido
    # La luna debe estar a 180 - delta_theta grados de separación
    # para que al cabo de TOF, la nave (que recorre 180) se encuentre con la luna.
    phi_target_deg = 180.0 - delta_theta_deg
    
    # 4. Cálculo del Impulso (Delta V)
    # V perigeo necesaria
    v_perigeo = np.sqrt(mu_earth * ( (2.0/r1) - (1.0/a) ))
    
    # V circular actual (hipotética para r1)
    # NOTA: El usuario pide "v_c = sqrt(mu/r1)". Esto asume que estamos en circular.
    # Si la nave tiene otra velocidad, esto es solo una referencia teórica del usuario.
    # Calcularemos también la REAL para comparar.
    v_circ_teorica = np.sqrt(mu_earth / r1)
    v_real_mag = np.linalg.norm(v_ship_vec)
    
    delta_v_teorico = v_perigeo - v_circ_teorica
    # Delta V Real (asumiendo quemado tangencial perfecto desde la velocidad actual)
    # v_p - v_actual ?? No, mejor ajustamos a lo que pide el usr:
    # "El resultado es la resta: vp - vc" <-- Usaremos esto para el reporte.
    
    # 5. Determinación Momento Exacto
    # Angulo actual entre nave y luna.
    # Dot product
    dot = np.dot(r_ship_vec, r_moon_vec)
    cos_phi = dot / (r1 * r2)
    # Clamp para evitar errores numéricos
    cos_phi = np.clip(cos_phi, -1.0, 1.0)
    phi_actual_rad = np.arccos(cos_phi)
    phi_actual_deg = np.degrees(phi_actual_rad)
    
    # Determinar signo (si la luna está adelante o atras)
    # Cruzamos r_ship x r_moon. Si Z es positivo, Moon is "ahead" (counter-clockwise)
    cross_z = r_ship_vec[0]*r_moon_vec[1] - r_ship_vec[1]*r_moon_vec[0]
    # En coordenadas usuales, ccw es positivo.
    # Si cross_z < 0, el ángulo es negativo (o 360 - phi).
    # Normalizamos a 0-360.
    if cross_z < 0:
        phi_actual_deg = 360.0 - phi_actual_deg

    return {
        'r1': r1,
        'r2': r2,
        'a': a,
        'tof': tof,
        'omega_luna': omega_luna,
        'delta_theta_deg': delta_theta_deg,
        'phi_target_deg': phi_target_deg,
        'v_perigeo': v_perigeo,
        'v_circ_teorica': v_circ_teorica,
        'delta_v_teorico': delta_v_teorico,
        'phi_actual_deg': phi_actual_deg
    }


def search_best_encounter_window(sim_obj, step=10):
    """
    Recorre la simulación para encontrar el momento donde la diferencia
    entre el ángulo de fase actual y el objetivo sea mínima (ventana de disparo).
    
    Retorna: (best_idx, best_diff, result_dict)
    """
    print("\n[BUSQUEDA] Escaneando simulación en busca de ventanas de disparo...")
    
    # Extraer arrays (asumiendo objeto simulación)
    try:
        # Intenta atributos directos
        rx = sim_obj.posx
        ry = sim_obj.posy
        rz = sim_obj.posz
        rlx = sim_obj.poslx
        rly = sim_obj.posly
        rlz = sim_obj.poslz
        tout = sim_obj.tout
    except:
        # Fallback a tupla
        tout = sim_obj[0]
        rx = sim_obj[1]; ry = sim_obj[2]; rz = sim_obj[3]
        rlx = sim_obj[9]; rly = sim_obj[10]; rlz = sim_obj[11]

    n = len(tout)
    best_idx = -1
    min_diff = float('inf')
    best_res = None
    
    # Iterar con stride para velocidad
    # Si encontramos un mínimo local, podríamos refinar, pero un paso de 10-100 suele bastar
    # para la escala de tiempo de órbitas lunares.
    
    for i in range(0, n, step):
        # 1. Geometry (Vectorized-like extraction for single point)
        r_ship = np.array([rx[i], ry[i], rz[i]])
        r_moon = np.array([rlx[i], rly[i], rlz[i]])
        
        r1 = np.linalg.norm(r_ship)
        if r1 < 6371000: continue # Ignorar bajo tierra
        
        r2 = np.linalg.norm(r_moon)
        a = (r1 + r2) / 2.0
        
        # 2. TOF
        from modelo_3d import mu_earth
        period = 2 * np.pi * np.sqrt(a**3 / mu_earth)
        tof = period / 2.0
        
        # 3. Lead Angle
        omega = np.sqrt(mu_earth / (r2**3))
        d_theta = np.degrees(omega * tof)
        phi_target = 180.0 - d_theta
        
        # 4. Actual Angle
        # Dot
        dot = np.dot(r_ship, r_moon)
        denom = r1 * r2
        if denom == 0: continue
        
        val = dot / denom
        val = max(-1.0, min(1.0, val)) # Clip
        phi_act = np.degrees(np.arccos(val))
        
        # Sign check (Cross Z)
        cross_z = r_ship[0]*r_moon[1] - r_ship[1]*r_moon[0]
        if cross_z < 0:
            phi_act = 360.0 - phi_act
            
        # Diferencia
        # Queremos minimizar diferencia circular. 
        # Diff = abs(act - target). Pero 359 vs 1 es diff 2.
        diff = abs(phi_act - phi_target)
        if diff > 180:
             diff = 360 - diff
             
        if diff < min_diff:
            min_diff = diff
            best_idx = i
            
    # Una vez encontrado el mejor índice aproximado, calculamos full data
    if best_idx != -1:
        best_res = calculate_encounter_prediction(sim_obj, best_idx)
        return best_idx, min_diff, best_res
    
    return -1, 999.0, None


def analyze_trajectory_pois(sim_obj):
    """
    Analiza la trayectoria completa para encontrar Puntos de Interés (POIs).
    Retorna una lista de diccionarios: {'label': str, 'index': int, 'info': str}
    """
    print("\n[ANALISIS] Buscando Puntos de Interés en la trayectoria...")
    
    pois = []
    
    # Extraer datos de manera segura
    try:
        rx = sim_obj.posx
        ry = sim_obj.posy
        rz = sim_obj.posz
        rlx = sim_obj.poslx
        rly = sim_obj.posly
        rlz = sim_obj.poslz
        tout = sim_obj.tout
    except:
        # Fallback si no es objeto
        return []

    if len(tout) < 10:
        return []

    # 1. Distancias
    r_earth = np.sqrt(rx**2 + ry**2 + rz**2)
    
    dx = rx - rlx
    dy = ry - rly
    dz = rz - rlz
    r_moon = np.sqrt(dx**2 + dy**2 + dz**2)
    
    # 2. Perigeo (Min dist tierra) - Ignoramos los primeros segundos si sale de superficie
    #    Buscamos minimos locales o globales.
    #    Para simplificar: Global min despues de T=1000s (para evitar el lanzamiento mismo)
    start_search_idx = min(len(tout)-1, 1000) # Un indice seguro
    if start_search_idx < len(tout):
        min_r_e_idx = np.argmin(r_earth[start_search_idx:]) + start_search_idx
        pois.append({
            'label': "Perigeo (Min Dist Tierra)",
            'index': min_r_e_idx,
            'info': f"Alt: {(r_earth[min_r_e_idx]-6371000)/1000:.1f} km, T={tout[min_r_e_idx]:.1f}s"
        })

    # 3. Apogeo (Max dist tierra)
    max_r_e_idx = np.argmax(r_earth)
    pois.append({
        'label': "Apogeo (Max Dist Tierra)",
        'index': max_r_e_idx,
        'info': f"Dist: {r_earth[max_r_e_idx]/1000:.1f} km, T={tout[max_r_e_idx]:.1f}s"
    })

    # 4. Perilunio (Min dist luna)
    #    Solo si esta razonablemente cerca (< 100,000 km)
    min_r_m_idx = np.argmin(r_moon)
    min_r_m_val = r_moon[min_r_m_idx]
    
    if min_r_m_val < 100000000.0: # < 100,000 km de radio esfera influencia amplia
         pois.append({
            'label': "Perilunio (Min Dist Luna)",
            'index': min_r_m_idx,
            'info': f"Dist: {min_r_m_val/1000:.1f} km, T={tout[min_r_m_idx]:.1f}s"
        })

    # 5. Punto Equidistante (Midpoint Earth-Moon)
    #    Donde abs(r_earth - r_moon) es minimo.
    diff_dists = np.abs(r_earth - r_moon)
    equi_idx = np.argmin(diff_dists)
    
    pois.append({
        'label': "Punto Equidistante (Tierra-Luna)",
        'index': equi_idx,
        'info': f"Dist a ambos ~ {r_earth[equi_idx]/1000:.1f} km, T={tout[equi_idx]:.1f}s"
    })

    # Ordenar por tiempo
    pois.sort(key=lambda x: x['index'])
    
    return pois


def vector_to_angles(vec):
    """
    Convierte un vector dirección (x, y, z) a Theta y Beta.
    Retorna (theta_deg, beta_deg)
    """
    # Normalizar
    norm = np.linalg.norm(vec)
    if norm == 0:
        return 0.0, 0.0
    
    u = vec / norm
    
    # Theta (Zenit / Latitud esférica desde Z): arccos(vz)
    theta_rad = np.arccos(u[2])
    
    # Beta (Azimut plano XY): arctan2(vy, vx)
    beta_rad = np.arctan2(u[1], u[0])
    
    theta_deg = np.degrees(theta_rad)
    beta_deg = np.degrees(beta_rad)
    
    if beta_deg < 0: 
        beta_deg += 360.0
        
    return theta_deg, beta_deg


def calculate_maneuver_vector(r_vec, v_vec, mode):
    """
    Calcula el vector unitario de quema según el modo orbital.
    Args:
        r_vec: Posición actual
        v_vec: Velocidad actual
        mode: 'prograde', 'retrograde', 'normal', 'antinormal', 'radial_out', 'radial_in'
    
    Retorna: (u_x, u_y, u_z) vector unitario
    """
    # 1. Base vectorial local (NTW frame / RSW frame variant)
    # T (Tangencial/Prograde): Dirección velocidad
    v_norm = np.linalg.norm(v_vec)
    if v_norm == 0: return np.array([0,0,1])
    t_hat = v_vec / v_norm
    
    # N (Normal): Perpendicular al plano orbital (h = r x v)
    h_vec = np.cross(r_vec, v_vec)
    h_norm = np.linalg.norm(h_vec)
    if h_norm == 0: return np.array([0,0,1]) # Degenerado
    n_hat = h_vec / h_norm
    
    # R (Radial): Completa la triada. R = N x T? No, R usualmente es unitario posición.
    # En sistema RSW (Radial, Transverse, Normal):
    # R va a lo largo del radio vector (hacia afuera).
    # S (Transverse) va perpendicular a R en el plano orbital (~Prograde).
    # W (Normal) va a lo largo de h.
    
    # Pero para maniobras "Prograde" suele ser Tangencial, no Transversal puro (aunque se parecen en circulares).
    # Radial Out suele ser perpendicular a la velocidad hacia "arriba"? 
    # Usemos definición standard KSP:
    # Prograde: t_hat
    # Normal: n_hat
    # Radial-Out: n_hat x t_hat (Completa triada ortogonal a velocidad)
    
    rad_hat = np.cross(n_hat, t_hat) 
    
    if mode == 'prograde':
        return t_hat
    elif mode == 'retrograde':
        return -t_hat
    elif mode == 'normal':
        return n_hat
    elif mode == 'antinormal':
        return -n_hat
    elif mode == 'radial_out':
        return rad_hat
    elif mode == 'radial_in':
        return -rad_hat
    else:
        # Default prograde
        return t_hat
