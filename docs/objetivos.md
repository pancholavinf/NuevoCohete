# Objetivos del Proyecto - NuevoCohete

Este documento define la visión, metas y alcances técnicos del simulador orbital **NuevoCohete**.

---

## 🎯 Objetivo General

Desarrollar un entorno de simulación numérica robusto, modular y extensible en Python para modelar trayectorias de vehículos espaciales desde órbitas bajas terrestres (LEO) hasta el sistema cislunar y órbita lunar, facilitando el diseño y análisis de misiones translunares.

---

## 📌 Objetivos Específicos

### 1. Modelado Físico y Gravitatorio de Alta Precisión
- Implementar la dinámica de vuelo en un marco inercial 3D considerando:
  - Gravedad de la Tierra como cuerpo central ($GM_{\oplus}$).
  - Perturbaciones gravitacionales lunares de tercer cuerpo ($GM_{Luna}$).
  - Movimiento orbital analítico o numérico de la Luna.
  - Efectos atmosféricos en fases bajas (cuando aplique) y condiciones de terminación (impacto contra la superficie terrestre o lunar).

### 2. Planificación y Cálculo de Maniobras (Astrodinámica)
- **TLI (Trans-Lunar Injection):**
  - Implementar solvers numéricos y analíticos para calcular el $\Delta V$ necesario para elevar el apogeo hasta la distancia orbital de la Luna ($\approx 384,400\text{ km}$).
  - Permitir quemados tangenciales progrado calculados dinámicamente desde el estado actual del vehículo.
- **Predicción de Encuentros y Esferas de Influencia:**
  - Detectar el paso del vehículo por la esfera de influencia lunar (SoI) o aproximación mínima (*perilunio*).
- **LOI (Lunar Orbit Insertion):**
  - Calcular quemados de frenado retrógrado para capturar la nave en órbita lunar cerrada a alturas deseadas.

### 3. Simulación Multi-Fase y Composición de Maniobras
- Proveer un mecanismo de unión secuencial (*stitching* / `craft_sim_results`) que permita encadenar fases de vuelo:
  - Fase 1: Órbita de estacionamiento.
  - Fase 2: Maniobra de encendido TLI.
  - Fase 3: Vuelo de crucero Tierra-Luna.
  - Fase 4: Maniobra LOI / Correcciones de trayectoria.
- Mantener la continuidad física del tiempo, masa, posición y vector velocidad entre fases.

### 4. Telemetría, Análisis Gráfico y Visualización
- Generar visualizaciones claras del sistema Tierra-Luna a escala:
  - Vista general del sistema completo (inercial geocéntrico).
  - Vistas de aproximación (*close-up*) a la Tierra y a la Luna (marco selenocéntrico).
  - Perfiles de telemetría: altitud vs. tiempo, velocidad vs. tiempo, masa vs. tiempo y distancias relativas.
- Exportar animaciones y videos de la trayectoria (`vid_sims/`).

### 5. Persistencia y Reproducibilidad
- Guardar estados completos de simulación en disco (`log_simulaciones/`) para análisis retrospectivo, exportación de datos y reanudación de simulaciones.
- Soportar simulaciones preconfiguradas, manuales e iteraciones por lotes (*batch simulations*).

---

## 📈 Roadmap y Metas Futuras
- [ ] Incorporar perturbaciones de armónicos zonales terrestres ($J_2$).
- [ ] Soporte para efemérides lunares de alta precisión (SPICE o JPL DE4xx).
- [ ] Optimización automática de trayectorias (algoritmos genéticos o SQP para minimización de $\Delta V$).
- [ ] Simulación de reentrada atmosférica con modelos térmicos simplificados.
