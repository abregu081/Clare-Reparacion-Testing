#----------------------------------------------
#             FUNCIONES SEGURITY
#----------------------------------------------
import csv
import os
from datetime import datetime

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
