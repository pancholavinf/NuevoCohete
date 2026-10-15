# Documentación Técnica - NuevoCohete

Bienvenido al directorio de documentación técnica del simulador de trayectorias y misiones espaciales **NuevoCohete**.

Este directorio centraliza los documentos técnicos, arquitectura del software, descripción de modelos físicos, funciones clave y guías de desarrollo del proyecto.

---

## 📂 Contenido del Directorio

| Archivo | Descripción |
| :--- | :--- |
| [`manual_tecnico_completo.md`](./manual_tecnico_completo.md) | **Manual técnico integral y arquitectura**: física, solvers astrodinámicos, pipeline de renderizado y flujos. |
| [`objetivos.md`](./objetivos.md) | Objetivos principales y secundarios del simulador, casos de uso y metas a corto/largo plazo. |
| [`funciones_clave.md`](./funciones_clave.md) | Catálogo de módulos, funciones críticas, firmas, entradas/salidas y flujo de ejecución. |
| [`arquitectura_y_datos.md`](./arquitectura_y_datos.md) | Modelo físico (3 cuerpos restringido, empuje, masa), vector de estado y estructura de la tupla de 17 elementos. |

---

## 🚀 Resumen Rápido del Proyecto

**NuevoCohete** es una plataforma de simulación orbital y de misiones cislunares escrita en Python. Permite:
1. Modelar etapas de propulsión con empuje vectorial variable en el tiempo.
2. Simular dinámicas orbitales bajo influencia gravitatoria combinada de la Tierra y la Luna.
3. Calcular maniobras orbitales complejas:
   - **TLI (Trans-Lunar Injection)**: Inyección translunar optimizada o numérica.
   - **LOI (Lunar Orbit Insertion)**: Captura e inserción en órbita lunar.
4. Unir (*stitch*) múltiples fases de vuelo en una trayectoria continua.
5. Visualizar trayectorias en 3D (geocéntricas y selenocéntricas), telemetría y generar animaciones de video.
