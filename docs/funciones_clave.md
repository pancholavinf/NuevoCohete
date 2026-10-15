# Funciones Clave y Módulos del Sistema

Este documento describe la arquitectura modular y las funciones críticas del proyecto **NuevoCohete**.

---

## 🧭 Mapa de Módulos

```
NuevoCohete/
├── main.py              # Orquestador del flujo principal, menús y concatenación
├── modelo_3d.py         # Motor físico e integración numérica (solve_ivp)
├── calc_luna.py         # Algoritmos de astrodinámica lunar (TLI, LOI, encuentros)
├── new_sim.py           # Estructuras de configuración de vuelo y presets
├── grf_data.py          # Gráficos 2D/3D, telemetría y renderizado de video
├── archivo_new.py       # Serialización y persistencia de simulaciones
└── archivo_open.py      # Carga e inspección de simulaciones archivadas
```

---

## 1. `modelo_3d.py` — Motor Físico

El núcleo de simulación numérica responsable de calcular la evolución temporal del estado del cohete.

### `calc_sim(config: ConfigSim)`
- **Descripción:** Ejecuta la integración numérica de las ecuaciones de movimiento usando `scipy.integrate.solve_ivp`.
- **Entrada:** Objeto `ConfigSim` con condiciones iniciales, parámetros de empuje y duración.
- **Salida:** Tupla estandarizada de 17 arrays con la telemetría completa.
- **Eventos:** Detecta impactos con la superficie de la Tierra o la Luna para detener la integración si ocurre una colisión.

### `get_thrust_vector(t, config: ConfigSim, current_mass)`
- **Descripción:** Calcula el vector tridimensional de fuerza de empuje $\vec{F}_T = [F_x, F_y, F_z]$ en Newtons en el tiempo $t$.
- **Detalle:** Itera sobre la lista de encendidos activos y descompone la magnitud según los ángulos de orientación esférica ($\theta$ y $\beta$).

### `get_mass_flow_rate(t, config: ConfigSim)`
- **Descripción:** Determina la tasa de consumo de propelente ($\dot{m} = \frac{F}{I_{sp} \cdot g_0}$).
- **Efecto:** Reduce continuamente la masa del vehículo durante los encendidos activos.

---

## 2. `calc_luna.py` — Astrodinámica y Maniobras Lunares

Módulo especializado en maniobras de transferencia Tierra-Luna.

### `find_moon_intercept(base_config, r_target=None)`
- **Descripción:** Solver numérico que calcula el impulso $\Delta V$ necesario para fijar el apogeo a la distancia lunar ($\approx 384,400\text{ km}$).
- **Particularidad:** No asume que el vehículo está exactamente en el perigeo; proyecta el quemado tangencial a la velocidad actual en cualquier punto de la órbita.

### `calculate_loi(...)`
- **Descripción:** Calcula el frenado retrógrado requerido en el perilunio para capturar la trayectoria hiperbólica en una elipse u órbita circular alrededor de la Luna.

### `calculate_encounter_prediction(...)`
- **Descripción:** Analiza una trayectoria dada para proyectar la distancia mínima a la Luna, tiempo de paso por el perilunio y velocidad de aproximación relativa.

---

## 3. `main.py` — Orquestación y Conexión de Fases

### `craft_sim_results(sim_activa, result_iter_tuple, config_iter_obj, time0)`
- **Descripción:** Une (*stitches*) dos simulaciones: una previa y una posterior iniciada a partir del índice temporal `time0`.
- **Algoritmo de unión:**
  1. Corta el segmento antiguo hasta `time0`.
  2. Ajusta el vector temporal `tout` de la nueva simulación sumando el último instante de la primera.
  3. Concatena los arrays de estado espacial `[x, y, z, vx, vy, vz, mass, alt_km, xL, yL, zL, vxL, vyL, vzL]`.
  4. Preserva y actualiza metadatos y configuraciones.

### `ran_new_sim()`
- **Descripción:** Menú interactivo que permite seleccionar perfiles rápidos (ej. Órbita 100 km High DV, Órbita 400 km coplanar con la Luna, o configuración manual), disparar la integración y guardar los resultados.

---

## 4. `new_sim.py` — Configuraciones y Presets

### `ConfigSim`
- **Clase principal** que almacena:
  - Vector de estado inicial: `x0, y0, z0, vx0, vy0, vz0`.
  - Masa inicial: `m0`.
  - Matriz de encendidos: `[t_inicio, duracion, empuje, Isp, theta, beta]`.
  - Parámetros de integración: paso de tiempo, duración total, tolerancias relativas/absolutas.

### Presets disponibles:
- `config_high_dv_orbit()`: Inyección rápida con alto delta-V en órbita baja.
- `config_400km_moon_plane()`: Establece el vehículo a 400 km en el plano orbital de la Luna para optimizar la geometría de TLI.
- `config_batch_from_template()`: Generación de barridos paramétricos para análisis de dispersión y optimización.

---

## 5. `grf_data.py` — Visualización y Telemetría

### `graf_all(result)`
- Genera el conjunto completo de análisis visual:
  - Órbita 3D global.
  - Telemetría en subplots (altitud, velocidad, aceleración y masa).
  - Vistas geocéntricas y selenocéntricas.

### `plot_moon_centered(...)`
- Transforma las coordenadas inerciales a un sistema centrado en la Luna para evaluar perigeo lunar, inserción en órbita y flybys.

### `animar_simulacion(...)`
- Compila fotogramas y genera archivos `.mp4` en `vid_sims/` mostrando la cinemática de la misión con texturas esféricas de la Tierra y la Luna.

---

## 6. `archivo_new.py` y `archivo_open.py` — Persistencia

- **`guardar_simulacion(result)`**: Empaqueta los datos procesados en archivos binarios o estructurados dentro de `log_simulaciones/`.
- **`getdata(path)`**: Carga simulaciones previas para re-graficar, contrastar o continuar fases de vuelo.
