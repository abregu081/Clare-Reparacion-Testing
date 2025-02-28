# Process.py
import os
import sys
import importlib

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

# 1) Leemos la lista de módulos.
#    setting["Modulos"] podría ser una lista o un string. 
#    Si es un string "AutoTest, Segurity, ManualInspection", lo transformamos a lista:
if isinstance(setting.get("Modulos", []), str):
    module_list = [m.strip() for m in setting["Modulos"].split(",")]
else:
    module_list = setting.get("Modulos", [])

# 2) Para cada módulo, construimos la ruta del directorio. 
#    Ej: si módulo = "AutoTest", buscamos "Directorio_AutoTest" en el CFG.
#    Lo guardamos en un dict para uso posterior.
modules_info = {}  # { "AutoTest": {"path": "...", "functions": ...}, ... }

for mod_name in module_list:
    # clave de CFG: Directorio_<mod_name>
    cfg_key = f"Directorio_{mod_name}"
    mod_path = setting.get(cfg_key, None)
    if not mod_path:
        # Si no encuentra la clave, avisa o ignora
        print(f"[WARN] No se encontró la ruta para el módulo '{mod_name}'. Revisar Parametros.cfg")
        continue

    # 3) Importación dinámica del archivo Funciones.py en la carpeta 'Modulos/<mod_name>'
    #    Asumimos que la carpeta 'Modulos' está en la misma ubicación que este script, 
    #    o en el PYTHONPATH. De lo contrario, habrá que ajustar la ruta.
    try:
        # importlib.import_module("Modulos.AutoTest.Funciones")
        module_ref = importlib.import_module(f"Modulos.{mod_name}.Funciones")
        # Guardamos en un diccionario las funciones de búsqueda, procesado e historial 
        # (ajusta los nombres según los que uses en cada Funciones.py)
        buscar_fn = getattr(module_ref, f"buscar_archivo_{mod_name.lower()}")
        procesar_fn = getattr(module_ref, f"procesar_archivo_{mod_name.lower()}")
        historial_fn = getattr(module_ref, f"rutaHistorial_archivo_{mod_name.lower()}")
        
        modules_info[mod_name] = {
            "path": mod_path,
            "buscar": buscar_fn,
            "procesar": procesar_fn,
            "historial": historial_fn
        }
    except ImportError as e:
        print(f"[ERROR] No se pudo importar el módulo {mod_name}: {e}")
    except AttributeError as e:
        print(f"[ERROR] Función faltante en {mod_name}: {e}")

# variables globales o acceso desde main
MODULES_INFO = modules_info
