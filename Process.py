import os
import sys
import importlib
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime

# -------------------------------
# FUNCIONES DE LECTURA/ESCRITURA CFG
# -------------------------------
def read_setting(file):
    setting = {}
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            if "=" in line:
                key, value = line.strip().split('=', 1)
                value = value.strip()
                if "," in value:
                    setting[key.strip()] = [v.strip() for v in value.split(",")]
                else:
                    setting[key.strip()] = value
    return setting

def write_settings_in_process(file_path, settings_dict):
    """
    Escribe el diccionario settings_dict en el archivo file_path.
    Si un valor es lista, lo convierte en una cadena separada por comas.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for key, value in settings_dict.items():
                if isinstance(value, list):
                    value = ", ".join(value)
                f.write(f"{key}={value}\n")
    except Exception as e:
        print(f"[ERROR] Al escribir configuración: {e}")

def obtener_ruta_cfg():
    current_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    cfg_file = os.path.join(current_directory, "Parametros.cfg")
    return cfg_file

cfg_file = obtener_ruta_cfg()
setting = read_setting(cfg_file)

# -------------------------------
# FUNCIONES PARA MANEJAR LOS MÓDULOS
# -------------------------------
def scan_modulos_folder():
    """
    Escanea la carpeta 'Modulos' en la raíz del proyecto y devuelve
    una lista con el nombre de cada subdirectorio (cada módulo).
    """
    project_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    modulos_dir = os.path.join(project_dir, "Modulos")
    if not os.path.exists(modulos_dir) or not os.path.isdir(modulos_dir):
        return []
    modules_found = []
    for entry in os.listdir(modulos_dir):
        full_path = os.path.join(modulos_dir, entry)
        if os.path.isdir(full_path):
            modules_found.append(entry)
    return modules_found

def actualizar_config_modulos(cfg_file):
    """
    Escanea la carpeta 'Modulos' y actualiza la configuración:
      - Agrega a la clave "Modulos" los nombres detectados que no estén ya registrados.
      - Para cada módulo nuevo, crea la clave 'Directorio_<Modulo>' con valor vacío.
    """
    config = read_setting(cfg_file)
    
    # Obtener módulos ya configurados (se maneja tanto string como lista)
    mod_value = config.get("Modulos", [])
    if isinstance(mod_value, str):
        modulos_config = [m.strip() for m in mod_value.split(",") if m.strip()]
    else:
        modulos_config = mod_value

    modulos_en_carpeta = scan_modulos_folder()
    nuevos = False
    for mod in modulos_en_carpeta:
        if mod not in modulos_config:
            modulos_config.append(mod)
            config[f"Directorio_{mod}"] = ""  # Valor vacío hasta que el usuario lo configure
            nuevos = True

    config["Modulos"] = modulos_config
    if nuevos:
        write_settings_in_process(cfg_file, config)
    return config

# -------------------------------
# FUNCIONES ADICIONALES
# -------------------------------
def normalize_drive_letter(path):
    """
    Si la ruta es absoluta y tiene formato de Windows (por ejemplo, 'd:\...'),
    fuerza la letra de la unidad a mayúscula.
    """
    if path and len(path) >= 2 and path[1] == ":":
        return path[0].upper() + path[1:]
    return path

# -------------------------------
# IMPORTACIÓN DINÁMICA DE FUNCIONES DE LOS MÓDULOS
# -------------------------------
if isinstance(setting.get("Modulos", []), str):
    module_list = [m.strip() for m in setting["Modulos"].split(",") if m.strip()]
else:
    module_list = setting.get("Modulos", [])

project_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
modules_info = {}
for mod_name in module_list:
    # Obtener ruta desde "Directorio_" o "RutaModulo_"
    cfg_key = f"Directorio_{mod_name}"
    mod_path = str(setting.get(cfg_key, "")).strip()
    mod_path = normalize_drive_letter(mod_path)
    if not mod_path:
        ruta_key = f"RutaModulo_{mod_name}"
        mod_path = str(setting.get(ruta_key, "")).strip()
        mod_path = normalize_drive_letter(mod_path)
        if not mod_path:
            default_path = os.path.join(project_dir, "Modulos", mod_name)
            mod_path = default_path
            if os.path.exists(default_path):
                print(f"[INFO] Se usó la ruta por defecto para el módulo '{mod_name}': {mod_path}")
            else:
                print(f"[WARN] No se encontró la ruta para el módulo '{mod_name}', se asignará ruta por defecto: {mod_path}")

    # Leer y convertir la bandera de habilitación del módulo
    enabled_value = setting.get(f"{mod_name}_enabled", "True").strip().lower()
    enabled_bool = False if enabled_value in ("false", "0", "no") else True

    try:
        module_ref = importlib.import_module(f"Modulos.{mod_name}.Funciones")
        buscar_fn = getattr(module_ref, f"buscar_archivo_{mod_name.lower()}")
        procesar_fn = getattr(module_ref, f"procesar_archivo_{mod_name.lower()}")
        historial_fn = getattr(module_ref, f"rutaHistorial_archivo_{mod_name.lower()}")
        modules_info[mod_name] = {
            "path": mod_path,
            "buscar": buscar_fn,
            "procesar": procesar_fn,
            "historial": historial_fn,
            "enabled": enabled_bool
        }
    except Exception as e:
        print(f"[ERROR] Error al cargar el módulo {mod_name}: {e}")
        modules_info[mod_name] = {
            "path": mod_path,
            "buscar": None,
            "procesar": None,
            "historial": None,
            "enabled": enabled_bool
        }

MODULES_INFO = modules_info

# -------------------------------
# FUNCIONES GUI PARA ADMINISTRAR MÓDULOS
# -------------------------------
def eliminar_modulos_gui(root, cfg_file):
    """
    Muestra una ventana con checkboxes para que el usuario seleccione
    qué módulos desea eliminar de la configuración.
    """
    config = read_setting(cfg_file)
    mod_value = config.get("Modulos", [])
    if isinstance(mod_value, str):
        modulos_config = [m.strip() for m in mod_value.split(",") if m.strip()]
    else:
        modulos_config = mod_value

    if not modulos_config:
        messagebox.showinfo("Información", "No hay módulos configurados para eliminar.")
        return

    top = tk.Toplevel(root)
    top.title("Eliminar Módulos")

    vars_dict = {}
    for i, mod in enumerate(modulos_config):
        var = tk.BooleanVar()
        chk = tk.Checkbutton(top, text=mod, variable=var)
        chk.grid(row=i, column=0, sticky="w", padx=5, pady=5)
        vars_dict[mod] = var

    def confirmar():
        mods_a_eliminar = [mod for mod, var in vars_dict.items() if var.get()]
        if not mods_a_eliminar:
            messagebox.showinfo("Información", "No se seleccionó ningún módulo.")
            return
        for mod in mods_a_eliminar:
            if mod in modulos_config:
                modulos_config.remove(mod)
            directorio_key = f"Directorio_{mod}"
            if directorio_key in config:
                del config[directorio_key]
            enabled_key = f"{mod}_enabled"
            if enabled_key in config:
                del config[enabled_key]
        config["Modulos"] = modulos_config
        write_settings_in_process(cfg_file, config)
        messagebox.showinfo("Información", "Módulos eliminados correctamente.")
        top.destroy()

    btn_confirm = tk.Button(top, text="Eliminar seleccionados", command=confirmar)
    btn_confirm.grid(row=len(modulos_config), column=0, padx=5, pady=10)

def agregar_modulos_gui(root, cfg_file):
    """
    Escanea la carpeta 'Modulos' y compara con los módulos ya configurados.
    Muestra una ventana con checkboxes para los nuevos módulos encontrados.
    Luego, se ofrecen dos opciones:
      - "Agregar Seleccionados": Agrega automáticamente los módulos seleccionados
         con la ruta por defecto (donde se encontró el módulo) y con el directorio de seguimiento vacío.
      - "Avanzar": Abre un formulario de detalles para configurar manualmente (opcional).
    """
    config = read_setting(cfg_file)
    mod_value = config.get("Modulos", [])
    if isinstance(mod_value, str):
        modulos_config = [m.strip() for m in mod_value.split(",") if m.strip()]
    else:
        modulos_config = mod_value

    nuevos_modulos = scan_modulos_folder()
    modulos_nuevos = [m for m in nuevos_modulos if m not in modulos_config]

    if not modulos_nuevos:
        messagebox.showinfo("Información", "No se encontraron nuevos módulos para agregar.")
        return

    top = tk.Toplevel(root)
    top.title("Agregar Nuevos Módulos")

    vars_dict = {}
    ttk.Label(top, text="Seleccione los módulos a agregar:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    for i, mod in enumerate(modulos_nuevos, start=1):
        var = tk.BooleanVar()
        chk = tk.Checkbutton(top, text=mod, variable=var)
        chk.grid(row=i, column=0, sticky="w", padx=5, pady=2)
        vars_dict[mod] = var

    project_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    def agregar_automaticamente():
        seleccionados = [mod for mod, var in vars_dict.items() if var.get()]
        if not seleccionados:
            messagebox.showinfo("Información", "No se seleccionó ningún módulo.")
            return
        settings = read_setting(cfg_file)
        mod_value = settings.get("Modulos", [])
        if isinstance(mod_value, str):
            modulos_list = [m.strip() for m in mod_value.split(",") if m.strip()]
        else:
            modulos_list = mod_value
        for mod in seleccionados:
            new_name = mod
            new_mod_path = os.path.join(project_dir, "Modulos", mod)
            new_tracking_dir = ""  # Por defecto vacío
            funciones_path = os.path.join(new_mod_path, "Funciones.py")
            if not os.path.exists(funciones_path):
                messagebox.showerror("Error", f"No se encontró 'Funciones.py' en la ruta del módulo:\n{new_mod_path}")
                return
            if new_name in modulos_list:
                messagebox.showerror("Error", f"El módulo '{new_name}' ya existe.")
                return
            modulos_list.append(new_name)
            settings["Modulos"] = modulos_list
            settings[f"Directorio_{new_name}"] = new_tracking_dir
            settings[f"RutaModulo_{new_name}"] = new_mod_path
            settings[f"{new_name}_enabled"] = "True"
        write_settings_in_process(cfg_file, settings)
        messagebox.showinfo("Información", "Módulos agregados automáticamente con valores por defecto.")
        top.destroy()

    def open_details_form():
        seleccionados = [mod for mod, var in vars_dict.items() if var.get()]
        if not seleccionados:
            messagebox.showinfo("Información", "No se seleccionó ningún módulo.")
            return
        details_win = tk.Toplevel(top)
        details_win.title("Detalles de Módulos a Agregar")
        form_entries = {}
        row_idx = 0
        for mod in seleccionados:
            ttk.Label(details_win, text=f"Detalles para el módulo '{mod}':", 
                      font=("Montserrat", 10, "bold")).grid(row=row_idx, column=0, columnspan=3, pady=(10,2), sticky="w")
            row_idx += 1
            ttk.Label(details_win, text="Nombre del Módulo:").grid(row=row_idx, column=0, padx=5, pady=2, sticky="e")
            mod_name_var = tk.StringVar(value=mod)
            entry_name = ttk.Entry(details_win, textvariable=mod_name_var, width=30)
            entry_name.grid(row=row_idx, column=1, padx=5, pady=2)
            row_idx += 1
            ttk.Label(details_win, text="Ruta del Módulo:").grid(row=row_idx, column=0, padx=5, pady=2, sticky="e")
            default_mod_path = os.path.join(project_dir, "Modulos", mod)
            mod_path_var = tk.StringVar(value=default_mod_path)
            entry_path = ttk.Entry(details_win, textvariable=mod_path_var, width=40)
            entry_path.grid(row=row_idx, column=1, padx=5, pady=2)
            def browse_mod_path(var=mod_path_var):
                chosen = filedialog.askdirectory(title="Seleccionar carpeta del módulo (debe contener Funciones.py)")
                if chosen:
                    var.set(chosen)
            ttk.Button(details_win, text="Examinar", command=browse_mod_path).grid(row=row_idx, column=2, padx=5, pady=2)
            row_idx += 1
            ttk.Label(details_win, text="Directorio de Seguimiento:").grid(row=row_idx, column=0, padx=5, pady=2, sticky="e")
            tracking_dir_var = tk.StringVar(value="")
            entry_tracking = ttk.Entry(details_win, textvariable=tracking_dir_var, width=40)
            entry_tracking.grid(row=row_idx, column=1, padx=5, pady=2)
            def browse_tracking_dir(var=tracking_dir_var):
                chosen = filedialog.askdirectory(title="Seleccionar directorio de seguimiento (CSV)")
                if chosen:
                    var.set(chosen)
            ttk.Button(details_win, text="Examinar", command=browse_tracking_dir).grid(row=row_idx, column=2, padx=5, pady=2)
            row_idx += 1
            form_entries[mod] = {
                "mod_name_var": mod_name_var,
                "mod_path_var": mod_path_var,
                "tracking_dir_var": tracking_dir_var
            }
        def guardar_detalles():
            settings = read_setting(cfg_file)
            mod_value = settings.get("Modulos", [])
            if isinstance(mod_value, str):
                modulos_list = [m.strip() for m in mod_value.split(",") if m.strip()]
            else:
                modulos_list = mod_value
            for mod, entries in form_entries.items():
                new_name = entries["mod_name_var"].get().strip()
                new_mod_path = entries["mod_path_var"].get().strip()
                new_tracking_dir = entries["tracking_dir_var"].get().strip()
                if not new_name or not new_mod_path:
                    messagebox.showwarning("Faltan datos", "Ingrese un nombre y la ruta del módulo válidos.")
                    return
                funciones_path = os.path.join(new_mod_path, "Funciones.py")
                if not os.path.exists(funciones_path):
                    messagebox.showerror("Error", f"No se encontró 'Funciones.py' en la ruta del módulo:\n{new_mod_path}")
                    return
                if os.path.basename(new_mod_path) != new_name:
                    messagebox.showwarning("Advertencia", "El nombre del módulo no coincide con el nombre de la carpeta seleccionada.")
                if new_name in modulos_list:
                    messagebox.showerror("Error", f"El módulo '{new_name}' ya existe.")
                    return
                modulos_list.append(new_name)
                settings["Modulos"] = modulos_list
                settings[f"Directorio_{new_name}"] = new_tracking_dir
                settings[f"RutaModulo_{new_name}"] = new_mod_path
                settings[f"{new_name}_enabled"] = "True"
            write_settings_in_process(cfg_file, settings)
            messagebox.showinfo("Información", "Módulos agregados correctamente con detalles.")
            details_win.destroy()
            top.destroy()
        ttk.Button(details_win, text="Confirmar", command=guardar_detalles).grid(row=row_idx, column=0, columnspan=3, pady=10)

    btn_agregar = ttk.Button(top, text="Agregar Seleccionados", command=agregar_automaticamente)
    btn_agregar.grid(row=len(modulos_nuevos) + 1, column=0, padx=5, pady=10, sticky="w")
    btn_avanzar = ttk.Button(top, text="Avanzar", command=open_details_form)
    btn_avanzar.grid(row=len(modulos_nuevos) + 1, column=1, padx=5, pady=10, sticky="w")

# -------------------------------
# FIN DEL MÓDULO Process.py
# -------------------------------