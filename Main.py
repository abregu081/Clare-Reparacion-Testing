import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import csv
import os
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from Process import Autotest_path, Segurity_path, ManualInspection_path
from Funciones_Procesado import (
    buscar_archivo_autotest,
    procesar_archivo_autotest,
    buscar_archivo_segurity,
    procesar_archivo_segurity,
    buscar_archivo_manual,
    procesar_archivo_manual,
    rutaHistorial_archivo_autotest,
    rutaHistorial_archivo_segurity,
    rutaHistorial_archivo_manual_inspection
)

# ------------------------------------------------------------------------------
# CLASE PRINCIPAL
# ------------------------------------------------------------------------------
class UptimeBot(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        self.directorio = None
        self.selected_type = None
        self.table_records = []
        self.sort_descending = False  # Para alternar el orden de clasificación en el historial

        # Creamos estilos para los botones de ruta: normal y seleccionado.
        self.style = ttk.Style()
        self.style.configure("Montserrat.TButton", font=("Montserrat", 12, "bold"))
        self.style.map("Montserrat.TButton",
                       background=[("active", "#0052cc")],
                       foreground=[("active", "white")])
        self.style.configure("Selected.TButton", font=("Montserrat", 12, "bold"),
                             background="#0052cc", foreground="white")
        
        # ----------------------------------------------------------------
        #   FRAME SUPERIOR (Logo, Fail-Tracker, Testing UNAE)
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

        # Fail-Tracker en el centro
        fail_tracker_label = ttk.Label(
            button_frame,
            image=self.logo_clare,
            anchor="center",
        )
        fail_tracker_label.grid(row=0, column=2, sticky="e", padx=10)

        xd_tracker_label = ttk.Label(
            button_frame,
            text="[UN-TRACKER]",
            font=("Chakra Petch", 32, "bold"),
            anchor="center",
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

        # Parte superior: Label + Entry + Botón "Cargar"
        top_frame = ttk.Frame(url_frame)
        top_frame.grid(row=0, column=0, sticky="n")
        url_label = ttk.Label(top_frame, text="Scan S/N", font=("Montserrat", 14, "bold"))
        url_label.pack(anchor="center", pady=5)
        self.url_entry = ttk.Entry(top_frame, width=25)
        self.url_entry.pack(anchor="center", pady=5)
        url_actions = ttk.Frame(top_frame)
        url_actions.pack(anchor="center", pady=5)
        submit_button = ttk.Button(url_actions, text="Buscar", command=self.on_submit)
        submit_button.pack(anchor="center")

        # Parte inferior: Frame para el historial
        help_frame = ttk.Frame(url_frame)
        help_frame.grid(row=1, column=0, sticky="n", pady=10)
        help_frame.rowconfigure(0, weight=1)
        # Treeview para mostrar el historial
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
        self.history_tree.pack(padx=5, pady=5, fill="both", expand=True)
        # Botón para ordenar por fecha (abajo del Treeview)
        order_button = ttk.Button(help_frame, text="Ordenar por Fecha", command=self.ordenar_por_fecha)
        order_button.pack(pady=5)

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
        # Botón "Limpiar Pantalla" al lado
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
        #   FRAME INFERIOR: Botones para selección de rutas
        # ----------------------------------------------------------------
        path_frame = ttk.Frame(self)
        path_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        path_frame.columnconfigure(0, weight=1)
        path_frame.columnconfigure(1, weight=1)
        path_frame.columnconfigure(2, weight=1)
        # Creamos referencias para poder actualizar el estilo al seleccionar
        self.btn_autotest = ttk.Button(path_frame, text="AutoTest", command=self.set_autotest_path, style="Montserrat.TButton")
        self.btn_autotest.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.btn_segurity = ttk.Button(path_frame, text="Segurity", command=self.set_segurity_path, style="Montserrat.TButton")
        self.btn_segurity.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.btn_manual = ttk.Button(path_frame, text="ManualInspection", command=self.set_manual_path, style="Montserrat.TButton")
        self.btn_manual.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Configuración de las filas y columnas principales
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=7)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=4)
        self.rowconfigure(2, weight=4)
        self.rowconfigure(3, weight=1)

    # ----------------------------------------------------------------
    # MÉTODOS PRINCIPALES
    # ----------------------------------------------------------------
    def download_csv(self):
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

    def set_manual_path(self):
        self.directorio = ManualInspection_path
        self.selected_type = "ManualInspection"
        print(f"[DEBUG] Ruta seleccionada para ManualInspection: {self.directorio}")
        # Actualizamos estilos: este botón se marca como seleccionado
        self.btn_manual.config(style="Selected.TButton")
        self.btn_autotest.config(style="Montserrat.TButton")
        self.btn_segurity.config(style="Montserrat.TButton")

    def set_segurity_path(self):
        self.directorio = Segurity_path
        self.selected_type = "Segurity"
        print(f"[DEBUG] Ruta seleccionada para Segurity: {self.directorio}")
        self.btn_segurity.config(style="Selected.TButton")
        self.btn_autotest.config(style="Montserrat.TButton")
        self.btn_manual.config(style="Montserrat.TButton")

    def set_autotest_path(self):
        self.directorio = Autotest_path
        self.selected_type = "AutoTest"
        print(f"[DEBUG] Ruta seleccionada para AutoTest: {self.directorio}")
        self.btn_autotest.config(style="Selected.TButton")
        self.btn_segurity.config(style="Montserrat.TButton")
        self.btn_manual.config(style="Montserrat.TButton")

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

        if self.selected_type == "AutoTest":
            csv_path = buscar_archivo_autotest(sn_value, self.directorio)
            if csv_path is not None:
                fail_row = procesar_archivo_autotest(csv_path)
        elif self.selected_type == "Segurity":
            csv_path = buscar_archivo_segurity(sn_value, self.directorio)
            if csv_path is not None:
                fail_row = procesar_archivo_segurity(csv_path)
        elif self.selected_type == "ManualInspection":
            csv_path = buscar_archivo_manual(sn_value, self.directorio)
            if csv_path is not None:
                fail_row = procesar_archivo_manual(csv_path)
        else:
            print("[ERROR] Tipo de directorio no reconocido.")
            return

        if csv_path is None:
            msg = f"[INFO] No se encontró ningún archivo CSV para S/N '{sn_value}'."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                file_content = f.readlines()
        except UnicodeDecodeError:
            with open(csv_path, "r", encoding="cp1252") as f:
                file_content = f.readlines()

        if not fail_row:
            msg = f"[INFO] No se encontraron filas con FAIL en el CSV '{csv_path}'."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        # Mostrar contenido en `history_log` resaltando la fila con FAIL
        self.history_log.tag_configure("highlight", background="yellow")

        for i, line in enumerate(file_content):
            self.history_log.insert("end", line)
            if fail_row and ",".join(fail_row) in line:
                self.history_log.tag_add("highlight", f"{i + 1}.0", f"{i + 1}.end")

        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tipo_value = fail_row[0] if len(fail_row) > 0 else ""
        falla_value = " | ".join(fail_row[1:]) if len(fail_row) > 1 else ""
        new_record = (hora_actual, sn_value, tipo_value, falla_value, "".join(file_content))
    
        self.table_records.insert(0, new_record)
        self._rebuild_table()
        self.buscar_historial()

    def _rebuild_table(self):
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
        """Busca en el historial según el tipo de directorio (AutoTest, Segurity, ManualInspection)
        y muestra los registros en el Treeview."""
        if not self.directorio:
            print("[ERROR] No se ha seleccionado un directorio para historial.")
            return
        codigo = self.url_entry.get().strip()
        if not codigo:
            print("[WARN] Ingrese un código para buscar en el historial.")
            return

        # Seleccionar la función de búsqueda según el tipo
        if self.selected_type == "AutoTest":
            registros = rutaHistorial_archivo_autotest(codigo, self.directorio)
        elif self.selected_type == "Segurity":
            registros = rutaHistorial_archivo_segurity(codigo, self.directorio)
        elif self.selected_type == "ManualInspection":
            registros = rutaHistorial_archivo_manual_inspection(codigo, self.directorio)
        else:
            print("[ERROR] Tipo de directorio no reconocido para historial.")
            return

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
        """Pregunta al usuario y, si confirma, limpia el log, el Treeview del historial y la tabla de seguimientos."""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar la pantalla?"):
            # Limpiar el widget del log
            self.history_log.delete("1.0", tk.END)
            # Limpiar el Treeview del historial
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            # Limpiar la tabla de seguimientos (Treeview derecho)
            for item in self.history_table.get_children():
                self.history_table.delete(item)
            # Opcional: Limpiar los registros almacenados internamente
            self.table_records.clear()

def main():
    root = tk.Tk()
    root.title("CLARE by [Testing UNAE]")
    root.geometry("1280x720")

    # Fondo principal blanco
    root.configure(bg="#FFFFFF")

    # Configurar estilos con ttk y usar el tema 'clam' para mayor personalización
    style = ttk.Style()
    style.theme_use("clam")
    
    # Fondo blanco para todos los frames
    style.configure("TFrame", background="#FFFFFF")
    
    # Estilo general para labels: fondo blanco y texto azul vibrante
    style.configure("TLabel", background="#FFFFFF", foreground="#000000", font=("Chakra Petch", 12))
    
    # Estilo para botones: fondo azul vibrante y texto blanco
    style.configure("TButton", font=("Montserrat", 12, "bold"), background="#141736", foreground="#FFFFFF")
    style.map("TButton",
              background=[("active", "#0040FF")],
              foreground=[("active", "#DEDCD3")])
    
    # Inicia la aplicación
    app = UptimeBot(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()

