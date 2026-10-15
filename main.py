from modelo_3d import calc_sim
# [MODIFICADO] Importamos la nueva función 'config_batch_from_template'
from new_sim import ConfigSim, config, test_config, config_from_sim, config_manual, config_batch, \
    config_batch_from_template, config_high_dv_orbit, config_from_sim_silent, config_400km_moon_plane
from grf_data import graf_all, plot_batch_telemetria, plot_batch_closeup, animar_simulacion, \
    plot_sistema_completo, plot_close_up_tierra, plot_datos_telemetria, plot_moon_centered, process_data
import numpy as np
from archivo_new import guardar_simulacion
from archivo_open import getdata
from calc_luna import find_moon_intercept, calculate_loi, calculate_encounter_prediction




def ran_new_sim():
    """Ejecuta el flujo para una simulación nueva (configurable o preconfigurada)."""
    try:
        a0 = int(input("\n1. Configurar Simulacion \n2. Simulacion Preconfig\n3. Orbita 100km (High DV)\n4. Orbita 400km (Plano Luna)\n--> "))
    except ValueError:
        print("Opción no válida.")
        return

    config_obj = None
    if a0 == 1:
        config_obj = config()
    elif a0 == 2:
        config_obj = config_manual()
    elif a0 == 3:
        config_obj = config_high_dv_orbit()
    elif a0 == 4:
        config_obj = config_400km_moon_plane()
    else:
        print("Opción no válida.")
        return

    print("\n[DEBUG] Configuración creada. Ejecutando calc_sim...")
    try:
        result = calc_sim(config_obj)
        print("[DEBUG] Simulación (calc_sim) finalizada con éxito.")
    except Exception as e:
        print(f"[ERROR] La simulación (calc_sim) falló: {e}")
        return

    print("[DEBUG] Generando todos los gráficos...")
    graf_all(result)
    print("[DEBUG] Gráficos mostrados.")

    try:
        a = int(input("\n1. Guardar simulación\n-->"))
        if a == 1:
            result = list(result)
            guardar_simulacion(result)
    except ValueError:
        print("Entrada no válida, no se guardará.")


# --- [NUEVA FUNCIÓN REIMPLEMENTADA] ---
def craft_sim_results(sim_activa, result_iter_tuple, config_iter_obj, time0):
    """
    Une la simulación 'activa' (antigua) con la 'result_iter_tuple' (nueva).

    Args:
        sim_activa (AdminResultasosSim): El objeto de la simulación base.
        result_iter_tuple (tuple): La tupla de 17 elementos de la nueva simulación.
        config_iter_obj (ConfigSim): El objeto de configuración usado para la nueva sim.
        time0 (int): El índice (punto de corte) donde la nueva sim comenzó.

    Returns:
        list: Una nueva lista de 17 elementos, unida.
    """
    print(f"[DEBUG] Uniendo simulaciones en el índice {time0}...")

    # 1. Get data
    old_data = list(sim_activa.graf_data())  # 17 elementos
    new_data = list(result_iter_tuple)  # 17 elementos

    stitched_list = []

    # 2. Stitch 'tout' (element 0)
    # Cortar el segmento antiguo
    tout_old_segment = old_data[0][:time0]
    # Obtener el último valor de tiempo
    last_old_time = tout_old_segment[-1]
    # Offset del nuevo segmento (saltando el t=0 duplicado)
    tout_new_segment = new_data[0][1:] + last_old_time
    stitched_tout = np.concatenate((tout_old_segment, tout_new_segment))
    stitched_list.append(stitched_tout)
    print(
        f"[DEBUG] 'tout' unido. Longitud antigua: {len(old_data[0])}, Nueva: {len(new_data[0])}, Final: {len(stitched_tout)}")

    # 3. Stitch data arrays (elements 1-14)
    # (x, y, z, vx, vy, vz, mass, alt_km, xL, yL, zL, vxL, vyL, vzL)
    for i in range(1, 15):
        old_array_segment = old_data[i][:time0]
        new_array_segment = new_data[i][1:]  # Skip t=0 duplicate
        stitched_array = np.concatenate((old_array_segment, new_array_segment))
        stitched_list.append(stitched_array)
    print(f"[DEBUG] {len(range(1, 15))} arrays de datos unidos.")

    # 4. Stitch metadata (elements 15, 16)

    # --- ang (element 15) ---
    # Combinamos la lista de 5 ángulos antiguos con los nuevos ángulos *activos*
    old_ang_list = old_data[15]
    num_new_burns = config_iter_obj.num_encendidos
    active_new_angs = new_data[15][:num_new_burns]

    stitched_ang = list(old_ang_list) + list(active_new_angs)
    stitched_list.append(stitched_ang)
    print(f"[DEBUG] Ángulos unidos. Total: {len(stitched_ang)}")

    # --- desc (element 16) ---
    # La nueva descripción es la más precisa, ya que explica la iteración.
    stitched_desc = new_data[16]
    stitched_list.append(stitched_desc)

    return stitched_list


# --- [FIN NUEVA FUNCIÓN] ---


def ran_iter_sim(sim_activa, config_iter_sim_obj, time0):
    """
    Ejecuta una *única* simulación que itera desde un punto,
    la une con la simulación original y la guarda.
    """
    print("\n[DEBUG] Ejecutando simulación iterativa (calc_sim)...")
    if config_iter_sim_obj is None:
        print("[ERROR] No se pudo crear la configuración iterativa.")
        return

    try:
        result_iter = calc_sim(config_iter_sim_obj)
        print("[DEBUG] Simulación iterativa finalizada con éxito.")
    except Exception as e:
        print(f"[ERROR] La simulación iterativa (calc_sim) falló: {e}")
        return

    # --- [LÓGICA DE UNIÓN AÑADIDA] ---
    print("[DEBUG] Creando simulación unida...")
    # Pasamos el config_obj para saber cuántos ángulos nuevos hay
    stitched_result_list = craft_sim_results(
        sim_activa, result_iter, config_iter_sim_obj, time0
    )
    # --- [FIN LÓGICA DE UNIÓN] ---

    print("[DEBUG] Generando gráficos de la simulación unida...")
    graf_all(stitched_result_list)  # Graficamos la simulación unida
    print("[DEBUG] Gráficos mostrados.")

    try:
        a0 = int(input("\n1. Guardar simulación UNIDA\n-->"))
        if a0 == 1:
            guardar_simulacion(stitched_result_list)  # Guardamos la simulación unida
            print("Simulación unida guardada.")
    except ValueError:
        print("Entrada no válida, no se guardará.")

    # Regresar al menú de la simulación madre (simplemente retornando, ya que estamos en un bucle allí)
    return


def ran_test_sim():
    """Ejecuta una simulación de prueba predefinida."""
    try:
        print("\n[DEBUG] Cargando test_config()...")
        config_obj = test_config()
        print("[DEBUG] Ejecutando calc_sim() para test...")
        result_test = calc_sim(config_obj)
        print("====Test finalizado con exito====")
    except Exception as e:
        print(f"Error al ejecutar el test: {e}")
        return

    print("[DEBUG] Generando gráficos de simulación de test...")
    graf_all(result_test)
    print("[DEBUG] Gráficos mostrados.")

    try:
        a = int(input("1. Guardar simulacion\n-->"))
        if a == 1:
            result_test = list(result_test)
            guardar_simulacion(result_test)
            print("Simulacion guardada")
    except ValueError:
        print("Entrada no válida, no se guardará.")


def _execute_batch_run(list_of_configs):
    """
    Función auxiliar interna.
    Recibe una lista de ConfigSim, las ejecuta, guarda
    y pregunta si se deben graficar.
    """
    if not list_of_configs:
        print("No se generaron configuraciones de lote. Volviendo al menú.")
        return

    num_jobs = len(list_of_configs)
    print(f"\n=== Iniciando Ejecución de Lote de {num_jobs} Simulaciones ===")

    batch_plot_data = []

    for i, config_obj in enumerate(list_of_configs):
        print(f"\n--- Ejecutando Simulación {i + 1}/{num_jobs} ---")

        try:
            desc_sim = config_obj.description
            print(f"Parámetros: {desc_sim.splitlines()[0]}")

            result = calc_sim(config_obj)
            result_list = list(result)

            sim_name = guardar_simulacion(result_list)

            if sim_name:
                print(f"Simulación {i + 1} guardada exitosamente como {sim_name}.")
                batch_plot_data.append((result_list, sim_name))
            else:
                print(f"Simulación {i + 1} falló al guardar.")

        except Exception as e:
            print(f"ERROR en la simulación {i + 1}: {e}")
            print("Continuando con la siguiente simulación del lote...")
        
    print("\n=== Lote de Simulaciones Completado ===")

    if not batch_plot_data:
        print("No se guardaron resultados, no se pueden generar gráficos de lote.")
        return

    try:
        a = input("\n¿Desea generar los gráficos comparativos del lote? (s/n)\n--> ").strip().lower()
        if a == 's':
            print("Generando gráfico de telemetría del lote...")
            plot_batch_telemetria(batch_plot_data)
            print("Generando gráfico de close-up 3D del lote...")
            plot_batch_closeup(batch_plot_data)
            print("Gráficos de lote generados.")
    except Exception as e:
        print(f"Error al generar gráficos de lote: {e}")


def ran_moon_shot():
    """Calculadora de disparo a la Luna."""
    print("\n=== Configuración Inicial para el Disparo ===")
    print("Seleccione una configuración base:")
    try:
        a0 = int(input("1. Configuración por defecto (Manual)\n2. Crear nueva configuración\n3. Orbita 100km (High DV)\n--> "))
        if a0 == 1:
            base_config = config_manual()
        elif a0 == 2:
            base_config = config()
        elif a0 == 3:
            base_config = config_high_dv_orbit()
        else:
            print("Opción no válida.")
            return
    except ValueError:
        print("Entrada inválida.")
        return

    # Llamar al optimizador
    burn_params = find_moon_intercept(base_config)
    
    if burn_params:
        print("\n¿Desea aplicar este encendido y visualizar la simulación?")
        try:
            a = input("(s/n) --> ").strip().lower()
            if a == 's':
                # Aplicar cambios
                # Limpiamos encendidos viejos y ponemos el optimizado
                base_config.data_encendidos = []
                base_config.num_encendidos = 1
                base_config.add_encendido(
                    burn_params['tstart'],
                    burn_params['tend'],
                    burn_params['thrust'],
                    burn_params['Isp'],
                    burn_params['theta'],
                    burn_params['beta']
                )
                base_config.description = f"Simulación Moon Shot (Optimizada)\nDistancia min: ...\n" + base_config.description
                
                # Ejecutar y graficar
                print("\n[DEBUG] Ejecutando simulación con solución óptima...")
                result = calc_sim(base_config)
                graf_all(result)
                
                # Opción de guardar
                if input("¿Guardar? (s/n): ").lower() == 's':
                     guardar_simulacion(list(result))
                     
        except Exception as e:
            print(f"Error al ejecutar la simulación resultante: {e}")


from calc_luna import find_moon_intercept, calculate_loi, calculate_encounter_prediction, search_best_encounter_window


def perform_tli_sequence(sim_activa, idx_start):
    """
    Ejecuta la logica de 'Calcular Disparo a la Luna' para un punto dado.
    Retorna True si se ejecutó una simulación (y por tanto quiza queramos salir del menu).
    """
    try:
        from new_sim import config_from_sim_silent # Asegurar import
        
        print(f"[INFO] Calculando TLI desde T={sim_activa.tout[idx_start]:.1f}s (Index: {idx_start})...")
        current_conf = config_from_sim_silent(idx_start, sim_activa)
        
        # Calcular target dinamico: Distancia Luna Actual - (RadioLuna + 100km)
        # Obtenemos posicion luna del frame actual
        # Depende de si es un objeto FullSim o tuple
        try:
             lx = sim_activa.poslx[idx_start]
             ly = sim_activa.posly[idx_start]
             lz = sim_activa.poslz[idx_start]
             r_moon_current = np.sqrt(lx**2 + ly**2 + lz**2)
             
             # Offset
             # r_target = r_moon_current - (1737100.0 + 1000000.0) # 1000 km
             r_target = r_moon_current - (1737100.0 + 10000000.0)
             print(f"[INFO] Objetivo dinámico calculado: {r_target/1000:.1f} km (Luna @ {r_moon_current/1000:.1f} km)")
        except:
             print("[WARN] No se pudo leer posición luna, usando default.")
             r_target = None

        res_tli = find_moon_intercept(current_conf, r_target=r_target)
        
        if res_tli:
            print("\n--- Solución TLI Encontrada ---")
            print(f"Delta V: {res_tli['delta_v']:.1f} m/s")
            print(f"Duración: {res_tli['tend']:.1f} s")
            
            if input("\n¿Aplicar este encendido? (s/n): ").lower() == 's':
                current_conf.num_encendidos = 1
                current_conf.data_encendidos = []
                current_conf.add_encendido(
                    res_tli['tstart'],
                    res_tli['tend'],
                    res_tli['thrust'],
                    res_tli['Isp'],
                    res_tli['theta'],
                    res_tli['beta']
                )
                current_conf.max_step = min(1.0, res_tli['tend'] / 10.0)
                current_conf.fill_empty_burns()
                current_conf.description += f"\n[TLI] DV={res_tli['delta_v']:.1f} MaxStep={current_conf.max_step}"
                
                ran_iter_sim(sim_activa, current_conf, idx_start)
                return True 
            else:
                print("Operación cancelada.")
        else:
            print("No se encontró solución válida.")
            
    except Exception as e:
        print(f"Error en TLI sequence: {e}")
        
    return False


def run_new_batch_sim():
    """
    Crea y ejecuta un lote de simulaciones desde CERO.
    Llamado desde el menú principal.
    """
    list_of_configs = config_batch()
    _execute_batch_run(list_of_configs)


def menu_sim_admin(sim_activa):
    """Muestra el submenú para administrar una simulación cargada."""
    while True:
        print(f"\n--- Menú Simulación: {sim_activa.name} ---")
        print("1. Graficas (Simulación Individual)")
        print("2. Maniobras Orbitales")
        print("3. Ver Descripción")
        print("4. Generar Animación")
        print("5. Extender simulación (días variable)")
        print("6. Volver al Menú Principal")

        try:
            a0 = int(input("--> "))
        except ValueError:
            print("Opción no válida.")
            continue

        if a0 == 1:
            print("\n--- Menú de Gráficos ---")
            print("1. Ver Todo (Secuencial)")
            print("2. Sistema Tierra-Luna (3D)")
            print("3. Close-up Tierra (3D)")
            print("4. Close-up Luna (3D)")
            print("5. Telemetría (2D)")
            print("6. Volver")

            try:
                g_op = int(input("--> "))
                if g_op == 6:
                    continue
                
                print("[DEBUG] Procesando datos para visualización...")
                # Procesamos datos una vez
                try:
                    raw_data = list(sim_activa.graf_data())
                    processed_data = process_data(raw_data)
                except Exception as e:
                    print(f"[ERROR] Falló el procesamiento de datos: {e}")
                    continue

                if g_op == 1:
                    graf_all(raw_data)
                elif g_op == 2:
                    plot_sistema_completo(processed_data)
                elif g_op == 3:
                    plot_close_up_tierra(processed_data)
                elif g_op == 4:
                    plot_moon_centered(processed_data)
                elif g_op == 5:
                    plot_datos_telemetria(processed_data)
                else:
                    print("Opción no válida.")
            except ValueError:
                print("Entrada no válida.")
            except Exception as e:
                print(f"Error al graficar: {e}")

        elif a0 == 2:
            # --- SUB-MENÚ MANIOBRAS ORBITALES ---
            while True:
                print(f"\n--- Maniobras Orbitales ---")
                print("1. Realizar Maniobra / Nueva Simulación")
                print("2. Herramientas de Cálculo Lunar")
                print("3. Volver")
                
                try:
                    a_man = int(input("--> "))

                    if a_man == 1:
                        # --- NUEVA LÓGICA "MANIOBRA ORBITAL" CON POIs ---
                        try:
                            # 1. Analizar Puntos de Interés
                            from calc_luna import analyze_trajectory_pois
                            pois = analyze_trajectory_pois(sim_activa)
                            
                            print(f"\n--- Selector de Punto de Inicio (Maniobra) ---")
                            print("Puntos de interés detectados:")
                            
                            # Validar que tengamos puntos
                            valid_pois = []
                            import string
                            abc_chars = string.ascii_lowercase
                            
                            if pois:
                                for i, p in enumerate(pois):
                                    tag = abc_chars[i] if i < len(abc_chars) else f"({i})"
                                    print(f"   {tag}) {p['label']} -> {p['info']}")
                                    valid_pois.append(p)
                            else:
                                print("   (No se detectaron puntos especiales llamativos)")

                            print(f"\nOpciones:")
                            print(f"   - Ingrese la LETRA del punto de interés (ej: a, b...)")
                            print(f"   - O ingrese un índice manual numérico (0 a {len(sim_activa.tout) - 1})")
                            
                            entrada = input("--> ").strip().lower()
                            
                            time0 = -1
                            
                            # Intentar interpretar como selección de menú (LETRA)
                            is_menu_sel = False
                            # Si es una letra y está en el rango de puntos mostrados
                            if len(entrada) == 1 and entrada.isalpha():
                                if entrada in abc_chars:
                                    idx_sel = abc_chars.find(entrada)
                                    if 0 <= idx_sel < len(valid_pois):
                                        time0 = valid_pois[idx_sel]['index']
                                        print(f"[SELECCIÓN] Usando {valid_pois[idx_sel]['label']} (Index: {time0})")
                                        is_menu_sel = True
                            
                            if not is_menu_sel:
                                # Interpretar como raw index
                                # Aceptamos digitos. Notar que si el usuario metió "1", ahora
                                # se interpretará como index 1 (manual), no opcion 1.
                                # Esto es lo que se pidió: distinguir 'a' (menu) de '123' (indice).
                                try:
                                    t_idx = int(entrada)
                                    if 0 <= t_idx < len(sim_activa.tout):
                                        time0 = t_idx
                                        print(f"[MANUAL] Usando índice personalizado: {time0}")
                                    else:
                                        print(f"[ERROR] Índice fuera de rango.")
                                        continue
                                except ValueError:
                                     print("Entrada no válida (debe ser letra 'a-z' o número de índice).")
                                     continue
                            
                            if not is_menu_sel:
                                # Interpretar como raw index
                                try:
                                    t_idx = int(entrada)
                                    if 0 <= t_idx < len(sim_activa.tout):
                                        time0 = t_idx
                                        print(f"[MANUAL] Usando índice personalizado: {time0}")
                                    else:
                                        print(f"[ERROR] Índice fuera de rango.")
                                        continue
                                except ValueError:
                                     print("Entrada no válida.")
                                     continue

                            if time0 == -1: continue

                            # --- WIZARD MANIOBRA ---
                            print(f"\n=== Configuración de Maniobra Orbitale (T={sim_activa.tout[time0]:.1f}s) ===")
                            
                            # 1. Seleccionar Dirección
                            print("Seleccione la DIRECCIÓN del encendido:")
                            print("1. Prograde (Acelerar)")
                            print("2. Retrograde (Frenar)")
                            print("3. Normal (Cambio Plano +)")
                            print("4. Antinormal (Cambio Plano -)")
                            print("5. Radial-Out (Subir Apogeo/Rotar)")
                            print("6. Radial-In (Bajar Apogeo/Rotar)")
                            print("7. Manual (Theta/Beta personalizados)")
                            
                            try:
                                d_sel = int(input("--> "))
                            except ValueError:
                                print("Opción inválida.")
                                continue

                            mode_map = {1: 'prograde', 2: 'retrograde', 3: 'normal', 4: 'antinormal', 5: 'radial_out', 6: 'radial_in'}
                            selected_mode = mode_map.get(d_sel, 'manual')
                            
                            target_theta = 0.0
                            target_beta = 0.0
                            
                            if selected_mode != 'manual':
                                from calc_luna import calculate_maneuver_vector, vector_to_angles
                                # Obtener vectores estado (wrapper compatible)
                                r_vec = np.array([sim_activa.posx[time0], sim_activa.posy[time0], sim_activa.posz[time0]])
                                v_vec = np.array([sim_activa.velx[time0], sim_activa.vely[time0], sim_activa.velz[time0]])
                                
                                u_burn = calculate_maneuver_vector(r_vec, v_vec, selected_mode)
                                target_theta, target_beta = vector_to_angles(u_burn)
                                print(f"[INFO] Dirección calculada: Theta={target_theta:.2f}, Beta={target_beta:.2f}")

                            else:
                                print("Ingrese ángulos manuales:")
                                try:
                                    target_theta = float(input("Theta [deg]: "))
                                    target_beta = float(input("Beta [deg]: "))
                                except ValueError:
                                    print("Valor inválido.")
                                    continue
                            
                            # 2. Parametros Encendido
                            print("\n--- Parámetros del Quemado ---")
                            try:
                                delta_v = float(input("Ingrese Delta-V deseado [m/s]: "))
                                thrust = float(input("Ingrese Empuje (Thrust) [N] (Default 500000): ") or 500000.0)
                                isp = float(input("Ingrese Isp [s] (Default 450): ") or 450.0)
                            except ValueError:
                                print("Entrada numérica inválida.")
                                continue
                                
                            duration = 0.0
                            # Calcular duración Rocket Equation
                            # global np is available
                            g0 = 9.80665
                            m0 = sim_activa.mass[time0]
                            # mf = m0 / exp(dv / ve)
                            ve = isp * g0
                            
                            if ve <= 0:
                                print("[ERROR] Isp debe ser positivo.")
                                continue

                            mf = m0 / np.exp(abs(delta_v) / ve)
                            m_prop = m0 - mf
                            mass_flow = thrust / ve
                            
                            if mass_flow > 0:
                                duration = m_prop / mass_flow
                                print(f"[CALC] Duración estimada: {duration:.2f} s Consumo: {m_prop:.1f} kg")
                            else:
                                print("[ERROR] Flujo másico cero (Thrust=0?).")
                                duration = 0.0

                            # 3. Configurar Simulación Automáticamente
                            print("\n[SETUP] Configurando nueva simulación...")
                            
                            # Duración de la simulación
                            # Igual lógica que extension: 1 día o user defined?
                            # El prompt decia: "automatizes la duracion... con los mismos parametros que usas para extender"
                            # En 'Extender' pedimos input float days.
                            # Aquí podemos hacer algo similar o default. "automatizes" suena a default inteligente o prompt rapido.
                            # Usaremos prompt rapido con default 1 dia.
                            
                            try:
                                raw_days = input("Duración Simulación [días] (Default 1.0): ") or "1.0"
                                sim_days = float(raw_days)
                            except ValueError: 
                                sim_days = 1.0
                            
                            sim_duration_s = sim_days * 86400.0
                            
                            # Crear config silenciosa
                            new_conf = config_from_sim_silent(time0, sim_activa, duration=sim_duration_s)
                            if new_conf:
                                # Setup Burn
                                if duration > 0 and thrust > 0:
                                    new_conf.num_encendidos = 1
                                    new_conf.data_encendidos = []
                                    new_conf.add_encendido(0.0, duration, thrust, isp, target_theta, target_beta)
                                    new_conf.fill_empty_burns()
                                    
                                    mode_str = selected_mode.upper() if selected_mode != 'manual' else "MANUAL"
                                    new_conf.description += f"\n[MANIOBRA] {mode_str} DV={delta_v}m/s T={duration:.1f}s"
                                
                                ran_iter_sim(sim_activa, new_conf, time0)
                                # Volver al loop del menu
                            else:
                                print("[ERROR] Falló la creación de configuración.")

                        except (IndexError, AttributeError) as e:
                            print(f"\n[ERROR] No se pudo iniciar la simulación iterativa.")
                            print(f"Detalle: {e}")
                            import traceback
                            traceback.print_exc()
                        except Exception as e:
                            print(f"Error inesperado: {e}")
                            import traceback
                            traceback.print_exc()
                            
                        # Evitar caer en el bloque antiguo
                        continue 

                    elif a_man == 2:
                        # --- LÓGICA ANTIGUA "Herramientas de Cálculo Lunar" ---
                        while True:
                            print(f"\n--- Herramientas Lunares (Simples) ---")
                            print("1. Calcular Disparo a la Luna (TLI) - Desde Posición Final")
                            print("2. Calcular Inserción Orbital (LOI) - Desde Perilunio")
                            print("3. Predicción de Encuentro Lunar (Calculadora Fase)")
                            print("4. Volver")
                            
                            try:
                                a_sub = int(input("--> "))
                                
                                if a_sub == 1:
                                    # --- TLI ---
                                    try:
                                        total_points = len(sim_activa.tout)
                                        last_idx = total_points - 1
                                        
                                        raw_idx = input(f"Simulacion tiene {total_points} puntos. Ingrese punto de inicio (Enter = {last_idx} [Final]): ").strip()
                                        
                                        if raw_idx == "":
                                            idx_start = last_idx
                                        else:
                                            try:
                                                idx_start = int(raw_idx)
                                                if not (0 <= idx_start <= last_idx):
                                                    print(f"[ERROR] Índice debe estar entre 0 y {last_idx}")
                                                    continue
                                            except ValueError:
                                                print("[ERROR] Entrada no válida. Usando final.")
                                                idx_start = last_idx
                                        
                                        if perform_tli_sequence(sim_activa, idx_start):
                                            pass # break? No, stay in lunar tools or orbit util? Stay in lunar tools
                                    except Exception as e:
                                        print(f"Error en TLI: {e}")

                                elif a_sub == 2:
                                    # --- LOI ---
                                    try:
                                        print("[INFO] Buscando aproximación más cercana a la Luna en datos existentes...")
                                        res_loi = calculate_loi(sim_activa)
                                        
                                        if res_loi:
                                            dist_km = res_loi['min_dist'] / 1000.0
                                            print("\n--- Solución LOI Encontrada ---")
                                            print(f"Distancia Mínima: {dist_km:.1f} km")
                                            print(f"Delta V Requerido: {abs(res_loi['delta_v']):.1f} m/s")
                                            
                                            if input("\n¿Aplicar inserción (circularizar)? (s/n): ").lower() == 's':
                                                idx_peri = res_loi['time_idx']
                                                peri_conf = config_from_sim_silent(idx_peri, sim_activa)
                                                
                                                peri_conf.num_encendidos = 0
                                                peri_conf.data_encendidos = []
                                                peri_conf.add_encendido(
                                                    res_loi['tstart'],
                                                    res_loi['tend'],
                                                    res_loi['thrust'],
                                                    res_loi['Isp'],
                                                    res_loi['theta'],
                                                    res_loi['beta']
                                                )
                                                peri_conf.description += f"\n[LOI] Capture @ {dist_km:.0f}km"
                                                ran_iter_sim(sim_activa, peri_conf, idx_peri)
                                                # break # Stay in lunar tools
                                        else:
                                            print("No se encontró una órbita cercana a la Luna para circularizar.")
                                    except Exception as e:
                                        print(f"Error en LOI: {e}")
                                        
                                elif a_sub == 3:
                                    # --- PREDICCION ENCUENTRO ---
                                    try:
                                        total_points = len(sim_activa.tout)
                                        last_idx = total_points - 1
                                        
                                        print(f"\n[OPCIONES] Enter/Num: Punto Manual ({last_idx}) | 'a': Buscar Ventana Óptima")
                                        raw_idx = input(f"Ingrese opción: ").strip().lower()
                                        
                                        idx_start = last_idx 
                                        
                                        if raw_idx == 'a':
                                            b_idx, b_diff, b_res = search_best_encounter_window(sim_activa)
                                            if b_idx != -1:
                                                print(f"--- ¡Ventana Encontrada! ---")
                                                print(f"Tiempo: T={sim_activa.tout[b_idx]:.1f}s (Index: {b_idx})")
                                                print(f"Desviación de fase: {b_diff:.2f} deg")
                                                idx_start = b_idx
                                                results = b_res
                                            else:
                                                print("[WARN] No se encontró ninguna ventana razonable.")
                                                results = calculate_encounter_prediction(sim_activa, idx_start, is_stand_alone=False)
                                        else:
                                            if raw_idx != "":
                                                try:
                                                    idx_start = int(raw_idx)
                                                    if not (0 <= idx_start <= last_idx):
                                                        print(f"[ERROR] Índice debe estar entre 0 y {last_idx}")
                                                        continue
                                                except ValueError:
                                                    print("[ERROR] Entrada no válida. Usando final.")
                                                    idx_start = last_idx
                                            results = calculate_encounter_prediction(sim_activa, idx_start, is_stand_alone=False)
                                        
                                        print("\n=== PREDICCION DE ENCUENTRO LUNAR ===")
                                        print(f"Radio Nave (r1):      {results['r1']/1000:.1f} km")
                                        print(f"Distancia Luna (r2):  {results['r2']/1000:.1f} km")
                                        print(f"Semieje Transf (a):   {results['a']/1000:.1f} km")
                                        print(f"Tiempo viaje (TOF):   {results['tof']:.1f} s ({results['tof']/3600:.2f} h)")
                                        print(f"Velocidad Luna (wL):  {results['omega_luna']:.8f} rad/s")
                                        print(f"Movimiento Luna (dTh):{results['delta_theta_deg']:.2f} deg")
                                        print("---------------------------------------")
                                        print(f"Ángulo Fase TARGET:   {results['phi_target_deg']:.2f} deg")
                                        print(f"Ángulo Fase ACTUAL:   {results['phi_actual_deg']:.2f} deg")
                                        diff = results['phi_actual_deg'] - results['phi_target_deg']
                                        print(f"Diferencia:           {diff:.2f} deg")
                                        print("---------------------------------------")
                                        print(f"V Perigeo (Requerida):{results['v_perigeo']:.2f} m/s")
                                        print(f"V Circular (Teórica): {results['v_circ_teorica']:.2f} m/s")
                                        print(f"Delta V (Estimado):   {results['delta_v_teorico']:.2f} m/s")
                                        print("=======================================")
                                        
                                        if abs(diff) < 5.0:
                                            print("[INFO] ¡Ventana de lanzamiento CERCANA (<5 deg)!")
                                            if input("¿Desea PROCEDER a calcular disparo TLI en este punto? (s/n): ").strip().lower() == 's':
                                                 perform_tli_sequence(sim_activa, idx_start)
                                                 # break 
                                        else:
                                            print("[INFO] Ventana de lanzamiento lejana.")

                                    except Exception as e:
                                        print(f"Error en Predicción: {e}")

                                elif a_sub == 4:
                                    break
                                else:
                                    print("Opción inválida")
                            except ValueError:
                                continue
                                
                    elif a_man == 3:
                        break
                    else:
                        print("Opción no válida.")
                except ValueError:
                    print("Entrada no válida.")

        elif a0 == 3:
            # Descripción
            try:
                print(f"\n {str(sim_activa)}\n")
            except AttributeError:
                print("\n[DEBUG] No disponible.")

        elif a0 == 4:
            # Animación
            try:
                sim_name = sim_activa.name
                sim_id = sim_name.split('_')[-1]
                video_name = f"{sim_id}_sim"
                print(f"\n[DEBUG] Generando animación {video_name}...")
                animar_simulacion(sim_activa.graf_data(), output_folder="vid_sims", video_name=video_name)
            except Exception as e:
                print(f"Error generando animación: {e}")

        elif a0 == 5:
            # Extender simulación X días
            try:
                raw_days = input("\nIngrese cantidad de días a extender (float): ")
                try:
                    days = float(raw_days)
                except ValueError:
                    print("Entrada no válida. Usando 1.0 días por defecto.")
                    days = 1.0
                
                duration_s = days * 86400.0
                print(f"\n[INFO] Configurando extensión de {days} días ({duration_s} s)...")
                
                last_idx = len(sim_activa.tout) - 1
                
                # Crear config silenciosa
                ext_config = config_from_sim_silent(last_idx, sim_activa, duration=duration_s)
                
                if ext_config:
                    ext_config.description += f"\n[EXTENSION] +{days} Días de simulación"
                    ran_iter_sim(sim_activa, ext_config, last_idx)
                else:
                    print("[ERROR] No se pudo crear la configuración de extensión.")
            
            except Exception as e:
                print(f"Error al extender simulación: {e}")

        elif a0 == 6:
            # Volver
            return

        else:
            print("Opción no válida.")


def load_sims():
    """Carga y muestra las simulaciones guardadas para que el usuario seleccione una."""
    all_sims = getdata()
    if not all_sims:
        print("\nNo se encontraron simulaciones guardadas.")
        return

    nombres = list(all_sims.keys())
    objc = list(all_sims.values())
    print(f"=====================\n"
          f"Nombre SIMS Guardadas\n"
          f"=====================\n")
    num_nombres = []
    for i in range(len(nombres)):
        n = nombres[i].removeprefix("sim_run_")
        num_nombres.append(n)
        print(f"{nombres[i]}")

    a = str(input(f"\nIngresa el numero asociado a la simulacion que se decea analizar(incluya los 0):\n--> "))

    sim_encontrada = None
    for i in range(len(nombres)):
        if a == num_nombres[i]:
            key_name = f"sim_run_{a}"
            sim_encontrada = all_sims.get(key_name)
            break

    if sim_encontrada:
        menu_sim_admin(sim_encontrada)
    else:
        print("Simulación no encontrada.")


def menu():
    """Bucle del menú principal."""
    while True:
        print("\n=========================")
        print("=== PROGRAMACIÓN COHETES ===")
        print("=========================")
        print("1. Nueva SIM")
        print("2. Cargar SIM Pasada")
        print("3. Ejecutar Test")
        print("4. Simulación por Lotes (Batch)")
        print("5. Calcular Disparo a la Luna")
        print("6. Salir")

        try:
            a = int(input("--> "))

            if a == 1:
                ran_new_sim()
            elif a == 2:
                load_sims()
            elif a == 3:
                print("=====TEST=====")
                ran_test_sim()
            elif a == 4:
                run_new_batch_sim()
            elif a == 5:
                ran_moon_shot()
            elif a == 6:
                print("Saliendo del programa.")
                exit()
            else:
                print("Opción no válida. Intente de nuevo.")

        except ValueError:
            print("Entrada inválida. Por favor ingrese un número.")
        except Exception as e:
            print(f"Ocurrió un error inesperado en el menú: {e}")


if __name__ == "__main__":
    menu()