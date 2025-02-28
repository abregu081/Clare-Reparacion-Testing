#----------------------------------------------
#             FUNCIONES AUTOTEST
#----------------------------------------------
import os
import csv
from datetime import datetime

def buscar_archivo_autotest(codigo, directorio):
    for hostname in os.listdir(directorio):
        hostname_path = os.path.join(directorio, hostname)
        if os.path.isdir(hostname_path):
            fail_path = os.path.join(hostname_path, "FAIL")
            if os.path.exists(fail_path) and os.path.isdir(fail_path):
                for subdir in os.listdir(fail_path):
                    subdir_path = os.path.join(fail_path, subdir)
                    if os.path.isdir(subdir_path):
                        for file in os.listdir(subdir_path):
                            if file.lower().endswith(".csv") and codigo in file:
                                return os.path.join(subdir_path, file)
    return None

def procesar_archivo_autotest(ruta_archivo):
    try:
        if ruta_archivo:
            with open(ruta_archivo, "r") as f:
                csv_reader = csv.reader(f)
                filas = list(csv_reader)
                for fila in filas:
                    if any("FAIL" in celda for celda in fila):
                        return fila 
    except Exception as e:
        print(f"Error al abrir el archivo: {e}")

def extraer_fecha_y_hora(folder_name, file_name):
    """
    Extrae la fecha y la hora usando:
    - El nombre de la carpeta (folder_name) => '230123' => 2023-01-23
    - El nombre del archivo (file_name) => '20230123103000_codigo.csv'
    
    Luego, intenta formatear fecha/hora a un formato más legible (YYYY-MM-DD y HH:MM:SS).
    Si no puede parsear, usa 'Unknown'.
    """
    date_str = "Unknown"
    time_str = "Unknown"
    
    # 1) Intentar extraer la fecha desde la carpeta
    if len(folder_name) == 6 and folder_name.isdigit():
        year, month, day = f"20{folder_name[:2]}", folder_name[2:4], folder_name[4:6]
        date_str = f"{year}{month}{day}"  # '20230123'
    
    # 2) Intentar extraer fecha/hora desde el nombre del archivo
    name_without_extension = os.path.splitext(os.path.basename(file_name))[0]
    parts = name_without_extension.split('_')
    if len(parts) >= 1:
        date_time_part = parts[0]  # p.e. '20230123103000'
        if len(date_time_part) == 14 and date_time_part.isdigit():
            date_str = date_time_part[:8]   # '20230123'
            time_str = date_time_part[8:]   # '103000'
    
    # 3) Formatear fecha y hora a un formato legible
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        date_str = date_obj.strftime("%Y-%m-%d")
    except:
        date_str = "Unknown"
    try:
        time_obj = datetime.strptime(time_str, "%H%M%S")
        time_str = time_obj.strftime("%H:%M:%S")
    except:
        time_str = "Unknown"

    return date_str, time_str

def rutaHistorial_archivo_autotest(codigo, directorio):
    """
    Recorre el 'directorio' buscando en carpetas PASS y FAIL archivos .csv
    cuyo nombre contenga 'codigo'. Devuelve una lista de diccionarios con la
    información (hostname, status, file_path, date_str, time_str).
    """
    resultado_busqueda = []
    for hostname in os.listdir(directorio):
        hostname_path = os.path.join(directorio, hostname)
        if not os.path.isdir(hostname_path):
            continue

        for root, dirs, files in os.walk(hostname_path):
            if "PASS" in root.upper():
                default_result = "PASS"
            elif "FAIL" in root.upper():
                default_result = "FAIL"
            else:
                continue

            for file in files:
                if file.lower().endswith(".csv") and codigo in file:
                    file_path = os.path.join(root, file)
                    folder_name = os.path.basename(root)
                    date_str, time_str = extraer_fecha_y_hora(folder_name, file)
                    resultado_busqueda.append({
                        "hostname": hostname,
                        "status": default_result,
                        "file_path": file_path,
                        "date_str": date_str,
                        "time_str": time_str
                    })
    
    # Ordenar ascendente por fecha/hora
    def parse_datetime(d_str, t_str):
        if d_str == "Unknown" or t_str == "Unknown":
            return None
        try:
            return datetime.strptime(d_str + t_str, "%Y-%m-%d%H:%M:%S")
        except ValueError:
            return None

    resultado_busqueda.sort(key=lambda x: parse_datetime(x["date_str"], x["time_str"]) or datetime.min)
    return resultado_busqueda