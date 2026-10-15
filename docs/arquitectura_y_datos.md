# Arquitectura de Datos y Modelos Físicos

Este documento define la estructura de datos interna y los fundamentos físicos utilizados en las simulaciones de **NuevoCohete**.

---

## 🌌 1. Modelo Físico y Ecuaciones de Movimiento

El sistema se modela como un problema restringido de 3 cuerpos (Tierra, Luna y Vehículo Espacial), donde la masa del cohete es despreciable respecto a la masa de los cuerpos primarios.

### Vector de Estado
El estado del vehículo en cualquier instante $t$ está representado por un vector de 7 componentes:
$$\vec{S}(t) = \begin{bmatrix} x \\ y \\ z \\ v_x \\ v_y \\ v_z \\ m \end{bmatrix}$$

### Ecuación Diferencial:
$$\frac{d\vec{S}}{dt} = \begin{bmatrix}
v_x \\
v_y \\
v_z \\
a_{g,\oplus,x} + a_{g,\text{Luna},x} + a_{T,x} \\
a_{g,\oplus,y} + a_{g,\text{Luna},y} + a_{T,y} \\
a_{g,\oplus,z} + a_{g,\text{Luna},z} + a_{T,z} \\
-\dot{m}
\end{bmatrix}$$

Donde:
- $\vec{a}_{g,\oplus} = -\frac{\mu_\oplus}{||\vec{r}||^3} \vec{r}$
- $\vec{a}_{g,\text{Luna}} = -\mu_{\text{Luna}} \left( \frac{\vec{r} - \vec{r}_{\text{Luna}}}{||\vec{r} - \vec{r}_{\text{Luna}}||^3} + \frac{\vec{r}_{\text{Luna}}}{||\vec{r}_{\text{Luna}}||^3} \right)$
- $\vec{a}_T = \frac{\vec{F}_T(t)}{m(t)}$ (aceleración por empuje de cohetes)
- $\dot{m} = \sum_i \frac{F_{T,i}}{I_{sp,i} \cdot g_0}$

---

## 📊 2. Estructura de la Tupla de Resultados (17 Elementos)

Las funciones principales de integración (`calc_sim`, `craft_sim_results`, etc.) intercambian la telemetría en una tupla indexada de 17 posiciones:

| Índice | Variable | Tipo / Unidad | Descripción |
| :---: | :--- | :--- | :--- |
| `0` | `tout` | `np.ndarray` (s) | Vector temporal de la simulación |
| `1` | `x` | `np.ndarray` (m) | Posición inercial X del vehículo |
| `2` | `y` | `np.ndarray` (m) | Posición inercial Y del vehículo |
| `3` | `z` | `np.ndarray` (m) | Posición inercial Z del vehículo |
| `4` | `vx` | `np.ndarray` (m/s) | Velocidad inercial X del vehículo |
| `5` | `vy` | `np.ndarray` (m/s) | Velocidad inercial Y del vehículo |
| `6` | `vz` | `np.ndarray` (m/s) | Velocidad inercial Z del vehículo |
| `7` | `mass` | `np.ndarray` (kg) | Masa total instantánea del vehículo |
| `8` | `alt_km` | `np.ndarray` (km) | Altitud sobre la superficie media de la Tierra |
| `9` | `xL` | `np.ndarray` (m) | Posición X de la Luna |
| `10` | `yL` | `np.ndarray` (m) | Posición Y de la Luna |
| `11` | `zL` | `np.ndarray` (m) | Posición Z de la Luna |
| `12` | `vxL` | `np.ndarray` (m/s) | Componente X de velocidad de la Luna |
| `13` | `vyL` | `np.ndarray` (m/s) | Componente Y de velocidad de la Luna |
| `14` | `vzL` | `np.ndarray` (m/s) | Componente Z de velocidad de la Luna |
| `15` | `config` | `ConfigSim` / `dict` | Configuración y parámetros utilizados |
| `16` | `metadata` | `dict` | Tiempos de cálculo, estado de finalización y notas |

---

## 💾 3. Organización de Almacenamiento

- **`log_simulaciones/`**: Almacena las corridas serializadas con fecha, hora y configuración para evitar tener que re-calcular trayectorias prolongadas.
- **`vid_sims/`**: Almacena las animaciones renderizadas generadas por `grf_data.py`.
- **`docs/`**: Archivos técnicos, documentación de arquitectura y bitácoras de diseño.
