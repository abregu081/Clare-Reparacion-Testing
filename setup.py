from cx_Freeze import setup, Executable
import sys
import os

# Datos de la versión
version = "1.8"
changelog = """
Cambios en la versión 1.5:
- Diseño renovado y más detalles en la organización.
- Seguimiento de log con un click en la función (únicamente funciona en el cuadro de seguimiento).
- Se agregó el botón de ordenar por fecha (únicamente disponible para el frame debajo del botón de cargar).
"""

# Escribir la versión y cambios en un archivo
with open("Version.txt", "w", encoding="utf-8") as version_file:
    version_file.write(f"Versión: {version}\n")
    version_file.write(changelog)

# Si la aplicación es una GUI en Windows, se recomienda definir una base
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Esto oculta la consola

# Configuración de cx_Freeze
includes = []
includefiles = ["Version.txt", "assets/Logo_Mirgor.png", "assets/Logo Clare.png"]  # Incluye archivos adicionales, por ejemplo imágenes
excludes = ['tkinter']  # En ocasiones se excluye 'tkinter' si no se necesita (pero en apps GUI normalmente se utiliza)
packages = ['os', 'csv', 'sys', 'datetime', 'tkinter', 'PIL']

# Si deseas asignar un icono a tu aplicación, coloca un archivo .ico (por ejemplo, app_icon.ico) en tu proyecto
exe = Executable(
    "Main.py",            # Archivo principal de tu aplicación
    base=base,            # Para GUI en Windows
    targetName="Clare.exe",  # Nombre del ejecutable
    icon="D:\Herrmienta_trackeo\assets\ICON.png"   # Ruta al archivo de icono (formato .ico)
)

setup(
    name="Clare",
    version=version,
    description="App desarrollada por abregu como herramienta para el puesto de reparación",
    options={'build_exe': {
        'includes': includes,
        'excludes': excludes,
        'packages': packages,
        'include_files': includefiles
    }},
    executables=[exe]
)
