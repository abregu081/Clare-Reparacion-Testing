#Modulo de busqueda y procesamiento de archivos de autotest
import os
import csv

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




def buscar_archivo_segurity(codigo, directorio):
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

def procesar_archivo_segurity(ruta_archivo):
    try:
        if ruta_archivo:
            with open(ruta_archivo, "r") as f:
                csv_reader = csv.reader(f)
                filas = list(csv_reader)
                for fila in filas:
                    if any("NG" in celda for celda in fila):
                        return fila 
    except Exception as e:
        print(f"Error al abrir el archivo: {e}")


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

