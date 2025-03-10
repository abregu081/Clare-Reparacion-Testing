# ----------------------------------------------
#             FUNCIONES MANUAL Y OQC
# ----------------------------------------------
import os
import csv
from datetime import datetime

def extraer_fecha_y_hora(folder_name, file_name):
    """
    Extrae la fecha y la hora usando:
    - El nombre de la carpeta (folder_name) => '230123' => 2023-01-23
    - El nombre del archivo (file_name) => '250226061538_005224522800D9540000905725_FAIL'
    
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
        date_time_part = parts[0]  # Ejemplo: '250226061538'
        # Si tiene 14 dígitos (YYYYMMDDHHMMSS)
        if len(date_time_part) == 14 and date_time_part.isdigit():
            date_str = date_time_part[:8]   # 'YYYYMMDD'
            time_str = date_time_part[8:]   # 'HHMMSS'
        # Si tiene 12 dígitos (YYMMDDHHMMSS)
        elif len(date_time_part) == 12 and date_time_part.isdigit():
            try:
                dt = datetime.strptime(date_time_part, "%y%m%d%H%M%S")
                date_str = dt.strftime("%Y%m%d")
                time_str = dt.strftime("%H%M%S")
            except Exception as e:
                # Si ocurre un error, se dejan como 'Unknown'
                print(f"Error al parsear fecha y hora: {e}")

    # 3) Formatear fecha y hora a un formato legible
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        date_str = date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        date_str = "Unknown"
        print(f"Error al formatear la fecha: {e}")

    try:
        time_obj = datetime.strptime(time_str, "%H%M%S")
        time_str = time_obj.strftime("%H:%M:%S")
    except Exception as e:
        time_str = "Unknown"
        print(f"Error al formatear la hora: {e}")

    return date_str, time_str


def buscar_archivo_manualinspection(codigo, directorio):
    """
    Busca recursivamente archivos .csv dentro de carpetas cuyo nombre contenga 'FAIL' o 'PASS'.
    Devuelve la primera coincidencia (ruta absoluta) o None si no encuentra nada.
    """
    for root, _, files in os.walk(directorio):
        root_up = root.upper()
        if ("FAIL" in root_up) or ("PASS" in root_up):
            for file in files:
                if file.lower().endswith(".csv") and codigo in file:
                    return os.path.join(root, file)
    return None


def procesar_archivo_manualinspection(ruta_archivo):
    """
    Busca en el CSV la primera fila donde aparezca 'FAIL'. 
    Retorna esa fila (lista de celdas) o None si no la encuentra.
    """
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
    return None


def es_carpeta_hostname(path):
    """
    Retorna True si 'path' (carpeta) contiene subcarpetas 'FAIL' o 'PASS'.
    """
    if not os.path.isdir(path):
        return False
    for item in os.listdir(path):
        if item.upper() in ("FAIL", "PASS"):
            subfolder = os.path.join(path, item)
            if os.path.isdir(subfolder):
                return True
    return False


def rutaHistorial_archivo_manualinspection(codigo, directorio):
    """
    Recorre 'directorio' y busca todos los archivos CSV que contengan 'codigo',
    dentro de subcarpetas FAIL o PASS, retornando una lista de diccionarios:
        {
          "hostname": nombre_de_la_carpeta,
          "status": 'FAIL' o 'PASS',
          "file_path": ruta absoluta al CSV,
          "date_str": fecha en formato YYYY-MM-DD,
          "time_str": hora en formato HH:MM:SS
        }
    Ordena los resultados ascendentemente por fecha y hora.

    - Si 'directorio' es ya la carpeta de un hostname (contiene subcarpetas FAIL/PASS),
      lo procesa directamente.
    - De lo contrario, asume que 'directorio' contiene múltiples carpetas hostname, 
      y recorre cada una de ellas.
    """
    resultado_busqueda = []

    def parse_datetime(d_str, t_str):
        if d_str == "Unknown" or t_str == "Unknown":
            return None
        try:
            return datetime.strptime(d_str + t_str, "%Y-%m-%d%H:%M:%S")
        except ValueError:
            return None

    def procesar_hostname(hostname, path_hostname):
        """
        Busca archivos CSV con 'codigo' en subcarpetas FAIL/PASS de path_hostname,
        y los agrega a resultado_busqueda.
        """
        for root, dirs, files in os.walk(path_hostname):
            root_up = root.upper()
            if "PASS" in root_up:
                default_result = "PASS"
            elif "FAIL" in root_up:
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

    # Caso 1: El 'directorio' dado es ya una carpeta 'hostname'
    if es_carpeta_hostname(directorio):
        hostname = os.path.basename(directorio)
        procesar_hostname(hostname, directorio)
    else:
        # Caso 2: 'directorio' contiene múltiples hostnames
        for hostname in os.listdir(directorio):
            path_hostname = os.path.join(directorio, hostname)
            if not os.path.isdir(path_hostname):
                continue
            if es_carpeta_hostname(path_hostname):
                procesar_hostname(hostname, path_hostname)

    # Ordenar ascendentemente por fecha/hora
    resultado_busqueda.sort(key=lambda x: parse_datetime(x["date_str"], x["time_str"]) or datetime.min)
    return resultado_busqueda