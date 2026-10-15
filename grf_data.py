import numpy as np
import matplotlib

matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation  # [NUEVO] Importación para animaciones
from scipy.ndimage import map_coordinates
import matplotlib.image as mpimg
from scipy.signal import find_peaks
import os  # [NUEVO] Para manejar directorios

##### CONSTANTES FÍSICAS #####
G = 6.6742e-11
Rplanet = 6_357_000.0
mplanet = 5.972e24
Rluna = 1_737_100
mluna = 7.34767309e22
g0 = 9.80665

##### VARIABLES GLOBALES DE TEXTURA #####
tierra_coords = None
tierra_tex = None
luna_coords_base = None


def _load_textures():
    """Carga las texturas y geometrías de los planetas una sola vez."""
    global tierra_coords, tierra_tex, luna_coords_base
    if tierra_coords is not None:
        return
    phi, theta = np.mgrid[0:np.pi:300j, 0:2 * np.pi:300j]
    xplanet = Rplanet * np.sin(phi) * np.cos(theta)
    yplanet = Rplanet * np.sin(phi) * np.sin(theta)
    zplanet = Rplanet * np.cos(phi)
    tierra_coords = (xplanet, yplanet, zplanet)
    try:
        img = mpimg.imread('textura_tierra.jpg')
        if img.dtype != float:
            img = img.astype(float) / 255.0
        lon = (theta / (2 * np.pi)) * img.shape[1]
        lat = (phi / np.pi) * img.shape[0]
        texture = np.zeros(phi.shape + (3,))
        for i in range(3):
            texture[..., i] = map_coordinates(img[..., i], [lat, lon], order=1, mode='wrap')
        tierra_tex = texture
    except FileNotFoundError:
        print("Advertencia: No se encontró 'textura_tierra.jpg'. La Tierra será azul.")
        tierra_tex = 'blue'
    xluna_base = Rluna * np.sin(phi) * np.cos(theta)
    yluna_base = Rluna * np.sin(phi) * np.sin(theta)
    zluna_base = Rluna * np.cos(phi)
    luna_coords_base = (xluna_base, yluna_base, zluna_base)


def process_data(data):
    """
    Procesa los datos crudos de la simulación y calcula todas las métricas derivadas.
    Retorna un diccionario con todo lo necesario para graficar.
    """
    if data is None or not (16 <= len(data) <= 17):
        raise ValueError(f"Datos inválidos: Se esperaban 16 o 17 elementos, recibidos {len(data) if data else 0}")

    if len(data) == 17:
        (tout, x, y, z, vx, vy, vz, mass, alt_tierra_km,
         xL, yL, zL, vxL, vyL, vzL, ang_rad, desc) = data
    else:
        # Compatibilidad 16 elementos
        (tout, x, y, z, vx, vy, vz, mass,
         xL, yL, zL, vxL, vyL, vzL, ang_rad, desc) = data
        alt_tierra_km = (np.sqrt(x ** 2 + y ** 2 + z ** 2) - Rplanet) / 1000.0

    # Cálculos derivados
    vel_mag = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
    dist_luna_m = np.sqrt((xL - x) ** 2 + (yL - y) ** 2 + (zL - z) ** 2)
    alt_luna_m = dist_luna_m - Rluna
    dvx, dvy, dvz = np.gradient(vx), np.gradient(vy), np.gradient(vz)
    dt_steps = np.gradient(tout)
    dt_safe = np.where(dt_steps == 0, 1e-9, dt_steps)
    accel_x, accel_y, accel_z = dvx / dt_safe, dvy / dt_safe, dvz / dt_safe
    accel_mag = np.sqrt(accel_x ** 2 + accel_y ** 2 + accel_z ** 2)
    g_loads = np.nan_to_num(accel_mag / g0)
    mu_tierra = G * mplanet
    r_tierra = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    energia_especifica = (vel_mag ** 2 / 2) - mu_tierra / r_tierra

    # Detección de encendidos (Burn detection)
    burn_indices, _ = find_peaks(g_loads, height=0.5, distance=10)
    burn_positions = [[x[i], y[i], z[i]] for i in burn_indices]
    burn_vectors = []

    for i, idx in enumerate(burn_indices):
        if i < len(ang_rad):
            current_ang = ang_rad[i]
            if isinstance(current_ang, (tuple, list, np.ndarray)) and len(current_ang) == 2:
                theta, beta = current_ang
            elif isinstance(current_ang, (float, np.float64)):
                theta = current_ang
                beta = 0.0
            else:
                theta, beta = 0.0, 0.0
            tx = np.sin(theta) * np.cos(beta)
            ty = np.sin(theta) * np.sin(beta)
            tz = np.cos(theta)
            v = np.array([tx, ty, tz])
            if np.linalg.norm(v) > 0:
                v = v / np.linalg.norm(v)
            burn_vectors.append(v)
        else:
            v = np.array([accel_x[idx], accel_y[idx], accel_z[idx]])
            v = v / np.linalg.norm(v)
            burn_vectors.append(v)
    
    return {
        'tout': tout, 'x': x, 'y': y, 'z': z,
        'vx': vx, 'vy': vy, 'vz': vz, 'mass': mass,
        'xL': xL, 'yL': yL, 'zL': zL,
        'vxL': vxL, 'vyL': vyL, 'vzL': vzL,
        'alt_tierra_km': alt_tierra_km,
        'alt_luna_m': alt_luna_m,
        'vel_mag': vel_mag,
        'g_loads': g_loads,
        'energia_especifica': energia_especifica,
        'burn_positions': burn_positions,
        'burn_vectors': burn_vectors,
        'desc': desc
    }


def graf_all(data):
    """
    Función wrapper que procesa los datos y muestra TODOS los gráficos.
    """
    try:
        processed = process_data(data)
    except ValueError as e:
        print(f"Error gestionando datos: {e}")
        return

    print("Datos procesados correctamente. Generando gráficos... ✅")
    _load_textures()

    try:
        print("1. Sistema Completo...")
        plot_sistema_completo(processed)
        print("2. Close-up Tierra...")
        plot_close_up_tierra(processed)
        print("3. Telemetría...")
        plot_datos_telemetria(processed)
        # Opcional: Mostrar también el de la Luna por defecto o no. 
        # Si el usuario pide visualizar "todo", tiene sentido que salga todo.
        print("4. Close-up Luna...")
        plot_moon_centered(processed)
        
        print("Todos los gráficos generados.")
    except Exception as e:
        print(f"Error durante la generación de gráficos: {e}")


def plot_sistema_completo(d):
    """ (FUNCIÓN 1) Sistema Tierra-Luna Completo. """
    x, y, z = d['x'], d['y'], d['z']
    xL, yL, zL = d['xL'], d['yL'], d['zL']
    
    fig, ax = plt.subplots(subplot_kw={'projection': '3d'}, figsize=(12, 12))
    t_coords, t_tex, l_coords = tierra_coords, tierra_tex, luna_coords_base
    
    # Tierra
    if isinstance(t_tex, str):
        ax.plot_surface(t_coords[0], t_coords[1], t_coords[2], color=t_tex, linewidth=0, shade=False, alpha=0.8)
    else:
        ax.plot_surface(t_coords[0], t_coords[1], t_coords[2], facecolors=t_tex, linewidth=0, shade=False, alpha=0.8)
    
    # Luna (posición final)
    px, py, pz = xL[-1], yL[-1], zL[-1]
    ax.plot_surface(l_coords[0] + px, l_coords[1] + py, l_coords[2] + pz,
                    color='grey', linewidth=0, antialiased=False, shade=True)
    
    ax.plot(xL, yL, zL, color='grey', linestyle='--', label='Órbita Lunar')
    ax.plot(x, y, z, 'tomato', label='Órbita Cohete', lw=2)
    
    # Removed black background overrides
    # fig.patch.set_facecolor('black')
    # ax.set_facecolor('black')
    ax.grid(True)
    # ax.set(xticks=[], yticks=[], zticks=[]) # Keep ticks for grid reference
    
    max_range = np.max(np.abs(np.array([x, y, z, xL, yL, zL]))) * 1.1
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-max_range, max_range)
    ax.legend()
    plt.title("Sistema Completo Tierra-Luna")
    plt.show()


def plot_close_up_tierra(d):
    """ (FUNCIÓN 2) Close-up Tierra. """
    x, y, z = d['x'], d['y'], d['z']
    burn_positions = d['burn_positions']
    burn_vectors = d['burn_vectors']

    fig, ax = plt.subplots(subplot_kw={'projection': '3d'}, figsize=(12, 12))
    t_coords, t_tex, _ = tierra_coords, tierra_tex, luna_coords_base
    
    if isinstance(t_tex, str):
        ax.plot_surface(t_coords[0], t_coords[1], t_coords[2], color=t_tex, linewidth=0, shade=True, alpha=0.7)
    else:
        ax.plot_surface(t_coords[0], t_coords[1], t_coords[2], facecolors=t_tex, linewidth=0, shade=True, alpha=0.7)
        
    ax.plot(x, y, z, 'tomato', label='Órbita Cohete', lw=2)
    
    vector_len = Rplanet * 0.3
    colors = ['lime', 'cyan', 'magenta', 'yellow', 'springgreen']
    for i, pos in enumerate(burn_positions):
        if i < len(burn_vectors):
            vec = burn_vectors[i]
            col = colors[i % len(colors)]
            ax.quiver(pos[0], pos[1], pos[2], vec[0], vec[1], vec[2],
                      length=vector_len, color=col, arrow_length_ratio=0.3, linewidth=2.5,
                      label=f'Encendido {i}')
            ax.plot(pos[0], pos[1], pos[2], 'o', color=col, markersize=8)
            
    # Removed black background overrides
    # fig.patch.set_facecolor('black')
    # ax.set_facecolor('black')
    ax.grid(True)
    # ax.set(xticks=[], yticks=[], zticks=[])
    
    max_range_orbital = np.max(np.sqrt(x ** 2 + y ** 2 + z ** 2))
    max_range = max(max_range_orbital, Rplanet * 1.5) * 1.1
    ax.set_xlim(-max_range, max_range)
    ax.set_ylim(-max_range, max_range)
    ax.set_zlim(-max_range, max_range)
    ax.legend()
    plt.title("Close-up Tierra y Encendidos")
    plt.show()


def plot_moon_centered(d):
    """ (FUNCIÓN 4 - NUEVA) Close-up Centrado en la Luna. """
    # Coordenadas relativas a la Luna
    x_rel = d['x'] - d['xL']
    y_rel = d['y'] - d['yL']
    z_rel = d['z'] - d['zL']
    
    fig, ax = plt.subplots(subplot_kw={'projection': '3d'}, figsize=(12, 12))
    _, _, l_coords = tierra_coords, tierra_tex, luna_coords_base
    
    # Dibujar Luna en (0,0,0)
    ax.plot_surface(l_coords[0], l_coords[1], l_coords[2],
                    color='grey', linewidth=0, antialiased=False, shade=True, alpha=0.9)
    
    # Trayectoria relativa
    ax.plot(x_rel, y_rel, z_rel, 'cyan', label='Trayectoria Relativa', lw=2)
    
    # Marcar inicio y fin
    ax.plot([x_rel[0]], [y_rel[0]], [z_rel[0]], 'o', color='green', label='Inicio')
    ax.plot([x_rel[-1]], [y_rel[-1]], [z_rel[-1]], 'x', color='red', label='Fin')

    # Removed black background overrides
    # fig.patch.set_facecolor('black')
    # ax.set_facecolor('black')
    ax.grid(True)
    # ax.set_axis_off() # Removed to show grid
    
    # Escala dinámica basada en la distancia máxima a la Luna durante la simulación
    # pero acotada para que no sea inmensa si la nave está en la Tierra.
    # Usemos el mínimo de la distancia para centrar el interés, o un rango fijo cercano si hay flyby?
    # Mejor: calcular distancias y ver dónde está la acción.
    dists = np.sqrt(x_rel**2 + y_rel**2 + z_rel**2)
    min_dist = np.min(dists)
    
    # Si la nave nunca se acerca a la luna (< 50,000 km), mostrar un rango amplio 
    # pero centrado en la luna implicaría ver la nave lejos.
    # Si hubo flyby, queremos ver eso.
    
    if min_dist < 20000000: # 20,000 km
        # Zoom en el periapsis lunar +/- un factor
        sphere_radius = max(min_dist * 5.0, Rluna * 3.0) 
    else:
        # Lejos, mostrar hasta donde llegue
        sphere_radius = Rluna * 20.0
       
    # A veces el usuario quiere ver "todo" el viaje relativo.
    # Probemos con un bounding box de la trayectoria que cae DENTRO de un radio razonable
    # O simplemente max_range de los puntos que estén "cerca".
    
    # Enfoque simple: Limitar a una "Esfera de Influencia Visual" de ~50,000 km
    # Si la nave sale de ahí, se corta el gráfico.
    
    interest_mask = dists < 100000000 # 100,000 km
    if np.any(interest_mask):
         max_r = np.max(dists[interest_mask]) * 1.1
    else:
         max_r = Rluna * 10
         
    # Clamp visual
    ax.set_xlim(-max_r, max_r)
    ax.set_ylim(-max_r, max_r)
    ax.set_zlim(-max_r, max_r)

    ax.legend()
    plt.title(f"Close-up Centrado en la Luna (Min Dist: {min_dist/1000:.1f} km)")
    plt.show()


def plot_datos_telemetria(d):
    """ (FUNCIÓN 3) Telemetría 2D. """
    # Unpack from dict
    tout = d['tout']
    alt_tierra_km = d['alt_tierra_km']
    alt_luna_m = d['alt_luna_m']
    vel_mag = d['vel_mag']
    mass = d['mass']
    g_loads = d['g_loads']
    energia_especifica = d['energia_especifica']

    fig, axes = plt.subplots(3, 2, figsize=(16, 12), sharex=True)
    fig.suptitle("Datos de Telemetría de Vuelo", fontsize=18)
    
    ax = axes[0, 0]
    ax.plot(tout, alt_tierra_km, color='blue')
    ax.set_title('Altitud (Tierra)')
    ax.set_ylabel('Altitud (km)')
    ax.grid(True)
    
    ax = axes[0, 1]
    ax.plot(tout, alt_luna_m / 1000, color='purple')
    ax.set_title('Altitud (Luna)')
    ax.set_ylabel('Altitud (km)')
    ax.grid(True)
    
    ax = axes[1, 0]
    ax.plot(tout, vel_mag, color='red')
    ax.set_title('Velocidad (Magnitud)')
    ax.set_ylabel('Velocidad (m/s)')
    ax.grid(True)
    
    ax = axes[1, 1]
    ax.plot(tout, mass, color='green')
    ax.set_title('Masa del Vehículo')
    ax.set_ylabel('Masa (kg)')
    ax.grid(True)
    
    ax = axes[2, 0]
    ax.plot(tout, g_loads, color='orange')
    ax.set_title('Cargas G (Aceleración)')
    ax.set_ylabel('Aceleración (g)')
    ax.set_xlabel('Tiempo (s)')
    ax.grid(True)
    
    ax = axes[2, 1]
    ax.plot(tout, energia_especifica, color='cyan')
    ax.set_title('Energía Orbital Específica')
    ax.set_ylabel('Energía (J/kg)')
    ax.set_xlabel('Tiempo (s)')
    ax.grid(True)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    manager = plt.get_current_fig_manager()
    if manager:
        manager.window.showMaximized()
    plt.show()





# --- [NUEVAS FUNCIONES DE PLOTEO DE LOTES] ---

def plot_batch_telemetria(batch_plot_data):
    """
    Grafica los datos de telemetría (2D) para un lote completo de simulaciones.
    """
    fig, axes = plt.subplots(3, 2, figsize=(16, 12), sharex=True)
    fig.suptitle("Resultados Comparativos del Lote (Telemetría)", fontsize=18)

    num_sims = len(batch_plot_data)
    colors = plt.cm.turbo(np.linspace(0, 1, num_sims))

    # [NUEVO] Almacenar todos los handles y labels para una leyenda unificada
    all_handles, all_labels = [], []

    for i, (result_data, sim_name) in enumerate(batch_plot_data):
        label = sim_name
        color = colors[i]

        # Asumimos que todos los datos son de 17 elementos
        (tout, x, y, z, vx, vy, vz, mass, alt_tierra_km,
         xL, yL, zL, vxL, vyL, vzL, ang_rad, desc) = result_data

        # Calcular métricas
        vel_mag = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        alt_luna_m = (np.sqrt((xL - x) ** 2 + (yL - y) ** 2 + (zL - z) ** 2) - Rluna) / 1000.0  # km
        dvx, dvy, dvz = np.gradient(vx), np.gradient(vy), np.gradient(vz)
        dt_steps = np.gradient(tout)
        dt_safe = np.where(dt_steps == 0, 1e-9, dt_steps)
        accel_x, accel_y, accel_z = dvx / dt_safe, dvy / dt_safe, dvz / dt_safe
        g_loads = np.nan_to_num(np.sqrt(accel_x ** 2 + accel_y ** 2 + accel_z ** 2) / g0)
        mu_tierra = G * mplanet
        r_tierra = np.sqrt(x ** 2 + y ** 2 + z ** 2)
        energia_especifica = (vel_mag ** 2 / 2) - mu_tierra / r_tierra

        # Graficar en cada subplot
        # Usamos 'l' para capturar el handle de la línea
        l1, = axes[0, 0].plot(tout, alt_tierra_km, color=color, label=label, alpha=0.8)
        axes[0, 1].plot(tout, alt_luna_m, color=color, label=label, alpha=0.8)
        axes[1, 0].plot(tout, vel_mag, color=color, label=label, alpha=0.8)
        axes[1, 1].plot(tout, mass, color=color, label=label, alpha=0.8)
        axes[2, 0].plot(tout, g_loads, color=color, label=label, alpha=0.8)
        axes[2, 1].plot(tout, energia_especifica, color=color, label=label, alpha=0.8)

        # Añadir el handle y label de la primera gráfica (son iguales para todas)
        all_handles.append(l1)
        all_labels.append(label)

    # Configurar títulos y etiquetas
    axes[0, 0].set_title('Altitud (Tierra)')
    axes[0, 0].set_ylabel('Altitud (km)')
    axes[0, 1].set_title('Altitud (Luna)')
    axes[0, 1].set_ylabel('Altitud (km)')
    axes[1, 0].set_title('Velocidad (Magnitud)')
    axes[1, 0].set_ylabel('Velocidad (m/s)')
    axes[1, 1].set_title('Masa del Vehículo')
    axes[1, 1].set_ylabel('Masa (kg)')
    axes[2, 0].set_title('Cargas G (Aceleración)')
    axes[2, 0].set_ylabel('Aceleración (g)')
    axes[2, 0].set_xlabel('Tiempo (s)')
    axes[2, 1].set_title('Energía Orbital Específica')
    axes[2, 1].set_ylabel('Energía (J/kg)')
    axes[2, 1].set_xlabel('Tiempo (s)')

    for ax_row in axes:
        for ax in ax_row:
            ax.grid(True, linestyle='--', alpha=0.5)

    # --- [BLOQUE DE LEYENDA MEJORADO] ---
    # Colocar la leyenda en el lado derecho de la figura
    fig.legend(all_handles, all_labels, loc='center left', bbox_to_anchor=(1.0, 0.5),
               title="Simulaciones", fontsize='small')

    # Ajustar el layout para dejar espacio a la leyenda
    # 'right=0.85' deja un 15% de espacio a la derecha
    fig.tight_layout(rect=[0, 0, 0.85, 0.96])
    # --- [FIN BLOQUE MEJORADO] ---

    manager = plt.get_current_fig_manager()
    if manager:
        manager.window.showMaximized()
    plt.show()


def plot_batch_closeup(batch_plot_data):
    """
    Grafica las trayectorias 3D (close-up) para un lote completo.
    """
    fig, ax = plt.subplots(subplot_kw={'projection': '3d'}, figsize=(12, 12))

    _load_textures()
    t_coords, t_tex, _ = tierra_coords, tierra_tex, luna_coords_base
    if isinstance(t_tex, str):
        ax.plot_surface(t_coords[0], t_coords[1], t_coords[2],
                        color=t_tex, linewidth=0, antialiased=False,
                        shade=True, alpha=0.7)
    else:
        ax.plot_surface(t_coords[0], t_coords[1], t_coords[2],
                        facecolors=t_tex, linewidth=0, antialiased=False,
                        shade=True, alpha=0.7)

    num_sims = len(batch_plot_data)
    colors = plt.cm.turbo(np.linspace(0, 1, num_sims))
    max_range_global = Rplanet * 1.5

    for i, (result_data, sim_name) in enumerate(batch_plot_data):
        label = sim_name
        color = colors[i]

        (tout, x, y, z, _, _, _, _, _, _, _, _, _, _, _, _, _) = result_data

        ax.plot(x, y, z, color=color, label=label, lw=2, alpha=0.8)

        max_range_orbital = np.max(np.sqrt(x ** 2 + y ** 2 + z ** 2))
        if max_range_orbital > max_range_global:
            max_range_global = max_range_orbital

    # --- Estética ---
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.grid(False)
    ax.set(xticks=[], yticks=[], zticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)

    max_range_global *= 1.1
    ax.set_xlim(-max_range_global, max_range_global)
    ax.set_ylim(-max_range_global, max_range_global)
    ax.set_zlim(-max_range_global, max_range_global)

    # --- [LEYENDA CONFIRMADA] ---
    # La leyenda se añade aquí
    ax.legend(title="Simulaciones")
    # -----------------------------

    plt.title("Resultados Comparativos del Lote (Trayectorias 3D)", color='white')
    plt.show()


# --- FUNCIONES ANTIGUAS (Redirigidas por compatibilidad) ---

def graf_debug_visual(data):
    """ Redirige la llamada de depuración visual a la nueva función 'graf_all'. """
    print("Redirigiendo 'graf_debug_visual' a 'graf_all'...")
    graf_all(data)


def graf_debug_basico(data):
    """ Redirige la llamada de depuración básica a la nueva función 'graf_all'. """
    print("Redirigiendo 'graf_debug_basico' a 'graf_all'...")
    graf_all(data)
# --- [NUEVA FUNCIÓN DE ANIMACIÓN] ---


# --- [NUEVA FUNCIÓN DE ANIMACIÓN MEJORADA - OO VERSION] ---
def animar_simulacion(data, output_folder="vid_sims", video_name="simulacion"):
    """
    Genera una animación .mp4/.gif con:
    1. Vista 3D (Tierra-Luna)
    2. Gráficos de Telemetría (Velocidad, Alt-Tierra, Alt-Luna)
    
    Usa 'matplotlib.figure.Figure' y 'FigureCanvasAgg' directamente
    para evitar conflictos con el backend 'QtAgg' y prevenir crashes.
    """
    import os
    import matplotlib.gridspec as gridspec
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    
    if not os.path.exists(output_folder):
        print(f"[DEBUG] Creando carpeta: {output_folder}")
        os.makedirs(output_folder)

    # 1. Desempaquetar datos
    try:
        if len(data) == 17:
             (tout, x, y, z, vx, vy, vz, mass, alt_tierra_km,
              xL, yL, zL, vxL, vyL, vzL, ang_rad, desc) = data
        elif len(data) == 16:
             (tout, x, y, z, vx, vy, vz, mass,
              xL, yL, zL, vxL, vyL, vzL, ang_rad, desc) = data
        else:
            print("Error: Datos corruptos para animación.")
            return
    except Exception as e:
        print(f"Error al desempaquetar para animación: {e}")
        return

    # Cálculos extra
    vel_mag = np.sqrt(vx**2 + vy**2 + vz**2)
    dist_luna = np.sqrt((x-xL)**2 + (y-yL)**2 + (z-zL)**2)
    alt_luna_km = (dist_luna - Rluna) / 1000.0

    print(f"Generando animación compleja '{video_name}'... (Paciencia)")

    # 2. Configurar Figura (Sin usar pyplot)
    # Estilo claro
    plt.style.use('default')
    
    fig = Figure(figsize=(14, 8))
    fig.patch.set_facecolor('white')
    
    # Es necesario asociar un Canvas para que save() funcione
    canvas = FigureCanvasAgg(fig)
    
    gs = gridspec.GridSpec(3, 3, figure=fig)

    # AX1: 3D View
    ax3d = fig.add_subplot(gs[:, :2], projection='3d')
    ax3d.set_facecolor('white')
    
    # AX2-4: Telemetry
    ax_vel = fig.add_subplot(gs[0, 2])
    ax_vel.set_title("Velocidad (m/s)", color='black', fontsize=10)
    
    ax_altE = fig.add_subplot(gs[1, 2])
    ax_altE.set_title("Altitud Tierra (km)", color='black', fontsize=10)
    
    ax_altM = fig.add_subplot(gs[2, 2])
    ax_altM.set_title("Altitud Luna (km)", color='black', fontsize=10)

    # --- Configurar 3D Scene ---
    _load_textures()
    t_coords, t_tex, l_coords = tierra_coords, tierra_tex, luna_coords_base

    # Tierra Estática
    if isinstance(t_tex, str):
        ax3d.plot_surface(t_coords[0], t_coords[1], t_coords[2], color=t_tex, 
                          linewidth=0, shade=False, alpha=0.8)
    else:
        ax3d.plot_surface(t_coords[0], t_coords[1], t_coords[2], facecolors=t_tex, 
                          linewidth=0, shade=False, alpha=0.8)

    # Elementos dinámicos 3D
    rocket_pt, = ax3d.plot([], [], [], 'o', color='red', markersize=5, label='Cohete')
    rocket_tr, = ax3d.plot([], [], [], '-', color='red', lw=1, alpha=0.6)
    moon_pt, = ax3d.plot([], [], [], 'o', color='gray', markersize=8, label='Luna')
    moon_tr, = ax3d.plot([], [], [], '--', color='gray', lw=0.5, alpha=0.5)

    # Fix Ejes 3D
    max_range = np.max(np.abs(np.array([x, y, z, xL, yL, zL]))) * 1.1
    ax3d.set_xlim(-max_range, max_range)
    ax3d.set_ylim(-max_range, max_range)
    ax3d.set_zlim(-max_range, max_range)
    ax3d.grid(False)
    ax3d.set_axis_off()
    
    time_txt = ax3d.text2D(0.05, 0.95, "T=0 s", transform=ax3d.transAxes, color='black')

    # --- Configurar Gráficos Laterales ---
    ax_vel.plot(tout, vel_mag, color='blue', alpha=0.3)
    ax_altE.plot(tout, alt_tierra_km, color='green', alpha=0.3)
    ax_altM.plot(tout, alt_luna_km, color='purple', alpha=0.3)
    
    line_v_vel = ax_vel.axvline(x=0, color='black', lw=1, linestyle='--')
    line_v_altE = ax_altE.axvline(x=0, color='black', lw=1, linestyle='--')
    line_v_altM = ax_altM.axvline(x=0, color='black', lw=1, linestyle='--')
    
    pt_vel, = ax_vel.plot([], [], 'o', color='blue')
    pt_altE, = ax_altE.plot([], [], 'o', color='green')
    pt_altM, = ax_altM.plot([], [], 'o', color='purple')

    for ax in [ax_vel, ax_altE, ax_altM]:
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.patch.set_facecolor('white')
        ax.tick_params(colors='black')
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
    
    fig.tight_layout()

    # --- SETUP ANIMACIÓN ---
    skip = max(1, len(tout) // 300) 
    indices = range(0, len(tout), skip)

    def update(frame_idx):
        t_curr = tout[frame_idx]
        
        # 1. Update 3D
        rocket_pt.set_data([x[frame_idx]], [y[frame_idx]])
        rocket_pt.set_3d_properties([z[frame_idx]])
        rocket_tr.set_data(x[:frame_idx], y[:frame_idx])
        rocket_tr.set_3d_properties(z[:frame_idx])

        moon_pt.set_data([xL[frame_idx]], [yL[frame_idx]])
        moon_pt.set_3d_properties([zL[frame_idx]])
        moon_tr.set_data(xL[:frame_idx], yL[:frame_idx])
        moon_tr.set_3d_properties(zL[:frame_idx])
        
        time_txt.set_text(f"T={t_curr:.1f} s")

        # 2. Update 2D
        line_v_vel.set_xdata([t_curr])
        pt_vel.set_data([t_curr], [vel_mag[frame_idx]])
        
        line_v_altE.set_xdata([t_curr])
        pt_altE.set_data([t_curr], [alt_tierra_km[frame_idx]])
        
        line_v_altM.set_xdata([t_curr])
        pt_altM.set_data([t_curr], [alt_luna_km[frame_idx]])

        return (rocket_pt, rocket_tr, moon_pt, moon_tr, time_txt, 
                line_v_vel, pt_vel, line_v_altE, pt_altE, line_v_altM, pt_altM)

    anim = FuncAnimation(fig, update, frames=indices, interval=30, blit=False)
    
    # --- GUARDADO ---
    file_path = os.path.join(output_folder, f"{video_name}.mp4")
    
    try:
        # Intento MP4
        anim.save(file_path, writer='ffmpeg', fps=30, dpi=100)
        print(f"Animación guardada: {file_path}")
    except Exception as e:
        print(f"Fallo MP4 ({e}). Intentando GIF...")
        try:
             gif_path = os.path.join(output_folder, f"{video_name}.gif")
             anim.save(gif_path, writer='pillow', fps=30)
             print(f"GIF guardado: {gif_path}")
        except Exception as e2:
             print(f"Error fatal guardando video: {e2}")

    # No llamamos a plt.close(fig) porque 'fig' no es manejada por pyplot.
    # Simplemente dejamos que se limpie por scope o garbage collection.
    # Esto elimina el conflicto con QtAgg.


