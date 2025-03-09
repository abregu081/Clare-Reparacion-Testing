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

        # Variable para activar/desactivar acumulación de fallas
        self.acumular_fallas = tk.BooleanVar(value=True)

        # Configuración de pesos en la ventana principal (una sola columna)
        self.columnconfigure(0, weight=1)
        # Usamos 6 filas:
        # 0: Superior (logos)
        # 1: Controles
        # 2: Path del módulo y Checkbutton de "Acumular Fallas"
        # 3: Historial (Treeview)
        # 4: Log
        # 5: (Opcional, para separación si se acumulan fallas)
        for r in range(6):
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

        logo_label_img = ttk.Label(button_frame, image=self.logo_mirgor)
        logo_label_img.grid(row=0, column=0, sticky="w", padx=10)
        xd_tracker_label = ttk.Label(button_frame, text="TESTING UNAE",
                                     font=("Montserrat", 32, "bold"), anchor="center")
        xd_tracker_label.grid(row=0, column=1, sticky="nsew", padx=10)
        fail_tracker_label = ttk.Label(button_frame, image=self.logo_clare, anchor="center")
        fail_tracker_label.grid(row=0, column=2, sticky="e", padx=10)

        # ----------------------------------------------------------------
        #   FRAME DE CONTROLES EN DOS MITADES
        # ----------------------------------------------------------------
        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        # MITAD IZQUIERDA
        left_frame = ttk.Frame(control_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_subframe = ttk.Frame(left_frame)
        left_subframe.pack(expand=True, anchor="center")

        sn_label = ttk.Label(left_subframe, text="Scan S/N", font=("Montserrat", 14, "bold"))
        sn_label.pack(side="left", padx=5, pady=5)
        self.sn_var = tk.StringVar()
        self.url_entry = ttk.Entry(left_subframe, width=25,textvariable=self.sn_var)
        self.url_entry.pack(side="left", padx=5, pady=5)

        # Control de la busqueda automatica con la pisotola de barras
        self.sn_var.trace_add("write", self.auto_submit_check)

        search_btn = ttk.Button(left_subframe, text="Buscar", command=self.on_submit)
        search_btn.pack(side="left", padx=5, pady=5)

        # MITAD DERECHA
        right_frame = ttk.Frame(control_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_subframe = ttk.Frame(right_frame)
        right_subframe.pack(expand=True, anchor="center")

        medio_label = ttk.Label(right_subframe, text="Medio:", font=("Montserrat", 14, "bold"))
        medio_label.pack(side="left", padx=5, pady=5)
        enabled_mods = [m for m, info in MODULES_INFO.items() if info.get("enabled", True)]
        self.combo_modulos = ttk.Combobox(right_subframe, values=enabled_mods, state="readonly", width=10)
        self.combo_modulos.pack(side="left", padx=5, pady=5)
        if enabled_mods:
            self.combo_modulos.current(0)
        self.combo_modulos.bind("<<ComboboxSelected>>", self.update_module_path)

        # Definimos un estilo "HiddenMenubutton" con letra y padding mínimos
        style.configure("HiddenMenubutton.TMenubutton",
                        font=("Montserrat", 1),
                        padding=0)

        # Creamos un Menubutton casi invisible: sin texto, width muy pequeño
        config_button = ttk.Menubutton(right_subframe, text="", width=1)
        config_button.configure(style="HiddenMenubutton.TMenubutton")

        # Ajustamos padding mínimo para que apenas se vea
        config_button.pack(side="left", padx=1, pady=1)

        # El menú sigue igual
        config_menu = tk.Menu(config_button, tearoff=False)
        config_menu.add_command(label="Eliminar Módulo", command=self.on_remove_module)
        config_menu.add_command(label="Agregar Módulo", command=self.on_add_module)
        config_button["menu"] = config_menu

        # ----------------------------------------------------------------
        #   NUEVA FILA: PATH DEL MÓDULO y opción de Acumular Fallas (centrado)
        # ----------------------------------------------------------------
        module_path_frame = ttk.Frame(self)
        module_path_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        module_path_frame.columnconfigure(0, weight=1)
        # Etiqueta del path
        self.module_path_var = tk.StringVar(value="Path: ")
        module_path_label = ttk.Label(module_path_frame,
                                      textvariable=self.module_path_var,
                                      font=("Montserrat", 12, "bold"),
                                      anchor="center")
        module_path_label.grid(row=0, column=0, sticky="ew")
        # Botón para explorar el path (llama a on_change_path)
        explorar_path = ttk.Button(module_path_frame, text="Explorar", command=self.on_change_path)
        explorar_path.grid(row=0, column=1, padx=5, pady=5)
        # Checkbutton para acumular fallas
        acumular_chk = ttk.Checkbutton(module_path_frame, text="Acumular Fallas",
                                        variable=self.acumular_fallas,
                                        command=self.update_layout)
        acumular_chk.grid(row=0, column=2, padx=5, pady=5)

        # ----------------------------------------------------------------
        #   FRAME DEL HISTORIAL: Cabecera + Treeview para mostrar registros
        # ----------------------------------------------------------------
        history_frame = ttk.Frame(self)
        history_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        # Configuramos dos filas: fila 0 para la cabecera y fila 1 para el Treeview
        history_frame.rowconfigure(1, weight=1)  # Le damos menos peso para achicarlo
        history_frame.columnconfigure(0, weight=1)

        header_frame = ttk.Frame(history_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        seguimiento_label = ttk.Label(header_frame, text="Seguimiento", font=("Montserrat", 14, "bold"))
        seguimiento_label.grid(row=0, column=0, sticky="w")
        clear_button = ttk.Button(header_frame, text="🗑️", style="SmallButton.TButton", command=self.clear_screen)
        clear_button.grid(row=0, column=2, padx=2, sticky="e")
        export_button = ttk.Button(header_frame, text="Exportar", style="SmallButton.TButton", command=self.download_csv)
        export_button.grid(row=0, column=3, padx=2, sticky="e")
        #order_button = ttk.Button(header_frame, text="↑", width=3, style="SmallButton.TButton", command=self.ordenar_por_fecha)
        #order_button.grid(row=0, column=3, padx=2, sticky="e")

        # --- Variables para ordenación de columnas ---
        self.column_indices = {"SN": 0, "Fecha_Hora": 1, "Medio": 2, "Status": 3, "Falla": 4, "Hostname": 5}
        self.sort_orders = {}  # Aquí se guarda el estado de orden (False: ascendente, True: descendente)

        # --- Agregamos el Treeview en un frame con scrollbar vertical ---
        tree_frame = ttk.Frame(history_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.history_tree = ttk.Treeview(
            tree_frame,
            columns=("SN", "Fecha_Hora", "Medio", "Status", "Falla", "Hostname"),
            show="headings",
            height=5  # Ajusta 'height' para achicar el cuadro
        )

        # Configuramos los encabezados con la función de ordenación:
        self.history_tree.heading("SN", text="SN", command=lambda col="SN": self.sort_by_column(col))
        self.history_tree.heading("Fecha_Hora", text="FECHA/HORA", command=lambda col="Fecha_Hora": self.sort_by_column(col))
        self.history_tree.heading("Medio", text="Medio", command=lambda col="Medio": self.sort_by_column(col))
        self.history_tree.heading("Status", text="Status", command=lambda col="Status": self.sort_by_column(col))
        self.history_tree.heading("Falla", text="Falla", command=lambda col="Falla": self.sort_by_column(col))
        self.history_tree.heading("Hostname", text="Hostname", command=lambda col="Hostname": self.sort_by_column(col))

        # Configuramos ancho y alineación de las columnas:
        self.history_tree.column("SN", width=100, anchor="center")
        self.history_tree.column("Fecha_Hora", width=150, anchor="center")
        self.history_tree.column("Medio", width=100, anchor="center")
        self.history_tree.column("Status", width=80, anchor="center")
        self.history_tree.column("Falla", width=200, anchor="w")
        self.history_tree.column("Hostname", width=100, anchor="center")

        self.history_tree.grid(row=0, column=0, sticky="nsew")
        self.history_tree.bind("<<TreeviewSelect>>", self.on_record_select)

        # Agregamos un scrollbar vertical:
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.history_tree.configure(yscrollcommand=tree_scroll.set)

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

        # Ajustamos los pesos de las filas de la ventana principal
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        # Si se acumulan fallas, dejamos el historial y el log con peso igual;
        # de lo contrario, expandimos el log
        if self.acumular_fallas.get():
            self.rowconfigure(3, weight=1)
            self.rowconfigure(4, weight=1)
        else:
            self.rowconfigure(3, weight=0)
            self.rowconfigure(4, weight=2)

    # ----------------------------------------------------------------
    #   MÉTODOS PRINCIPALES
    # ----------------------------------------------------------------
    def update_module_path(self, event=None):
        mod_name = self.combo_modulos.get().strip()
        if mod_name and mod_name in MODULES_INFO:
            self.module_path_var.set("Path: " + MODULES_INFO[mod_name]["path"])
        else:
            self.module_path_var.set("Path:")

    def update_layout(self):
        """Actualiza la distribución de filas según si se acumulan fallas o no."""
        if self.acumular_fallas.get():
            self.rowconfigure(3, weight=1)
            self.rowconfigure(4, weight=1)
        else:
            self.rowconfigure(3, weight=0)
            self.rowconfigure(4, weight=2)

    def on_submit(self):
        """
        1) Toma el módulo seleccionado y el SN ingresado.
        2) Busca y procesa el archivo CSV para el SN.
        3) Muestra y resalta el contenido en history_log.
        4) Finalmente, invoca a buscar_historial para insertar registros en la tabla.
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
        # Actualizamos el label del path (siempre visible)
        self.module_path_var.set(f"Path: {self.directorio}")

        sn_value = self.url_entry.get().strip()
        if not sn_value:
            print("[WARN] S/N está vacío, ingrese un valor.")
            return

        # Limpiamos el ScrolledText
        self.history_log.delete("1.0", "end")

        # Obtén las funciones buscar y procesar del módulo
        buscar_fn = info_modulo["buscar"]
        procesar_fn = info_modulo["procesar"]

        # 1) Buscar el CSV para el SN
        csv_path = buscar_fn(sn_value, self.directorio)
        if csv_path is None:
            msg = f"[INFO] No se encontró ningún archivo CSV para S/N '{sn_value}' en '{mod_name}'."
            print(msg)
            self.history_log.insert("end", msg + "\n")

            # Si no vamos a acumular fallas, limpiamos pantalla y tabla:
            if not self.acumular_fallas.get():
                self.clear_screen()  # Limpia el Treeview y el history_log
            return

        # 2) Procesar el archivo para obtener la falla
        fail_row = procesar_fn(csv_path)
        if csv_path and not fail_row:
            msg = f"[INFO] No se encontraron filas con FAIL/NG en '{csv_path}' (módulo: {mod_name})."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            #return

        # 3) Leer el contenido y resaltarlo en history_log
        file_content = []
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                file_content = f.readlines()
        except UnicodeDecodeError:
            with open(csv_path, "r", encoding="cp1252") as f:
                file_content = f.readlines()

        file_content_str = "".join(file_content)
        self.history_log.tag_configure("highlight", background="yellow")

        for i, line in enumerate(file_content):
            self.history_log.insert("end", line)
            if fail_row and ",".join(fail_row) in line:
                self.history_log.tag_add("highlight", f"{i + 1}.0", f"{i + 1}.end")

        # 4) Actualiza la tabla invocando a buscar_historial
        #    La responsabilidad de crear e insertar registros en self.table_records 
        #    recae completamente en buscar_historial. 
        #    _rebuild_table() se ejecuta internamente al final de buscar_historial 
        #    o cuando quieras refrescar la vista.

        # Si _rebuild_table() se llama dentro de buscar_historial, no necesitas llamarlo aquí.
        # Sin embargo, si te interesa refrescar algo antes, puedes llamarlo:
        # self._rebuild_table()

        # Llamamos a buscar_historial pasando accumulate para decidir si acumulamos registros
        self.buscar_historial(mod_name, accumulate=self.acumular_fallas.get())

    def _rebuild_table(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for index, row in enumerate(self.table_records):
            self.history_tree.insert("", "end", iid=index, values=row[:6])

    def on_record_select(self, event):
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

    def buscar_historial(self, mod_name, accumulate=False):
        """
        ÚNICA función que crea registros y los inserta en self.table_records y el Treeview.
        Si accumulate=False, se limpia la tabla previo a insertar los nuevos registros.
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

        # Limpia la tabla y la lista si no se acumula
        if not accumulate:
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            self.table_records.clear()

        # Construye e inserta registros en la tabla
        for reg in registros:
            # date_str + time_str
            fecha_hora = f"{reg['date_str']} {reg['time_str']}"
            fail_row = procesar_fn(reg["file_path"])
            # Ejemplo: si la primer posición de fail_row es el status, y el resto es la falla
            # Ajusta según tu realidad.
            # Aquí supongo que reg["status"] es el "Status" y fail_row[0] el "Falla",
            # o viceversa, dependiendo de tu caso real.
            # Te muestro un ejemplo donde se respeta: 
            #   col3 -> reg["status"]
            #   col4 -> fail_row[0]
            falla_value = fail_row[0] if fail_row else ""

            file_content_str = ""
            try:
                with open(reg["file_path"], "r", encoding="utf-8") as f:
                    file_content_str = f.read()
            except UnicodeDecodeError:
                with open(reg["file_path"], "r", encoding="cp1252") as f:
                    file_content_str = f.read()

            new_record = (
                codigo,             # SN        -> col0
                fecha_hora,         # FECHA/HORA-> col1
                mod_name,           # Medio     -> col2
                reg["status"],      # Status    -> col3
                falla_value,        # Falla     -> col4
                reg["hostname"],    # Hostname  -> col5
                reg["file_path"],   # Ruta
                file_content_str,   # Contenido
                fail_row            # Para resaltado
            )

            self.table_records.append(new_record)
            self.history_tree.insert("", "end", iid=len(self.table_records)-1, values=new_record[:6])

    def ordenar_por_fecha(self):
        self.sort_descending = not self.sort_descending
        current_mod = self.combo_modulos.get()
        if current_mod:
            self.buscar_historial(current_mod)
    
    def sort_by_column(self, col):
        col_index = self.column_indices.get(col)
        if col_index is None:
            return

        # Alterna el orden: por defecto, si no existe, se asume ascendente (False)
        current_order = self.sort_orders.get(col, False)
        new_order = not current_order
        self.sort_orders[col] = new_order

        # Si la columna es "Fecha_Hora", intentamos convertirla a datetime para un orden correcto
        if col == "Fecha_Hora":
            try:
                self.table_records.sort(
                    key=lambda record: datetime.strptime(record[col_index], "%Y-%m-%d %H:%M:%S"),
                    reverse=new_order
                )
            except Exception:
                # En caso de error (por ejemplo, formato distinto), ordenamos como string
                self.table_records.sort(key=lambda record: record[col_index], reverse=new_order)
        else:
            self.table_records.sort(key=lambda record: record[col_index], reverse=new_order)

        # Reconstruye la tabla para reflejar el nuevo orden
        self._rebuild_table()


    #Funcion de buscado automatico para la pisotola lectora de barras

    def auto_submit_check(self, *args):
        current_sn = self.sn_var.get().strip()
        if len(current_sn) == 26:
            self.on_submit()

    def clear_screen(self):
            self.history_log.delete("1.0", tk.END)
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            self.table_records.clear()

    def download_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Data_Puesto"
        )
        if not filename:
            msg = "Exportación cancelada por el usuario."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Si deseas solo las 6 columnas que se ven:
                writer.writerow(["SN", "Fecha/Hora", "Medio", "Status", "Falla", "Hostname"])
                
                # Obtenemos los IDs de todos los hijos actuales del Treeview
                for child_id in self.history_tree.get_children():
                    # 'values' traerá la tupla con las 6 columnas
                    row_values = self.history_tree.item(child_id, "values")
                    writer.writerow(row_values)

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
                    if not mod_path:
                        print(f"[INFO] Se usó la ruta por defecto para el módulo '{mod_name}': {mod_path}")
                        continue
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
    root.title("Clare by Mirgor-UNAE (Versión 1.0)") 
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
