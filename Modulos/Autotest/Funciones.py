#----------------------------------------------
#             FUNCIONES AUTOTEST (MODULAR)
#----------------------------------------------
import os
import csv
from datetime import datetime


def buscar_archivo_autotest(codigo, directorio):
    """
    Busca recursivamente archivos .csv dentro de carpetas con 'FAIL' o 'PASS' en su ruta.
    Devuelve la primera coincidencia o None si no encuentra nada.
    """
    for root, _, files in os.walk(directorio):
        root_up = root.upper()
        if ("FAIL" in root_up) or ("PASS" in root_up):
            for file in files:
                if file.lower().endswith(".csv") and codigo in file:
                    return os.path.join(root, file)
    return None


def procesar_archivo_autotest(ruta_archivo):
    """
    Abre el archivo CSV y busca la primera fila que contenga la palabra 'FAIL'.
    Si la encuentra, retorna esa fila (lista de celdas), de lo contrario retorna None.
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


def extraer_fecha_y_hora(folder_name, file_name):
    """
    Extrae la fecha y la hora usando:
    - El nombre de la carpeta (folder_name) => '230123' => 2023-01-23
    - El nombre del archivo (file_name) => '20230123103000_codigo.csv'
    
    Luego, intenta formatear fecha/hora a un formato legible (YYYY-MM-DD y HH:MM:SS).
    Si no puede parsear, usa 'Unknown'.
    """
    date_str = "Unknown"
    time_str = "Unknown"
    
    # 1) Intentar extraer la fecha desde la carpeta
    if len(folder_name) == 6 and folder_name.isdigit():
        year = f"20{folder_name[:2]}"
        month = folder_name[2:4]
        day = folder_name[4:6]
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


# --------------------------------------------------------------------
#   NUEVAS FUNCIONES PARA DETECTAR HOSTNAME Y PROCESAR RECURSIVAMENTE
# --------------------------------------------------------------------
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


def rutaHistorial_archivo_autotest(codigo, directorio):
    """
    Recorre el 'directorio' y encuentra archivos .csv en subcarpetas FAIL/PASS
    que contengan 'codigo'. Puede operar de dos maneras:
    
    1) Si 'directorio' es ya una carpeta de hostname (tiene subcarpetas FAIL/PASS),
       se procesa directamente.
    2) Si no, asume que 'directorio' contiene múltiples carpetas hostname,
       y para cada una que contenga subcarpetas FAIL o PASS, se realiza el proceso.

    Devuelve una lista de diccionarios con:
      {
        'hostname': <nombre_de_la_carpeta>,
        'status': 'FAIL' o 'PASS',
        'file_path': <ruta_completa_del_archivo>,
        'date_str': <fecha_formateada>,
        'time_str': <hora_formateada>
      }
    ordenados por fecha/hora ascendente.
    """
    resultado_busqueda = []

    # Función auxiliar para convertir fecha/hora a datetime
    def parse_datetime(d_str, t_str):
        if d_str == "Unknown" or t_str == "Unknown":
            return None
        try:
            return datetime.strptime(d_str + t_str, "%Y-%m-%d%H:%M:%S")
        except ValueError:
            return None

    def procesar_hostname(hostname, hostname_path):
        """
        Recorre recursivamente 'hostname_path' para buscar archivos CSV
        en subcarpetas FAIL/PASS que contengan 'codigo', y los agrega al
        listado 'resultado_busqueda'.
        """
        for root, dirs, files in os.walk(hostname_path):
            root_up = root.upper()
            if "PASS" in root_up:
                status = "PASS"
            elif "FAIL" in root_up:
                status = "FAIL"
            else:
                # Si no detectamos FAIL ni PASS en la ruta, no procesamos
                continue

            for file in files:
                if file.lower().endswith(".csv") and codigo in file:
                    file_path = os.path.join(root, file)
                    folder_name = os.path.basename(root)
                    date_str, time_str = extraer_fecha_y_hora(folder_name, file)
                    resultado_busqueda.append({
                        "hostname": hostname,
                        "status": status,
                        "file_path": file_path,
                        "date_str": date_str,
                        "time_str": time_str
                    })

    # -----------------------------------------------------------------
    #   Lógica principal: detectar si 'directorio' es un hostname o no
    # -----------------------------------------------------------------
    if es_carpeta_hostname(directorio):
        # El directorio es directamente un hostname
        hostname = os.path.basename(directorio)
        procesar_hostname(hostname, directorio)
    else:
        # El directorio contiene potencialmente varias carpetas hostname
        for hostname in os.listdir(directorio):
            hostname_path = os.path.join(directorio, hostname)
            if not os.path.isdir(hostname_path):
                continue
            # Si la carpeta 'hostname' es en verdad un hostname con FAIL/PASS
            if es_carpeta_hostname(hostname_path):
                procesar_hostname(hostname, hostname_path)

    # Ordenar por fecha/hora ascendente
    resultado_busqueda.sort(key=lambda x: parse_datetime(x["date_str"], x["time_str"]) or datetime.min)
    return resultado_busqueda