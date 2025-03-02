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
      - date_str (YYYY-MM-DD) (se arma a partir de la carpeta_fecha)
      - time_str (se obtiene de la primera fila de datos, columna "START TIME")
    """
    resultado_busqueda = []
    
    for hostname in os.listdir(directorio):
        hostname_path = os.path.join(directorio, hostname)
        if not os.path.isdir(hostname_path):
            continue
        
        for station in os.listdir(hostname_path):
            station_path = os.path.join(hostname_path, station)
            if not os.path.isdir(station_path):
                continue
            
            for carpeta_fecha in os.listdir(station_path):
                fecha_path = os.path.join(station_path, carpeta_fecha)
                # Verifica que la carpeta sea de 6 dígitos (ej: '230226')
                if not (os.path.isdir(fecha_path) and carpeta_fecha.isdigit() and len(carpeta_fecha) == 6):
                    continue
                
                # Construye la fecha en formato YYYY-MM-DD
                date_str = "20" + carpeta_fecha  # => '20230226' p.ej.
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
                                
                                # Inicializamos time_str como vacío
                                time_str = ""
                                try:
                                    with open(file_path, "r", newline="", encoding="utf-8") as f:
                                        csv_reader = csv.reader(f)
                                        header = next(csv_reader, None)  # Omitimos la cabecera
                                        
                                        # Tomamos la PRIMERA fila de datos
                                        first_row = next(csv_reader, None)  # <-- aquí leemos la primera fila real
                                        if first_row and len(first_row) > 7:
                                            # Supongamos que la columna "START TIME" es la 8ª (índice 7)
                                            time_str = first_row[7]  # <-- extraemos el valor
                                
                                except Exception as e:
                                    print(f"Error leyendo el archivo {file_path}: {e}")
                                
                                resultado_busqueda.append({
                                    "hostname": hostname,
                                    "status": estado,
                                    "file_path": file_path,
                                    "date_str": date_str,
                                    "time_str": time_str
                                })
    return resultado_busqueda