import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import csv
import os
import sys
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import importlib
from Process import read_setting, cfg_file, write_settings_in_process, normalize_drive_letter
import importlib
from Process import MODULES_INFO, cfg_file, read_setting, write_settings_in_process, agregar_modulos_gui

class UptimeBot(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("SmallButton.TButton", font=("Montserrat", 10), padding=2)

        self.directorio = None
        # Lista donde almacenamos todos los registros (cada uno con 9 elementos)
        self.table_records = []
        self.sort_descending = False  # Para alternar el orden de clasificación en el historial

        # Configuración de pesos en la ventana principal (una sola columna)
        self.columnconfigure(0, weight=1)
        for r in range(5):  # Ahora usamos 5 filas (agregamos una nueva para el path)
            self.rowconfigure(r, weight=1)

        # ----------------------------------------------------------------
        #   FRAME SUPERIOR (Logo, etc.)
        # ----------------------------------------------------------------
        button_frame = ttk.Frame(self)
        button_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        original_image = Image.open("assets/Logo_Mirgor.png")
        resized_image = original_image.resize((300, 100), Image.LANCZOS)
        self.logo_mirgor = ImageTk.PhotoImage(resized_image)

        clare_logo = Image.open("assets/Logo Clare.png")
        resized_clare = clare_logo.resize((200, 150), Image.LANCZOS)
        self.logo_clare = ImageTk.PhotoImage(resized_clare)

        # Logo a la izquierda
        logo_label_img = ttk.Label(button_frame, image=self.logo_mirgor)
        logo_label_img.grid(row=0, column=0, sticky="w", padx=10)
        # Texto en el centro
        xd_tracker_label = ttk.Label(
            button_frame,
            text="[UN-TRACKER]",
            font=("Chakra Petch", 32, "bold"),
            anchor="center"
        )
        xd_tracker_label.grid(row=0, column=1, sticky="nsew", padx=10)
        # Logo a la derecha
        fail_tracker_label = ttk.Label(button_frame, image=self.logo_clare, anchor="center")
        fail_tracker_label.grid(row=0, column=2, sticky="e", padx=10)

        # ----------------------------------------------------------------
        #   FRAME DE CONTROLES EN DOS MITADES
        # ----------------------------------------------------------------
        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        # Configuramos dos columnas para dividir la fila en dos mitades
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        #
        # MITAD IZQUIERDA
        #
        left_frame = ttk.Frame(control_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")

        # Usamos un subframe con pack para centrar los widgets en horizontal
        left_subframe = ttk.Frame(left_frame)
        left_subframe.pack(expand=True, anchor="center")

        sn_label = ttk.Label(left_subframe, text="Scan S/N", font=("Montserrat", 14, "bold"))
        sn_label.pack(side="left", padx=5, pady=5)

        # Entry para el S/N
        self.url_entry = ttk.Entry(left_subframe, width=25)
        self.url_entry.pack(side="left", padx=5, pady=5)

        search_btn = ttk.Button(left_subframe, text="Buscar", command=self.on_submit)
        search_btn.pack(side="left", padx=5, pady=5)

        #
        # MITAD DERECHA
        #
        right_frame = ttk.Frame(control_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")

        # Usamos otro subframe con pack para centrar los widgets en horizontal
        right_subframe = ttk.Frame(right_frame)
        right_subframe.pack(expand=True, anchor="center")

        medio_label = ttk.Label(right_subframe, text="Medio:", font=("Montserrat", 14, "bold"))
        medio_label.pack(side="left", padx=5, pady=5)

        enabled_mods = [m for m, info in MODULES_INFO.items() if info.get("enabled", True)]
        self.combo_modulos = ttk.Combobox(right_subframe, values=enabled_mods, state="readonly", width=10)
        self.combo_modulos.pack(side="left", padx=5, pady=5)
        if enabled_mods:
            self.combo_modulos.current(0)

        config_button = ttk.Menubutton(right_subframe, text="Configuraciones")
        config_button.pack(side="left", padx=5, pady=5)
        config_menu = tk.Menu(config_button, tearoff=False)
        config_menu.add_command(label="Cambiar Ruta", command=self.on_change_path)
        config_menu.add_command(label="Eliminar Módulo", command=self.on_remove_module)
        config_menu.add_command(label="Agregar Módulo", command=self.on_add_module)
        config_button["menu"] = config_menu

        # ----------------------------------------------------------------
        #   NUEVA FILA: PATH DEL MÓDULO
        # ----------------------------------------------------------------
        # Aseguramos que la columna 0 del contenedor (en este caso self) se expanda
        self.columnconfigure(0, weight=1)

        # Creamos la etiqueta con anchor "center"
        self.module_path_var = tk.StringVar(value="Path: ")
        module_path_label = ttk.Label(self, textvariable=self.module_path_var, font=("Montserrat", 12, "bold"), anchor="center")

        # Colocamos la etiqueta de forma que se expanda horizontalmente
        module_path_label.grid(row=2, column=0, sticky="ew", padx=20, pady=5)

        # ----------------------------------------------------------------
        #   FRAME DEL HISTORIAL: Cabecera + Treeview para mostrar registros
        # ----------------------------------------------------------------
        history_frame = ttk.Frame(self)
        history_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        # Configuramos dos filas: la fila 0 para la cabecera y la fila 1 para el Treeview
        history_frame.rowconfigure(1, weight=3)
        history_frame.columnconfigure(0, weight=1)

        # --- Cabecera del Historial ---
        header_frame = ttk.Frame(history_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        seguimiento_label = ttk.Label(header_frame, text="Seguimiento", font=("Montserrat", 14, "bold"))
        seguimiento_label.grid(row=0, column=0, sticky="w")

        clear_button = ttk.Button(header_frame, text="🗑️", style="SmallButton.TButton", command=self.clear_screen)
        clear_button.grid(row=0, column=1, padx=2, sticky="e")

        export_button = ttk.Button(header_frame, text="Exportar", style="SmallButton.TButton", command=self.download_csv)
        export_button.grid(row=0, column=2, padx=2, sticky="e")

        order_button = ttk.Button(header_frame, text="↑", width=3, style="SmallButton.TButton", command=self.ordenar_por_fecha)
        order_button.grid(row=0, column=3, padx=2, sticky="e")

        # --- Treeview del Historial ---
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("SN", "Fecha_Hora", "Medio", "Status", "Falla", "Hostname"),
            show="headings"
        )
        self.history_tree.heading("SN", text="SN")
        self.history_tree.heading("Fecha_Hora", text="FECHA/HORA")
        self.history_tree.heading("Medio", text="Medio")
        self.history_tree.heading("Status", text="Status")
        self.history_tree.heading("Falla", text="Falla")
        self.history_tree.heading("Hostname", text="Hostname")

        self.history_tree.column("SN", width=100, anchor="center")
        self.history_tree.column("Fecha_Hora", width=150, anchor="center")
        self.history_tree.column("Medio", width=100, anchor="center")
        self.history_tree.column("Status", width=80, anchor="center")
        self.history_tree.column("Falla", width=200, anchor="w")
        self.history_tree.column("Hostname", width=100, anchor="center")

        self.history_tree.grid(row=1, column=0, sticky="nsew")
        self.history_tree.bind("<<TreeviewSelect>>", self.on_record_select)

        # ----------------------------------------------------------------
        #   FRAME DEL LOG: Área de log debajo del historial
        # ----------------------------------------------------------------
        log_frame = ttk.Frame(self)
        log_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=10)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_label_var = tk.StringVar(value="Log:")
        history_log_label = ttk.Label(log_frame, textvariable=self.log_label_var, font=("Montserrat", 14, "bold"))
        history_log_label.pack(pady=(0, 10))

        self.history_log = ScrolledText(log_frame, height=10)
        self.history_log.pack(fill="both", expand=True)

        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)

    # ----------------------------------------------------------------
    #   MÉTODOS PRINCIPALES
    # ----------------------------------------------------------------
    def on_submit(self):
        """
        - Lee qué módulo está seleccionado en el Combobox.
        - Busca la ruta en MODULES_INFO.
        - Busca y procesa el CSV para el S/N ingresado.
        - Almacena el registro en self.table_records y reconstruye la tabla.
        """
        mod_name = self.combo_modulos.get().strip()
        if not mod_name:
            messagebox.showwarning("Módulo no seleccionado", "Por favor seleccione un módulo en el menú desplegable.")
            return

        info_modulo = MODULES_INFO.get(mod_name)
        if not info_modulo:
            messagebox.showerror("Error", f"No se encontró información para el módulo '{mod_name}'")
            return

        self.directorio = info_modulo["path"]
        # Actualizamos el path del módulo en la etiqueta
        self.module_path_var.set(f"Path: {self.directorio}")

        sn_value = self.url_entry.get().strip()
        if not sn_value:
            print("[WARN] S/N está vacío, ingrese un valor.")
            return

        self.history_log.delete("1.0", "end")
        file_content = []
        csv_path = None
        fail_row = None

        buscar_fn = info_modulo["buscar"]
        procesar_fn = info_modulo["procesar"]

        # 1) Buscar
        csv_path = buscar_fn(sn_value, self.directorio)
        if csv_path is None:
            msg = f"[INFO] No se encontró ningún archivo CSV para S/N '{sn_value}' en '{mod_name}'."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        # 2) Procesar
        fail_row = procesar_fn(csv_path)

        if csv_path and not fail_row:
            msg = f"[INFO] No se encontraron filas con FAIL/NG en '{csv_path}' (módulo: {mod_name})."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        # Leer archivo para mostrar su contenido
        file_content_str = ""
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                file_content = f.readlines()
        except UnicodeDecodeError:
            with open(csv_path, "r", encoding="cp1252") as f:
                file_content = f.readlines()
        file_content_str = "".join(file_content)

        # Resaltar la fila con FAIL/NG en history_log
        self.history_log.tag_configure("highlight", background="yellow")
        for i, line in enumerate(file_content):
            self.history_log.insert("end", line)
            if fail_row and ",".join(fail_row) in line:
                self.history_log.tag_add("highlight", f"{i + 1}.0", f"{i + 1}.end")

        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tipo_value = fail_row[0] if fail_row else ""
        falla_value = " | ".join(fail_row[1:]) if fail_row and len(fail_row) > 1 else ""
        new_record = (
            sn_value,            # SN
            hora_actual,         # Fecha/Hora
            mod_name,            # Medio
            tipo_value,          # Status
            falla_value,         # Falla
            "",                  # Hostname (vacío en este ejemplo)
            csv_path,            # Ruta del archivo
            file_content_str,    # Contenido del archivo
            fail_row             # Guardamos fail_row para resaltado
        )
        self.table_records.insert(0, new_record)
        self._rebuild_table()
        self.buscar_historial(mod_name)

    def _rebuild_table(self):
        """
        Recrea la tabla de seguimientos (history_tree) con self.table_records.
        Solo se muestran las primeras 6 columnas.
        """
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for index, row in enumerate(self.table_records):
            self.history_tree.insert("", "end", iid=index, values=row[:6])

    def on_record_select(self, event):
        """
        Al seleccionar un registro, se actualiza la etiqueta del Log con la ruta
        y se muestra el contenido resaltando la falla.
        """
        selected = self.history_tree.focus()
        if selected:
            try:
                index = int(selected)
                record = self.table_records[index]
                file_path = record[6]
                file_content = record[7]
                fail_row = record[8]
                self.log_label_var.set(f"Log: {file_path}")
                self._highlight_fail(self.history_log, file_content, fail_row)
            except (ValueError, IndexError) as e:
                print(f"[ERROR] Al recuperar el log del registro: {e}")

    def _highlight_fail(self, text_widget, file_content_str, fail_row):
        """
        Inserta file_content_str en text_widget y resalta la falla usando fail_row.
        """
        text_widget.delete("1.0", "end")
        text_widget.insert("end", file_content_str)
        text_widget.tag_configure("highlight", background="yellow")
        if not fail_row:
            return
        fail_str = ",".join(fail_row)
        lines = file_content_str.split("\n")
        for i, line in enumerate(lines):
            if fail_str in line:
                start_index = f"{i+1}.0"
                end_index = f"{i+1}.end"
                text_widget.tag_add("highlight", start_index, end_index)

    def buscar_historial(self, mod_name):
        """
        Busca en el historial usando la función del módulo seleccionado.
        Se agregan los registros a self.table_records y se muestran en el Treeview.
        """
        if not self.directorio:
            print("[ERROR] No se ha seleccionado un directorio para historial.")
            return
        codigo = self.url_entry.get().strip()
        if not codigo:
            print("[WARN] Ingrese un código para buscar en el historial.")
            return
        info_modulo = MODULES_INFO.get(mod_name)
        if not info_modulo:
            print(f"[ERROR] No hay información de módulo para {mod_name}")
            return
        historial_fn = info_modulo["historial"]
        procesar_fn = info_modulo["procesar"]
        registros = historial_fn(codigo, self.directorio)
        if self.sort_descending:
            registros = list(reversed(registros))
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.table_records.clear()
        for reg in registros:
            fecha_hora = f"{reg['date_str']} {reg['time_str']}"
            fail_row = procesar_fn(reg["file_path"])
            tipo_value = fail_row[0] if fail_row else ""
            file_content_str = ""
            try:
                with open(reg["file_path"], "r", encoding="utf-8") as f:
                    file_content_str = f.read()
            except UnicodeDecodeError:
                with open(reg["file_path"], "r", encoding="cp1252") as f:
                    file_content_str = f.read()
            new_record = (
                codigo,            # SN
                fecha_hora,        # Fecha/Hora
                mod_name,          # Medio
                reg["status"],     # Status
                tipo_value,        # Falla
                reg["hostname"],   # Hostname
                reg["file_path"],  # Ruta del archivo
                file_content_str,  # Contenido del archivo
                fail_row           # fail_row para resaltado
            )
            self.table_records.append(new_record)
            self.history_tree.insert("", "end", iid=len(self.table_records)-1, values=new_record[:6])

    def ordenar_por_fecha(self):
        """Alterna el orden de clasificación y vuelve a cargar el historial."""
        self.sort_descending = not self.sort_descending
        current_mod = self.combo_modulos.get()
        if current_mod:
            self.buscar_historial(current_mod)

    def clear_screen(self):
        """Limpia el log, el Treeview y la lista de registros."""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar la pantalla?"):
            self.history_log.delete("1.0", tk.END)
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            self.table_records.clear()

    def download_csv(self):
        """Exporta los registros actuales a un archivo CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Datos Puesto de Reparacion"
        )
        if not filename:
            msg = "Exportación cancelada por el usuario."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return
        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["SN", "Fecha/Hora", "Medio", "Status", "Falla", "Hostname", "Ruta", "Contenido"])
                for row in self.table_records:
                    writer.writerow(row)
            msg = f"Registros exportados a '{filename}' con éxito."
            print(msg)
            self.history_log.insert("end", msg + "\n")
        except Exception as e:
            err_msg = f"Error al exportar CSV: {e}"
            print(err_msg)
            self.history_log.insert("end", err_msg + "\n")

    # ---------------------------------------
    #   MÉTODOS DE LECTURA/ESCRITURA DE CFG
    # ---------------------------------------
    def write_settings(self, file_path, settings_dict):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in settings_dict.items():
                    if isinstance(value, list):
                        value = ", ".join(value)
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"[ERROR] Al escribir configuración: {e}")

    def reload_modules_info(self):
        new_settings = read_setting(cfg_file)
        if isinstance(new_settings.get("Modulos", []), str):
            new_module_list = [m.strip() for m in new_settings["Modulos"].split(",") if m.strip()]
        else:
            new_module_list = new_settings.get("Modulos", [])
        new_modules_info = {}
        project_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        for mod_name in new_module_list:
            cfg_key = f"Directorio_{mod_name}"
            mod_path = str(new_settings.get(cfg_key, "")).strip()
            mod_path = normalize_drive_letter(mod_path)
            if not mod_path:
                ruta_key = f"RutaModulo_{mod_name}"
                mod_path = str(new_settings.get(ruta_key, "")).strip()
                mod_path = normalize_drive_letter(mod_path)
                if not mod_path:
                    default_path = os.path.join(project_dir, "Modulos", mod_name)
                    mod_path = default_path
                    if os.path.exists(default_path):
                        print(f"[INFO] Se usó la ruta por defecto para el módulo '{mod_name}': {mod_path}")
                    else:
                        print(f"[WARN] No se encontró la ruta para '{mod_name}', se asignará ruta por defecto: {mod_path}")
            enabled_value = new_settings.get(f"{mod_name}_enabled", "True").strip().lower()
            enabled_bool = False if enabled_value in ("false", "0", "no") else True
            try:
                module_ref = importlib.import_module(f"Modulos.{mod_name}.Funciones")
                buscar_fn = getattr(module_ref, f"buscar_archivo_{mod_name.lower()}")
                procesar_fn = getattr(module_ref, f"procesar_archivo_{mod_name.lower()}")
                historial_fn = getattr(module_ref, f"rutaHistorial_archivo_{mod_name.lower()}")
                new_modules_info[mod_name] = {
                    "path": mod_path,
                    "buscar": buscar_fn,
                    "procesar": procesar_fn,
                    "historial": historial_fn,
                    "enabled": enabled_bool
                }
            except Exception as e:
                print(f"[ERROR] Error al cargar el módulo {mod_name}: {e}")
                new_modules_info[mod_name] = {
                    "path": mod_path,
                    "buscar": None,
                    "procesar": None,
                    "historial": None,
                    "enabled": enabled_bool
                }
        MODULES_INFO.clear()
        MODULES_INFO.update(new_modules_info)
        self.combo_modulos["values"] = [m for m, info in MODULES_INFO.items() if info.get("enabled", True)]
        if self.combo_modulos.get() not in MODULES_INFO:
            self.combo_modulos.set("")

    # ----------------------------------------------------------------
    #   MÉTODOS DE ADMINISTRACIÓN DE MÓDULOS
    # ----------------------------------------------------------------
    def on_change_path(self):
        mod_name = self.combo_modulos.get().strip()
        if not mod_name:
            messagebox.showwarning("Módulo no seleccionado", "Seleccione un módulo para cambiar su ruta.")
            return
        new_path = filedialog.askdirectory(title=f"Seleccionar nueva ruta para {mod_name}")
        if not new_path:
            return
        settings = read_setting(cfg_file)
        settings[f"Directorio_{mod_name}"] = new_path
        self.write_settings(cfg_file, settings)
        if messagebox.askyesno("Ruta actualizada", f"Se actualizó la ruta de {mod_name} a:\n{new_path}\n\n¿Desea recargar la configuración actual?"):
            self.reload_modules_info()

    def on_remove_module(self):
        top = tk.Toplevel(self)
        top.title("Gestionar Módulos")
        top.geometry("500x300")
        config = read_setting(cfg_file)
        mod_value = config.get("Modulos", [])
        if isinstance(mod_value, str):
            modulos_config = [m.strip() for m in mod_value.split(",") if m.strip()]
        else:
            modulos_config = mod_value
        if not modulos_config:
            messagebox.showinfo("Información", "No hay módulos configurados.")
            top.destroy()
            return
        ttk.Label(top, text="Módulo", font=("Montserrat", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(top, text="Habilitado", font=("Montserrat", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(top, text="Eliminar", font=("Montserrat", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(top, text="Estado Actual", font=("Montserrat", 10, "bold")).grid(row=0, column=3, padx=5, pady=5)
        enable_vars = {}
        remove_vars = {}
        for idx, mod in enumerate(modulos_config, start=1):
            ttk.Label(top, text=mod).grid(row=idx, column=0, padx=5, pady=2, sticky="w")
            current_enabled = config.get(f"{mod}_enabled", "True")
            default_val = True
            if current_enabled.strip().lower() in ("false", "0", "no"):
                default_val = False
            enable_var = tk.BooleanVar(value=default_val)
            enable_chk = tk.Checkbutton(top, text="", variable=enable_var)
            enable_chk.grid(row=idx, column=1, padx=5, pady=2)
            enable_vars[mod] = enable_var
            remove_var = tk.BooleanVar()
            remove_chk = tk.Checkbutton(top, text="", variable=remove_var)
            remove_chk.grid(row=idx, column=2, padx=5, pady=2)
            remove_vars[mod] = remove_var
            ttk.Label(top, text=current_enabled).grid(row=idx, column=3, padx=5, pady=2, sticky="w")
        def confirmar():
            for mod in modulos_config[:]:
                if remove_vars[mod].get():
                    modulos_config.remove(mod)
                    directorio_key = f"Directorio_{mod}"
                    if directorio_key in config:
                        del config[directorio_key]
                    enabled_key = f"{mod}_enabled"
                    if enabled_key in config:
                        del config[enabled_key]
                else:
                    config[f"{mod}_enabled"] = "True" if enable_vars[mod].get() else "False"
            config["Modulos"] = modulos_config
            write_settings_in_process(cfg_file, config)
            messagebox.showinfo("Información", "La configuración se actualizó correctamente.")
            top.destroy()
            self.reload_modules_info()
        ttk.Button(top, text="Aplicar cambios", command=confirmar).grid(row=len(modulos_config)+1, column=0, columnspan=4, pady=10)

    def on_add_module(self):
        agregar_modulos_gui(self, cfg_file)
        self.reload_modules_info()


def main():
    root = tk.Tk()
    root.title("CLARE by [Testing UNAE]")
    root.geometry("1280x720")
    root.configure(bg="#FFFFFF")
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#FFFFFF")
    style.configure("TLabel", background="#FFFFFF", foreground="#000000", font=("Chakra Petch", 12))
    style.configure("TButton", font=("Montserrat", 12, "bold"), background="#141736", foreground="#FFFFFF")
    style.map("TButton", background=[("active", "#0040FF")], foreground=[("active", "#DEDCD3")])
    app = UptimeBot(master=root)
    app.mainloop()


if __name__ == "__main__":
    main()
