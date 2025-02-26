#Modulo de busqueda y procesamiento de archivos segun el medio a analizar
import os
import csv
from datetime import datetime

#----------------------------------------------
#             FUNCIONES AUTOTEST
#----------------------------------------------

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

#----------------------------------------------
#             FUNCIONES SEGURITY
#----------------------------------------------

def buscar_archivo_segurity(codigo, directorio):
    # directorio es la carpeta raíz, por ejemplo: D:\Seguimiento_segurity_temporal
    for hostname in os.listdir(directorio):
        hostname_path = os.path.join(directorio, hostname)
        if os.path.isdir(hostname_path):
            # Dentro del hostname (ej. DESKTOP-14OEBLB) se encuentra la carpeta de estación (ej. STLA_R28.03)
            for station in os.listdir(hostname_path):
                station_path = os.path.join(hostname_path, station)
                if os.path.isdir(station_path):
                    # Dentro de la estación se encuentran carpetas con fechas (ej. 250225)
                    for fecha in os.listdir(station_path):
                        fecha_path = os.path.join(station_path, fecha)
                        if os.path.isdir(fecha_path):
                            # Dentro de la carpeta de fecha se espera la subcarpeta "FAIL"
                            fail_path = os.path.join(fecha_path, "FAIL")
                            if os.path.isdir(fail_path):
                                # Dentro de "FAIL" se tiene una subcarpeta con el código, por ejemplo:
                                # 005224522800D9540034105625
                                for subfolder in os.listdir(fail_path):
                                    subfolder_path = os.path.join(fail_path, subfolder)
                                    if os.path.isdir(subfolder_path) and codigo in subfolder:
                                        # Dentro de esa subcarpeta se busca el archivo CSV
                                        for file in os.listdir(subfolder_path):
                                            if file.lower().endswith(".csv") and codigo in file:
                                                return os.path.join(subfolder_path, file)
    return None


def procesar_archivo_segurity(ruta_archivo):
    try:
        if ruta_archivo:
            with open(ruta_archivo, "r", newline="", encoding="utf-8") as f:
                csv_reader = csv.reader(f)
                # Se omite la cabecera
                header = next(csv_reader, None)
                for fila in csv_reader:
                    # Se revisa cada celda para ver si alguna es exactamente "NG" (sin espacios)
                    if any(celda.strip() == "NG" for celda in fila):
                        return fila
    except Exception as e:
        print(f"Error al abrir el archivo: {e}")

def rutaHistorial_archivo_segurity(codigo, directorio):
    """
    Recorre la siguiente estructura:
    
    directorio/
        hostname/
            station/
                carpeta_fecha (6 dígitos)
                    [FAIL | PASS]/
                        subcarpeta/
                            archivo.csv
    
    Busca archivos .csv cuyo nombre contenga 'codigo' y devuelve una lista de diccionarios con:
      - hostname
      - status (FAIL o PASS)
      - file_path
      - date_str (formado como "20" + carpeta_fecha)
      - time_str (se deja vacío o se extrae de algún dato adicional si se requiere)
    """
    resultado_busqueda = []
    
    # Recorremos cada carpeta en el directorio raíz (hostname)
    for hostname in os.listdir(directorio):
        hostname_path = os.path.join(directorio, hostname)
        if not os.path.isdir(hostname_path):
            continue
        
        # Dentro de cada hostname se espera una carpeta de estación (ej: STLA_R28.03)
        for station in os.listdir(hostname_path):
            station_path = os.path.join(hostname_path, station)
            if not os.path.isdir(station_path):
                continue
            
            # Se recorren las carpetas de fecha (debe ser numérica y de 6 dígitos)
            for carpeta_fecha in os.listdir(station_path):
                fecha_path = os.path.join(station_path, carpeta_fecha)
                if not (os.path.isdir(fecha_path) and carpeta_fecha.isdigit() and len(carpeta_fecha) == 6):
                    continue
                
                # Podemos formar una cadena de fecha; por ejemplo, "20" + carpeta_fecha
                date_str = "20" + carpeta_fecha  
                
                # Revisamos ambos estados: FAIL y PASS
                for estado in ["FAIL", "PASS"]:
                    carpeta_estado = os.path.join(fecha_path, estado)
                    if not os.path.exists(carpeta_estado):
                        continue
                    
                    # Dentro de carpeta_estado se encuentran subcarpetas
                    for subcarpeta in os.listdir(carpeta_estado):
                        subcarpeta_path = os.path.join(carpeta_estado, subcarpeta)
                        if not os.path.isdir(subcarpeta_path):
                            continue
                        
                        # Iteramos sobre los archivos dentro de la subcarpeta
                        for archivo in os.listdir(subcarpeta_path):
                            if archivo.lower().endswith(".csv") and codigo in archivo:
                                file_path = os.path.join(subcarpeta_path, archivo)
                                # Si se requiere extraer la hora u otros datos, se podría llamar a una función adicional;
                                # por ahora, dejamos time_str vacío.
                                time_str = ""
                                resultado_busqueda.append({
                                    "hostname": hostname,
                                    "status": estado,
                                    "file_path": file_path,
                                    "date_str": date_str,
                                    "time_str": time_str
                                })
    return resultado_busqueda


#----------------------------------------------
#             FUNCIONES MANUAL Y OQC
#----------------------------------------------

def buscar_archivo_manual(codigo, directorio):
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

def procesar_archivo_manual(ruta_archivo):
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

def rutaHistorial_archivo_manual_inspection(codigo,directorio):
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
