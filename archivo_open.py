import numpy as np

##### CONSTANTES FÍSICAS #####
Rplanet = 6_357_000.0  # [m]


class AdminResultasosSim:
    # [MODIFICADO] __init__ ahora acepta 'num_encendidos'
    def __init__(self, name, description, posx, posy, posz, velx, vely, velz, mass,
                 alt_tierra_km,
                 poslx, posly, poslz, vellx, velly, vellz, tout, ang,
                 num_encendidos):  # <-- Nuevo parámetro
        self.name = name
        self.description = description
        self.posx = posx
        self.posy = posy
        self.posz = posz
        self.velx = velx
        self.vely = vely
        self.velz = velz
        self.mass = mass
        self.alt_tierra_km = alt_tierra_km
        self.poslx = poslx
        self.posly = posly
        self.poslz = poslz
        self.vellx = vellx
        self.velly = velly
        self.vellz = vellz
        self.tout = tout
        self.ang = ang
        self.num_encendidos = num_encendidos  # <-- Nuevo atributo

    def __str__(self):
        return (f"Lanzamiento {self.name}:\n"
                f"Description: {self.description}\n"
                f"Encendidos activos (estimados si es antiguo): {self.num_encendidos}\n")

    def graf_data(self):
        """Retorna la tupla de 17 elementos que 'graf_all' espera."""
        # 'num_encendidos' NO se pasa a graf_all. Se queda en el objeto.
        return (self.tout, self.posx, self.posy, self.posz,
                self.velx, self.vely, self.velz, self.mass,
                self.alt_tierra_km,
                self.poslx, self.posly, self.poslz,
                self.vellx, self.velly, self.vellz,
                self.ang, self.description)

    # ... (el resto de print_types y print_len sin cambios) ...


def getdata():
    """Carga los archivos .npz y los convierte en objetos AdminResultasosSim."""

    keys_file_path = "log_simulaciones/Nombres_Sim.txt"
    keys = []

    try:
        with open(keys_file_path, "r") as keys_sim:
            keys = keys_sim.read().splitlines()
    except FileNotFoundError:
        print(f"Error: El archivo '{keys_file_path}' no existe.")
        return {}

    simulaciones = {}
    for key in keys:
        try:
            file_path = "log_simulaciones/" + key + ".npz"
            data = np.load(file_path, allow_pickle=True)

            sim_name = str(data.get('name'))
            sim_desc = str(data.get('description'))

            # --- [BLOQUE DE RETROCOMPATIBILIDAD 1: alt_tierra_km] ---
            try:
                sim_alt_km = data['alt_tierra_km']
            except KeyError:
                print(f"  -> Adv: 'alt_tierra_km' no encontrado en {key}. Calculando manualmente.")
                sim_alt_km = (np.sqrt(
                    data['position_x'] ** 2 + data['position_y'] ** 2 + data['position_z'] ** 2) - Rplanet) / 1000.0

            # --- [BLOQUE DE RETROCOMPATIBILIDAD 2: num_encendidos] ---
            try:
                sim_num_encendidos = int(data['num_encendidos'])
            except KeyError:
                # Estimación de fallback para simulaciones antiguas
                fallback_num_encendidos = 3
                sim_num_encendidos = fallback_num_encendidos
            # --- [FIN BLOQUES] ---

            sim_obj = AdminResultasosSim(
                name=sim_name,
                description=sim_desc,
                posx=data['position_x'],
                posy=data['position_y'],
                posz=data['position_z'],
                velx=data['velocity_x'],
                vely=data['velocity_y'],
                velz=data['velocity_z'],
                mass=data['mass'],
                alt_tierra_km=sim_alt_km,
                poslx=data['L_pos_x'],
                posly=data['L_pos_y'],
                poslz=data['L_pos_z'],
                vellx=data['L_vel_x'],
                velly=data['L_vel_y'],
                vellz=data['L_vel_z'],
                tout=data['time'],
                ang=data['ang'],
                num_encendidos=sim_num_encendidos  # <-- Pasando el valor
            )

            simulaciones[sim_name] = sim_obj

        except FileNotFoundError:
            print(f"  -> Advertencia: No se encontró el archivo '{key}'.")
        except KeyError as e:
            print(f"  -> Error: La clave {e} no se encontró en el archivo '{key}'. El archivo puede estar corrupto.")

    return simulaciones


if __name__ == "__main__":
    print("Ejecutando prueba de carga de datos...\n")
    sims_cargadas = getdata()
    if sims_cargadas:
        print(f"Prueba exitosa: Se cargaron {len(sims_cargadas)} simulaciones.")
        primer_nombre = list(sims_cargadas.keys())[0]
        primera_sim = sims_cargadas[primer_nombre]
        print("Datos de la primera simulación:")
        print(primera_sim)
    else:
        print("Prueba finalizada: No se encontraron simulaciones.")