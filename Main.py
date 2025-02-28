# main.py
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import csv
import os
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Importamos el diccionario con la información de cada módulo:
# { 
#   "AutoTest": {
#       "path": "E:\\Seguimiento_Autotest_temporal",
#       "buscar": <func buscar_archivo_autotest>,
#       "procesar": <func procesar_archivo_autotest>,
#       "historial": <func rutaHistorial_archivo_autotest>
#   },
#   ...
# }
from Process import MODULES_INFO

class UptimeBot(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        self.directorio = None
        self.selected_type = None
        self.table_records = []
        self.sort_descending = False  # Para alternar el orden de clasificación en el historial
        
        # ----------------------------------------------------------------
        #   CONFIGURACIÓN DE ESTILOS
        # ----------------------------------------------------------------
        self.style = ttk.Style()
        self.style.configure("Montserrat.TButton", font=("Montserrat", 12, "bold"))
        self.style.map("Montserrat.TButton",
                       background=[("active", "#0052cc")],
                       foreground=[("active", "white")])
        self.style.configure("Selected.TButton", font=("Montserrat", 12, "bold"),
                             background="#0052cc", foreground="white")
        
        # ----------------------------------------------------------------
        #   FRAME SUPERIOR (Logo, etc.)
        # ----------------------------------------------------------------
        button_frame = ttk.Frame(self)
        button_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=30, pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        # Carga y redimensiona logos (ajusta rutas según tu proyecto)
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
        xd_tracker_label = ttk.Label(button_frame, text="[UN-TRACKER]",
                                     font=("Chakra Petch", 32, "bold"),
                                     anchor="center")
        xd_tracker_label.grid(row=0, column=1, sticky="nsew", padx=10)

        # ----------------------------------------------------------------
        #   FRAME IZQUIERDO: S/N + Submit + Historial
        # ----------------------------------------------------------------
        url_frame = ttk.Frame(self)
        url_frame.grid(row=1, column=0, sticky="n", padx=20)
        url_frame.columnconfigure(0, weight=1)
        url_frame.rowconfigure(0, weight=0)
        url_frame.rowconfigure(1, weight=1)

        # Parte superior: Label + Entry + Botón "Buscar"
        top_frame = ttk.Frame(url_frame)
        top_frame.grid(row=0, column=0, sticky="n")
        url_label = ttk.Label(top_frame, text="Scan S/N", font=("Montserrat", 14, "bold"))
        url_label.pack(anchor="center", pady=5)

        self.url_entry = ttk.Entry(top_frame, width=25)
        self.url_entry.pack(anchor="center", pady=5)

        url_actions = ttk.Frame(top_frame)
        url_actions.pack(anchor="center", pady=5)
        submit_button = ttk.Button(url_actions, text="Buscar ", command=self.on_submit)
        submit_button.pack(anchor="center")

        # Parte inferior: Frame para el historial (treeview)
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
        style_small.configure("SmallButton.TButton", font=("Montserrat", 10),padding=(5,2))
        # Ponemos el tree en la fila 0, col 0
        self.history_tree.grid(row=0, column=0, sticky="nsew")
        # Botón para ordenar por fecha
        order_button = ttk.Button(help_frame, text="↑", width= 3, style= "SmallButton.TButton",command=self.ordenar_por_fecha)
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

        # ----------------------------------------------------------------
        #   FRAME INFERIOR: Botones para selección de rutas (DINÁMICO)
        # ----------------------------------------------------------------
        path_frame = ttk.Frame(self)
        path_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        # Para que los botones se distribuyan bien, definimos un número de columnas dinámico
        # según la cantidad de módulos cargados.
        num_modulos = len(MODULES_INFO)
        for i in range(num_modulos):
            path_frame.columnconfigure(i, weight=1)

        # Diccionario para acceder luego a cada botón y cambiar estilos
        self.module_buttons = {}

        # Creación de botones de manera dinámica
        for idx, module_name in enumerate(MODULES_INFO):
            btn = ttk.Button(
                path_frame,
                text=module_name,
                command=lambda m=module_name: self.set_module(m),
                style="Montserrat.TButton"
            )
            btn.grid(row=0, column=idx, padx=5, pady=5, sticky="ew")
            self.module_buttons[module_name] = btn

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
    def set_module(self, module_name):
        """Selecciona el módulo en uso y cambia estilos de botones."""
        info = MODULES_INFO.get(module_name)
        if not info:
            print(f"[ERROR] Módulo '{module_name}' no encontrado en MODULES_INFO")
            return

        self.selected_type = module_name
        self.directorio = info["path"]

        # Ajustamos estilo para remarcar el botón seleccionado
        for m, btn in self.module_buttons.items():
            if m == module_name:
                btn.config(style="Selected.TButton")
            else:
                btn.config(style="Montserrat.TButton")

        print(f"[DEBUG] Ruta seleccionada para {module_name}: {self.directorio}")

    def on_submit(self):
        if not self.directorio:
            print("[ERROR] No se ha seleccionado directorio todavía.")
            return

        sn_value = self.url_entry.get().strip()
        if not sn_value:
            print("[WARN] S/N está vacío, ingrese un valor.")
            return

        self.history_log.delete("1.0", "end")
        file_content = ""
        csv_path = None
        fail_row = None

        # Obtenemos las funciones del módulo seleccionado
        info_modulo = MODULES_INFO.get(self.selected_type)
        if not info_modulo:
            print(f"[ERROR] No hay información de módulo para {self.selected_type}")
            return

        buscar_fn = info_modulo["buscar"]
        procesar_fn = info_modulo["procesar"]

        # 1) Buscar
        csv_path = buscar_fn(sn_value, self.directorio)
        if csv_path is None:
            msg = f"[INFO] No se encontró ningún archivo CSV para S/N '{sn_value}' en '{self.selected_type}'."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        # 2) Procesar
        fail_row = procesar_fn(csv_path)

        if csv_path and not fail_row:
            msg = f"[INFO] No se encontraron filas con FAIL/NG en '{csv_path}' (módulo: {self.selected_type})."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        # Si existe fail_row, leemos el archivo para mostrar su contenido
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
        self.buscar_historial()

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

    def buscar_historial(self):
        """Busca en el historial usando la función del módulo seleccionado."""
        if not self.directorio:
            print("[ERROR] No se ha seleccionado un directorio para historial.")
            return

        codigo = self.url_entry.get().strip()
        if not codigo:
            print("[WARN] Ingrese un código para buscar en el historial.")
            return

        info_modulo = MODULES_INFO.get(self.selected_type)
        if not info_modulo:
            print(f"[ERROR] No hay información de módulo para {self.selected_type}")
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
                "", "end",
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
        self.buscar_historial()

    def clear_screen(self):
        """Limpia el log, el Treeview del historial y la tabla de seguimientos."""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar la pantalla?"):
            # Limpiar el widget del log
            self.history_log.delete("1.0", tk.END)
            # Limpiar el Treeview del historial
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            # Limpiar la tabla de seguimientos (Treeview derecho)
            for item in self.history_table.get_children():
                self.history_table.delete(item)
            # Limpiar los registros almacenados
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

def main():
    root = tk.Tk()
    root.title("CLARE by [Testing UNAE]")
    root.geometry("1280x720")

    # Fondo principal blanco
    root.configure(bg="#FFFFFF")

    # Estilos con ttk y usar el tema 'clam' para mayor personalización
    style = ttk.Style()
    style.theme_use("clam")

    # Fondo blanco para todos los frames
    style.configure("TFrame", background="#FFFFFF")

    # Estilo general para labels
    style.configure("TLabel", background="#FFFFFF", foreground="#000000", font=("Chakra Petch", 12))

    # Estilo para botones
    style.configure("TButton", font=("Montserrat", 12, "bold"), background="#141736", foreground="#FFFFFF")
    style.map("TButton",
              background=[("active", "#0040FF")],
              foreground=[("active", "#DEDCD3")])

    app = UptimeBot(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
