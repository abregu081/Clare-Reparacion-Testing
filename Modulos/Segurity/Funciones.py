#----------------------------------------------
#             FUNCIONES SEGURITY
#----------------------------------------------
import csv
import os
from datetime import datetime

def buscar_archivo_segurity(codigo, directorio):
    """
    Recorre recursivamente el 'directorio' para encontrar el primer
    archivo .csv cuyo nombre contenga 'codigo', dentro de carpetas
    que contengan 'FAIL' o 'PASS' en su ruta.
    Retorna la ruta absoluta o None si no encuentra nada.
    """
    for root, _, files in os.walk(directorio):
        root_up = root.upper()
        if "FAIL" in root_up or "PASS" in root_up:
            for file in files:
                if file.lower().endswith(".csv") and codigo in file:
                    return os.path.join(root, file)
    return None


def procesar_archivo_segurity(ruta_archivo):
    """
    Abre el 'ruta_archivo' CSV en modo lectura, omite la cabecera,
    y revisa cada fila para ver si alguna celda es exactamente 'NG'.
    Retorna la primera fila en que aparezca 'NG', o None si no la hay.
    """
    try:
        if ruta_archivo:
            with open(ruta_archivo, "r", newline="", encoding="utf-8") as f:
                csv_reader = csv.reader(f)
                _header = next(csv_reader, None)  # Omitimos la cabecera
                for fila in csv_reader:
                    if any(celda.strip() == "NG" for celda in fila):
                        return fila
    except Exception as e:
        print(f"Error al abrir el archivo: {e}")
    return None


def es_carpeta_hostname_seg(path):
    """
    Retorna True si en 'path' (carpeta) existe al menos la estructura:
       station/ -> carpeta_fecha (6 dígitos) -> FAIL/PASS
    """
    if not os.path.isdir(path):
        return False

    for station in os.listdir(path):
        station_path = os.path.join(path, station)
        if not os.path.isdir(station_path):
            continue

        for carpeta_fecha in os.listdir(station_path):
            fecha_path = os.path.join(station_path, carpeta_fecha)
            if not (os.path.isdir(fecha_path) and carpeta_fecha.isdigit() and len(carpeta_fecha) == 6):
                continue

            for estado in ("FAIL", "PASS"):
                carpeta_estado = os.path.join(fecha_path, estado)
                if os.path.isdir(carpeta_estado):
                    return True
    return False


def procesar_hostname_seg(hostname_path, hostname, codigo):
    """
    Recorre la estructura station/ -> carpeta_fecha (6 dígitos) -> [FAIL|PASS]
    buscando archivos .csv cuyo nombre contenga 'codigo'.
    Extrae date_str de la carpeta_fecha y time_str de la primera fila del CSV.
    
    Retorna una lista de diccionarios:
       {hostname, status, file_path, date_str, time_str}
    """
    resultados = []

    for station in os.listdir(hostname_path):
        station_path = os.path.join(hostname_path, station)
        if not os.path.isdir(station_path):
            continue

        for carpeta_fecha in os.listdir(station_path):
            fecha_path = os.path.join(station_path, carpeta_fecha)
            if not (os.path.isdir(fecha_path) and carpeta_fecha.isdigit() and len(carpeta_fecha) == 6):
                continue

            # Construimos date_str en formato YYYY-MM-DD
            date_str = "20" + carpeta_fecha  # => '20230226', p.ej.
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"  # => '2023-02-26'

            for estado in ["FAIL", "PASS"]:
                carpeta_estado = os.path.join(fecha_path, estado)
                if not os.path.exists(carpeta_estado):
                    continue

                for subcarpeta in os.listdir(carpeta_estado):
                    subcarpeta_path = os.path.join(carpeta_estado, subcarpeta)
                    if not os.path.isdir(subcarpeta_path):
                        continue

                    for archivo in os.listdir(subcarpeta_path):
                        if archivo.lower().endswith(".csv") and codigo in archivo:
                            file_path = os.path.join(subcarpeta_path, archivo)
                            time_str = ""
                            try:
                                with open(file_path, "r", newline="", encoding="utf-8") as f:
                                    csv_reader = csv.reader(f)
                                    _header = next(csv_reader, None)  # Cabecera
                                    first_row = next(csv_reader, None)
                                    if first_row and len(first_row) > 7:
                                        # Columna "START TIME" = índice 7 (ajusta si difiere)
                                        time_str = first_row[7]
                            except Exception as e:
                                print(f"Error leyendo archivo {file_path}: {e}")

                            resultados.append({
                                "hostname": hostname,
                                "status": estado,
                                "file_path": file_path,
                                "date_str": date_str,
                                "time_str": time_str
                            })

    return resultados


def rutaHistorial_archivo_segurity(codigo, directorio):
    """
    Recorre la estructura:

        directorio/  [o carpeta hostname directa]
           hostname/
               station/
                   carpeta_fecha (6 dígitos)
                       [FAIL|PASS]/
                           subcarpeta/
                               archivo.csv

    Devuelve una lista de diccionarios:
      {
        "hostname", "status", "file_path",
        "date_str", "time_str"
      }
    """
    resultado_busqueda = []

    def parse_datetime(d_str, t_str):
        if d_str == "Unknown" or t_str == "Unknown":
            return None
        try:
            return datetime.strptime(d_str + t_str, "%Y-%m-%d%H:%M:%S")
        except ValueError:
            return None

    # 1) ¿directorio es una carpeta hostname?
    if es_carpeta_hostname_seg(directorio):
        hostname = os.path.basename(directorio)
        resultado_busqueda.extend(procesar_hostname_seg(directorio, hostname, codigo))
    else:
        # 2) Sino, iteramos cada subcarpeta como posible hostname
        for hostname in os.listdir(directorio):
            hostname_path = os.path.join(directorio, hostname)
            if not os.path.isdir(hostname_path):
                continue

            if es_carpeta_hostname_seg(hostname_path):
                resultado_busqueda.extend(procesar_hostname_seg(hostname_path, hostname, codigo))

    # Ordenar ascendente por fecha/hora
    resultado_busqueda.sort(key=lambda x: parse_datetime(x["date_str"], x["time_str"]) or datetime.min)
    return resultado_busqueda
