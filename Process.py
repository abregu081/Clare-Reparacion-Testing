#Modulo de funciones de procesamiento de la app y lectura de parametros
import os
import sys

#funcion para leer el archivo de configuracion 
def read_setting(file):
    setting = {}
    with open(file, 'r') as f:
        for line in f:
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            if "=" in line:
                key, value = line.strip().split('=')
                value = value.strip()
                if "," in value:
                    setting[key.strip()] = [v.strip() for v in value.split(",")]
                else:
                    setting[key.strip()] = value
    return setting

def obtener_ruta_cfg():
    current_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    cfg_file = os.path.join(current_directory, "Parametros.cfg")
    return cfg_file


cfg_file = obtener_ruta_cfg()
setting = read_setting(cfg_file)

#ruta de los directorios
Autotest_path = setting.get("Directorio_Autotest","")
Segurity_path = setting.get("Directorio_Segurity","")
ManualInspection_path = setting.get("Directorio_ManualInspeccion","")

