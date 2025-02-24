import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import csv
import os
from tkinter import filedialog
from PIL import Image, ImageTk
from Process import Autotest_path, Segurity_path, ManualInspection_path
from Autotest import buscar_archivo_autotest, procesar_archivo_autotest, buscar_archivo_segurity, procesar_archivo_segurity, buscar_archivo_manual, procesar_archivo_manual


class UptimeBot(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        self.directorio = None
        self.selected_type = None  # Indica qué ruta se ha seleccionado
        self.table_records = []

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

        # Logo a la izquierda
        logo_label_img = ttk.Label(button_frame, image=self.logo_mirgor)
        logo_label_img.grid(row=0, column=0, sticky="w", padx=10)

        # Fail-Tracker en el centro (con fuente Montserrat)
        fail_tracker_label = ttk.Label(
            button_frame,
            text="[Fail-Tracker]",
            font=("Futura", 32, "bold"),  # Cambia "Futura" por "Montserrat" si la tienes instalada.
            anchor="center"
        )
        fail_tracker_label.grid(row=0, column=1, sticky="nsew", padx=10)

        # Testing UNAE a la derecha (con fuente Montserrat)
        logo_label_txt = ttk.Label(
            button_frame,
            text="Testing UNAE",
            font=("Montserrat", 32, "bold")
        )
        logo_label_txt.grid(row=0, column=2, sticky="e", padx=10)

        # ----------------------------------------------------------------
        #   FRAME IZQUIERDO: S/N + Submit
        # ----------------------------------------------------------------
        url_frame = ttk.Frame(self)
        url_frame.grid(row=1, column=0, sticky="n", padx=20)
        center_frame = ttk.Frame(url_frame)
        center_frame.pack(expand=True, fill="both")
        url_label = ttk.Label(center_frame, text="Scan S/N", font=("Montserrat", 14, "bold"))
        url_label.pack(anchor="center", pady=5)
        self.url_entry = ttk.Entry(center_frame, width=25)
        self.url_entry.pack(anchor="center", pady=5)
        url_actions = ttk.Frame(center_frame)
        url_actions.pack(anchor="center", pady=5)
        submit_button = ttk.Button(url_actions, text="Cargar", command=self.on_submit)
        submit_button.pack(anchor="center")

        # ----------------------------------------------------------------
        #   FRAME DERECHO: Tabla + Log
        # ----------------------------------------------------------------
        history_frame = ttk.Frame(self)
        history_frame.grid(row=1, column=1, rowspan=2, sticky="nsew")
        history_info = ttk.Frame(history_frame)
        history_info.pack(fill="x", expand=False, side="top")
        history_label = ttk.Label(history_info, text="Seguimiento", font=("Montserrat", 14, "bold"))
        history_label.pack(side="left")
        history_download = ttk.Button(history_info, text="Exportar", command=self.download_csv)
        history_download.pack(side="right", fill="both")
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

        # ----------------------------------------------------------------
        #   FRAME INFERIOR: Botones para selección de rutas
        # ----------------------------------------------------------------
        # Definimos un estilo personalizado para los botones con fuente Montserrat
        style = ttk.Style()
        style.configure("Montserrat.TButton", font=("Montserrat", 12, "bold"))
        style.map("Montserrat.TButton",
          background=[("active", "#0052cc")],  # Fondo azul al hacer hover
          foreground=[("active", "white")])

        path_frame = ttk.Frame(self)
        path_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        # Configuramos tres columnas iguales para centrar los botones
        path_frame.columnconfigure(0, weight=1)
        path_frame.columnconfigure(1, weight=1)
        path_frame.columnconfigure(2, weight=1)
        btn_path1 = ttk.Button(path_frame, text="AutoTest", command=self.set_autotest_path, style="Montserrat.TButton")
        btn_path1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        btn_path2 = ttk.Button(path_frame, text="Segurity", command=self.set_segurity_path, style="Montserrat.TButton")
        btn_path2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        btn_path3 = ttk.Button(path_frame, text="ManualInspection", command=self.set_manual_path, style="Montserrat.TButton")
        btn_path3.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=7)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=4)
        self.rowconfigure(2, weight=4)
        self.rowconfigure(3, weight=1)

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
                    writer.writerow(row)
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

    def set_segurity_path(self):
        self.directorio = Segurity_path
        self.selected_type = "Segurity"
        print(f"[DEBUG] Ruta seleccionada para Segurity: {self.directorio}")

    def set_autotest_path(self):
        self.directorio = Autotest_path
        self.selected_type = "AutoTest"
        print(f"[DEBUG] Ruta seleccionada para AutoTest: {self.directorio}")

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
                try:
                    with open(csv_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    with open(csv_path, "r", encoding="cp1252") as f:
                        file_content = f.read()
                fail_row = procesar_archivo_autotest(csv_path)
        elif self.selected_type == "Segurity":
            csv_path = buscar_archivo_segurity(sn_value, self.directorio)
            if csv_path is not None:
                try:
                    with open(csv_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    with open(csv_path, "r", encoding="cp1252") as f:
                        file_content = f.read()
                fail_row = procesar_archivo_segurity(csv_path)
        elif self.selected_type == "ManualInspection":
            csv_path = buscar_archivo_manual(sn_value, self.directorio)
            if csv_path is not None:
                try:
                    with open(csv_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    with open(csv_path, "r", encoding="cp1252") as f:
                        file_content = f.read()
                fail_row = procesar_archivo_manual(csv_path)
        else:
            print("[ERROR] Tipo de directorio no reconocido.")
            return

        if csv_path is None:
            msg = f"[INFO] No se encontró ningún archivo CSV para S/N '{sn_value}'."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        if not fail_row:
            msg = f"[INFO] No se encontraron filas con FAIL en el CSV '{csv_path}'."
            print(msg)
            self.history_log.insert("end", msg + "\n")
            return

        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tipo_value = fail_row[0] if len(fail_row) > 0 else ""
        falla_value = " | ".join(fail_row[1:]) if len(fail_row) > 1 else ""
        new_record = (hora_actual, sn_value, tipo_value, falla_value)
        self.table_records.insert(0, new_record)
        self._rebuild_table()
        self.history_log.insert("end", f"{file_content}")

    def _rebuild_table(self):
        for item in self.history_table.get_children():
            self.history_table.delete(item)
        for row in self.table_records:
            self.history_table.insert("", "end", values=row)

def main():
    root = tk.Tk()
    root.title("CLARE by [Testing UNAE]")
    root.geometry("1280x720")
    app = UptimeBot(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()
