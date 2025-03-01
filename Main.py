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

from Process import MODULES_INFO, cfg_file, read_setting

class UptimeBot(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        self.directorio = None
        self.table_records = []
        self.sort_descending = False  # Para alternar el orden de clasificación en el historial

        # ----------------------------------------------------------------
        #   CONFIGURACIÓN DE ESTILOS
        # ----------------------------------------------------------------
        self.style = ttk.Style()
        self.style.configure("Montserrat.TButton", font=("Montserrat", 12, "bold"))
        self.style.map(
            "Montserrat.TButton",
            background=[("active", "#0052cc")],
            foreground=[("active", "white")]
        )
        self.style.configure(
            "Selected.TButton",
            font=("Montserrat", 12, "bold"),
            background="#0052cc",
            foreground="white"
        )
        
        # ----------------------------------------------------------------
        #   FRAME SUPERIOR (Logo, etc.)
        # ----------------------------------------------------------------
        button_frame = ttk.Frame(self)
        button_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=30, pady=10)
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

        # Logo a la derecha
        fail_tracker_label = ttk.Label(button_frame, image=self.logo_clare, anchor="center")
        fail_tracker_label.grid(row=0, column=2, sticky="e", padx=10)

        # Texto en el centro
        xd_tracker_label = ttk.Label(
            button_frame,
            text="[UN-TRACKER]",
            font=("Chakra Petch", 32, "bold"),
            anchor="center"
        )
        xd_tracker_label.grid(row=0, column=1, sticky="nsew", padx=10)

        # ----------------------------------------------------------------
        #   FRAME IZQUIERDO: S/N + Submit + Historial
        # ----------------------------------------------------------------
        url_frame = ttk.Frame(self)
        url_frame.grid(row=1, column=0, sticky="n", padx=20)
        url_frame.columnconfigure(0, weight=1)
        url_frame.rowconfigure(0, weight=0)
        url_frame.rowconfigure(1, weight=1)

        # Parte superior: Label + Entry
        top_frame = ttk.Frame(url_frame)
        top_frame.grid(row=0, column=0, sticky="n")

        url_label = ttk.Label(top_frame, text="Scan S/N", font=("Montserrat", 14, "bold"))
        url_label.pack(anchor="center", pady=5)

        self.url_entry = ttk.Entry(top_frame, width=25)
        self.url_entry.pack(anchor="center", pady=5)

        # Frame para Combobox + Botones de administración
        combo_admin_frame = ttk.Frame(url_frame)
        combo_admin_frame.grid(row=3, column=0, sticky="n", pady=5)

        # Menú desplegable (Combobox) para elegir el módulo
        enabled_mods = [m for m, info in MODULES_INFO.items() if info.get("enabled", True)]
        self.combo_modulos = ttk.Combobox(combo_admin_frame, values=enabled_mods, state="readonly")
        self.combo_modulos.grid(row=0, column=0, padx=5)

        if enabled_mods:
            self.combo_modulos.current(0)

        # Botón "Configuraciones"
        config_button = ttk.Menubutton(
            combo_admin_frame,
            text="Configuraciones"
        )
        config_button.grid(row=0, column=1, padx=5)

        # Creamos el menú desplegable asociado a config_button
        config_menu = tk.Menu(config_button, tearoff=False)
        config_menu.add_command(label="Cambiar Ruta", command=self.on_change_path)
        config_menu.add_command(label="Eliminar Módulo", command=self.on_remove_module)
        config_menu.add_command(label="Agregar Módulo", command=self.on_add_module)

        # Asignamos el menú al Menubutton
        config_button["menu"] = config_menu

        # Botón "Buscar"
        search_btn = ttk.Button(top_frame, text="Buscar", command=self.on_submit)
        search_btn.pack(anchor="center", pady=5)

        # ----------------------------------------------------------------
        #   FRAME para el historial (Treeview)
        # ----------------------------------------------------------------
        help_frame = ttk.Frame(url_frame)
        help_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        help_frame.rowconfigure(0, weight=1)

        self.history_tree = ttk.Treeview(
            help_frame,
            columns=("Hostname", "Status", "Fecha", "Hora", "Archivo"),
            show="headings"
        )
        self.history_tree.heading("Hostname", text="Hostname")
        self.history_tree.heading("Status", text="Status")
        self.history_tree.heading("Fecha", text="Fecha")
        self.history_tree.heading("Hora", text="Hora")
        self.history_tree.heading("Archivo", text="Archivo")

        self.history_tree.column("Hostname", width=100, anchor="center")
        self.history_tree.column("Status", width=70, anchor="center")
        self.history_tree.column("Fecha", width=80, anchor="center")
        self.history_tree.column("Hora", width=80, anchor="center")
        self.history_tree.column("Archivo", width=100, anchor="w")

        style_small = ttk.Style()
        style_small.configure(
            "SmallButton.TButton",
            font=("Montserrat", 10),
            padding=(5,2)
        )

        self.history_tree.grid(row=0, column=0, sticky="nsew")

        # Botón para ordenar por fecha (columna 1)
        order_button = ttk.Button(
            help_frame,
            text="↑",
            width=3,
            style="SmallButton.TButton",
            command=self.ordenar_por_fecha
        )
        order_button.grid(row=0, column=1, sticky="n")

        # ----------------------------------------------------------------
        #   FRAME DERECHO: Tabla + Log
        # ----------------------------------------------------------------
        history_frame = ttk.Frame(self)
        history_frame.grid(row=1, column=1, rowspan=2, sticky="nsew")

        history_info = ttk.Frame(history_frame)
        history_info.pack(fill="x", expand=False, side="top")

        history_label = ttk.Label(history_info, text="Seguimiento", font=("Montserrat", 14, "bold"))
        history_label.pack(side="left")

        # Botón "Exportar"
        history_download = ttk.Button(history_info, text="Exportar", command=self.download_csv)
        history_download.pack(side="right", padx=5)

        # Botón "Limpiar Pantalla"
        clear_button = ttk.Button(history_info, text="Limpiar Pantalla", command=self.clear_screen)
        clear_button.pack(side="right", padx=5)

        columns = ("Hora", "S/N", "TIPO", "FALLA")
        self.history_table = ttk.Treeview(history_frame, columns=columns, show="headings")
        self.history_table.pack(fill="both", expand=True, side="top")

        self.history_table.heading("Hora", text="Hora")
        self.history_table.heading("S/N", text="S/N")
        self.history_table.heading("TIPO", text="TIPO")
        self.history_table.heading("FALLA", text="FALLA")

        self.history_table.column("Hora", width=150, anchor="center")
        self.history_table.column("S/N", width=100, anchor="center")
        self.history_table.column("TIPO", width=100, anchor="center")
        self.history_table.column("FALLA", width=300, anchor="w")

        history_log_label = ttk.Label(history_frame, text="Log", font=("Montserrat", 14, "bold"))
        history_log_label.pack(fill="both", expand=False)

        self.history_log = ScrolledText(history_frame, height=10)
        self.history_log.pack(fill="both", expand=True)

        # Evento para mostrar log al seleccionar un registro
        self.history_table.bind("<<TreeviewSelect>>", self.on_record_select)

        # Ajustes de pesos en la ventana principal
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=7)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=4)
        self.rowconfigure(2, weight=4)
        self.rowconfigure(3, weight=1)

    # ----------------------------------------------------------------
    #   MÉTODOS PRINCIPALES
    # ----------------------------------------------------------------
    def on_submit(self):
        """
        - Lee qué módulo está seleccionado en el Combobox.
        - Busca la ruta en MODULES_INFO.
        - Busca y procesa el CSV para el S/N ingresado.
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

        sn_value = self.url_entry.get().strip()
        if not sn_value:
            print("[WARN] S/N está vacío, ingrese un valor.")
            return

        self.history_log.delete("1.0", "end")
        file_content = ""
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
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                file_content = f.readlines()
        except UnicodeDecodeError:
            with open(csv_path, "r", encoding="cp1252") as f:
                file_content = f.readlines()

        # Resaltar la fila con FAIL/NG en history_log
        self.history_log.tag_configure("highlight", background="yellow")

        for i, line in enumerate(file_content):
            self.history_log.insert("end", line)
            if fail_row and ",".join(fail_row) in line:
                self.history_log.tag_add("highlight", f"{i + 1}.0", f"{i + 1}.end")

        # Insertamos registro en la tabla de seguimientos
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tipo_value = fail_row[0] if fail_row else ""
        falla_value = " | ".join(fail_row[1:]) if fail_row and len(fail_row) > 1 else ""
        new_record = (hora_actual, sn_value, tipo_value, falla_value, "".join(file_content))

        self.table_records.insert(0, new_record)
        self._rebuild_table()
        self.buscar_historial(mod_name)

    def _rebuild_table(self):
        """Recrea la tabla de seguimientos (history_table) con self.table_records."""
        for item in self.history_table.get_children():
            self.history_table.delete(item)
        for index, row in enumerate(self.table_records):
            self.history_table.insert("", "end", iid=index, values=row[:4])

    def on_record_select(self, event):
        selected = self.history_table.focus()
        if selected:
            try:
                index = int(selected)
                record = self.table_records[index]
                log_content = record[4]
                self.history_log.delete("1.0", "end")
                self.history_log.insert("end", log_content)
            except (ValueError, IndexError) as e:
                print(f"[ERROR] Al recuperar el log del registro: {e}")

    def buscar_historial(self, mod_name):
        """Busca en el historial usando la función del módulo seleccionado."""
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
        registros = historial_fn(codigo, self.directorio)

        if self.sort_descending:
            registros = list(reversed(registros))

        # Limpia el Treeview actual
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Inserta cada registro en el Treeview
        for reg in registros:
            self.history_tree.insert(
                "",
                "end",
                values=(
                    reg["hostname"],
                    reg["status"],
                    reg["date_str"],
                    reg["time_str"],
                    reg["file_path"]
                )
            )

    def ordenar_por_fecha(self):
        """Alterna el orden de clasificación (asc/desc) y vuelve a cargar el historial."""
        self.sort_descending = not self.sort_descending
        current_mod = self.combo_modulos.get()
        if current_mod:
            self.buscar_historial(current_mod)

    def clear_screen(self):
        """Limpia el log, el Treeview del historial y la tabla de seguimientos."""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar la pantalla?"):
            self.history_log.delete("1.0", tk.END)
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            for item in self.history_table.get_children():
                self.history_table.delete(item)
            self.table_records.clear()

    def download_csv(self):
        """Exporta los registros actuales (table_records) a un archivo CSV."""
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
                writer.writerow(["Hora", "S/N", "TIPO", "FALLA"])
                for row in self.table_records:
                    writer.writerow(row[:4])
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
        """
        Escribe el diccionario `settings_dict` en el archivo `file_path`
        usando un formato compatible con read_setting().
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in settings_dict.items():
                    # Si el valor es lista, re-convertimos a "elem1, elem2, elem3"
                    if isinstance(value, list):
                        value = ", ".join(value)
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"[ERROR] Al escribir configuración: {e}")

    def reload_modules_info(self):
        """
        Relee el archivo Parametros.cfg, reconstruye el diccionario MODULES_INFO
        y actualiza el combobox de módulos para reflejar los cambios sin reiniciar la app.
        """
        new_settings = read_setting(cfg_file)

        # Si "Modulos" es string => lo convertimos a lista. Si ya es lista => la usamos tal cual.
        if isinstance(new_settings.get("Modulos", []), str):
            new_module_list = [m.strip() for m in new_settings["Modulos"].split(",") if m.strip()]
        else:
            new_module_list = new_settings.get("Modulos", [])

        new_modules_info = {}
        for mod_name in new_module_list:
            cfg_key = f"Directorio_{mod_name}"
            mod_path = new_settings.get(cfg_key)
            if not mod_path:
                print(f"[WARN] No se encontró la ruta para '{mod_name}'. Saltando.")
                continue

            try:
                module_ref = importlib.import_module(f"Modulos.{mod_name}.Funciones")
                buscar_fn = getattr(module_ref, f"buscar_archivo_{mod_name.lower()}")
                procesar_fn = getattr(module_ref, f"procesar_archivo_{mod_name.lower()}")
                historial_fn = getattr(module_ref, f"rutaHistorial_archivo_{mod_name.lower()}")
                new_modules_info[mod_name] = {
                    "path": mod_path,
                    "buscar": buscar_fn,
                    "procesar": procesar_fn,
                    "historial": historial_fn
                }
            except ImportError as e:
                print(f"[ERROR] No se pudo importar el módulo {mod_name}: {e}")
            except AttributeError as e:
                print(f"[ERROR] Función faltante en {mod_name}: {e}")

        # Actualizamos MODULES_INFO (global o de clase)
        MODULES_INFO.clear()
        MODULES_INFO.update(new_modules_info)

        # Refrescamos la lista de valores en el ComboBox
        self.combo_modulos["values"] = list(MODULES_INFO.keys())

        # Si el que estaba seleccionado ya no existe, limpiamos el combobox
        if self.combo_modulos.get() not in MODULES_INFO:
            self.combo_modulos.set("")

    # ----------------------------------------------------------------
    #   MÉTODOS DE ADMINISTRACIÓN DE MÓDULOS
    # ----------------------------------------------------------------
    def on_change_path(self):
        """Abre un filedialog para cambiar la ruta del módulo seleccionado y reescribe Parametros.cfg."""
        mod_name = self.combo_modulos.get().strip()
        if not mod_name:
            messagebox.showwarning("Módulo no seleccionado", "Seleccione un módulo para cambiar su ruta.")
            return

        new_path = filedialog.askdirectory(title=f"Seleccionar nueva ruta para {mod_name}")
        if not new_path:
            return  # usuario canceló

        settings = read_setting(cfg_file)
        settings[f"Directorio_{mod_name}"] = new_path
        self.write_settings(cfg_file, settings)

        # Preguntamos si queremos recargar la configuración
        if messagebox.askyesno(
            "Ruta actualizada",
            f"Se actualizó la ruta de {mod_name} a:\n{new_path}\n\n¿Desea recargar la configuración actual?"
        ):
            self.reload_modules_info()

    def on_remove_module(self):
        """Elimina el módulo seleccionado de Parametros.cfg y reescribe."""
        mod_name = self.combo_modulos.get().strip()
        if not mod_name:
            messagebox.showwarning("Módulo no seleccionado", "Seleccione un módulo para eliminar.")
            return

        if not messagebox.askyesno("Confirmar", f"¿Seguro que desea eliminar el módulo '{mod_name}'?"):
            return

        settings = read_setting(cfg_file)

        # Aseguramos que "Modulos" sea lista
        mod_value = settings.get("Modulos", [])
        if isinstance(mod_value, str):
            modulos_list = [m.strip() for m in mod_value.split(",") if m.strip()]
        else:
            modulos_list = mod_value

        # Eliminamos el nombre del módulo si existe
        if mod_name in modulos_list:
            modulos_list.remove(mod_name)

        # Guardamos el cambio
        settings["Modulos"] = modulos_list

        # Borramos las entradas Directorio_<mod_name>, <mod_name>_enabled
        if f"Directorio_{mod_name}" in settings:
            del settings[f"Directorio_{mod_name}"]
        if f"{mod_name}_enabled" in settings:
            del settings[f"{mod_name}_enabled"]

        self.write_settings(cfg_file, settings)

        # Pregunta si queremos recargar
        if messagebox.askyesno(
            "Módulo eliminado",
            f"Se ha eliminado '{mod_name}' de la configuración.\n\n¿Desea recargar la configuración actual?"
        ):
            self.reload_modules_info()

    def on_add_module(self):
        """Abre una ventana Toplevel para ingresar un nuevo módulo, su ruta y el directorio de seguimiento."""
        add_win = tk.Toplevel(self)
        add_win.title("Agregar Módulo")

        # Campo: Nombre del Módulo
        ttk.Label(add_win, text="Nombre del Módulo:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        mod_name_var = tk.StringVar()
        ttk.Entry(add_win, textvariable=mod_name_var).grid(row=0, column=1, padx=5, pady=5)

        # Campo: Ruta del Módulo (debe contener Funciones.py)
        ttk.Label(add_win, text="Ruta del Módulo:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        mod_path_var = tk.StringVar()
        ttk.Entry(add_win, textvariable=mod_path_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        def browse_mod_path():
            chosen = filedialog.askdirectory(title="Seleccionar carpeta del módulo (debe contener Funciones.py)")
            if chosen:
                mod_path_var.set(chosen)
        ttk.Button(add_win, text="Examinar", command=browse_mod_path).grid(row=1, column=2, padx=5, pady=5)

        # Campo: Directorio de Seguimiento (ruta para los CSV u otros archivos)
        ttk.Label(add_win, text="Directorio de Seguimiento:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tracking_dir_var = tk.StringVar()
        ttk.Entry(add_win, textvariable=tracking_dir_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        def browse_tracking_dir():
            chosen = filedialog.askdirectory(title="Seleccionar directorio de seguimiento (CSV)")
            if chosen:
                tracking_dir_var.set(chosen)
        ttk.Button(add_win, text="Examinar", command=browse_tracking_dir).grid(row=2, column=2, padx=5, pady=5)

        def confirm_add():
            new_name = mod_name_var.get().strip()
            new_mod_path = mod_path_var.get().strip()
            new_tracking_dir = tracking_dir_var.get().strip()

            if not new_name or not new_mod_path or not new_tracking_dir:
                messagebox.showwarning("Faltan datos", "Ingrese un nombre, la ruta del módulo y el directorio de seguimiento válidos.")
                return

            # Verificar que en la ruta del módulo exista 'Funciones.py'
            funciones_path = os.path.join(new_mod_path, "Funciones.py")
            if not os.path.exists(funciones_path):
                messagebox.showerror("Error", f"No se encontró 'Funciones.py' en la ruta del módulo:\n{new_mod_path}")
                return

            # Opcional: Verificar que el nombre del módulo coincida con el nombre de la carpeta seleccionada
            if os.path.basename(new_mod_path) != new_name:
                messagebox.showwarning("Advertencia", "El nombre del módulo no coincide con el nombre de la carpeta seleccionada.")
                # Puedes decidir si forzar la corrección o permitir continuar.

            # Leer la configuración actual
            settings = read_setting(cfg_file)

            # Asegurarse de que "Modulos" se maneje como lista
            mod_value = settings.get("Modulos", [])
            if isinstance(mod_value, str):
                modulos_list = [m.strip() for m in mod_value.split(",") if m.strip()]
            else:
                modulos_list = mod_value

            if new_name in modulos_list:
                messagebox.showerror("Error", f"El módulo '{new_name}' ya existe.")
                return

            # Agregar el módulo a la lista
            modulos_list.append(new_name)
            settings["Modulos"] = modulos_list

            # Guardar el directorio de seguimiento en 'Directorio_<módulo>'
            settings[f"Directorio_{new_name}"] = new_tracking_dir
            # Si deseas, puedes guardar también la ruta del módulo en una clave separada:
            settings[f"RutaModulo_{new_name}"] = new_mod_path
            settings[f"{new_name}_enabled"] = "True"

            # Escribir los cambios en Parametros.cfg
            self.write_settings(cfg_file, settings)

            if messagebox.askyesno(
                "Módulo agregado",
                f"Se ha agregado el módulo '{new_name}'\nRuta del módulo: {new_mod_path}\nDirectorio de seguimiento: {new_tracking_dir}\n\n¿Desea recargar la configuración actual?"
            ):
                self.reload_modules_info()

            add_win.destroy()

        ttk.Button(add_win, text="Agregar", command=confirm_add).grid(row=3, column=0, columnspan=3, pady=10)


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
    style.map("TButton",
              background=[("active", "#0040FF")],
              foreground=[("active", "#DEDCD3")])

    app = UptimeBot(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
