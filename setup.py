import sys
import os
from cx_Freeze import setup, Executable

# Aumentar el límite de recursión si es necesario (opcional)
sys.setrecursionlimit(10000)

# Datos de la versión
version = "1.5"
changelog = """
Cambios en la versión 1.5:
- Diseño renovado y más detalles en la organización.
- Seguimiento de log con un clic en la función (únicamente funciona en el cuadro de seguimiento).
- Se agregó el botón de ordenar por fecha (únicamente disponible para el frame debajo del botón de cargar).
"""

# Escribir la versión y cambios en un archivo
with open("Version.txt", "w", encoding="utf-8") as version_file:
    version_file.write(f"Versión: {version}\n")
    version_file.write(changelog)

# Definir base para ocultar la consola en Windows
base = "Win32GUI" if sys.platform == "win32" else None

# Archivos a incluir
include_files = ["Version.txt"]

# Módulos a incluir
includes = [
    "tkinter",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.ttk",
    "tkinter.scrolledtext",
    "PIL"
]

# Módulos a excluir (para reducir tamaño)
excludes = [
    "unittest",
    "email",
    "http",
    "urllib",
    "xml",
    "logging",
    "asyncio",
    "sqlite3",  # Si no usas SQLite, puedes excluirlo
    "multiprocessing"  # Si no usas procesos paralelos, puedes excluirlo
]

# Paquetes usados en la app
packages = [
    "os", "csv", "sys", "datetime",
    "importlib", "Process"
]

# Definir el ejecutable
exe = Executable(
    script="Main.py",  # Archivo principal de la app
    base=base,
    target_name="Clare.exe"  # Nombre del ejecutable
)

# Configurar cx_Freeze
setup(
    name="Clare",
    version=version,
    description="App desarrollada por abregu como herramienta para el puesto de reparación",
    options={
        "build_exe": {
            "includes": includes,
            "excludes": excludes,
            "packages": packages,
            "include_files": include_files
        }
    },
    executables=[exe]
)
