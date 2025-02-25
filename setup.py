from cx_Freeze import setup, Executable

# Datos de la versión
version = "1.5"
changelog = """
Cambios en la versión 1.5:
- Diseño renovado y mas detalles en la organizacion
- Seguimiento de log con un click en la funcion unicamente funciona en el cuadro de seguimiento
- Se agrego el boton de ordenar por fecha unicamente disponible para el frame que se encuentra por debajo del boton de cargar 
"""
# Escribir la versión y cambios en un archivo
with open("Version.txt", "w", encoding="utf-8") as version_file:
    version_file.write(f"Versión: {version}\n")
    version_file.write(changelog)

# Configuración de cx_Freeze
includes = []
includefiles = ["Version.txt"]  # Aseguramos que se incluya en el .exe
excludes = ['tkinter']  # Corregido: 'Tkinter' -> 'tkinter'
packages = [
    'os', 'csv', 'sys', 're', 'collections', 'datetime', 'socket',
    'tkinter', 'PIL'
] 

setup(
    name="Clare",
    version=version,
    description="App desarrolloda por abregu como herramienta para el puesto de reparacion",
    options={'build_exe': {'excludes': excludes, 'packages': packages, 'include_files': includefiles}},
    executables=[Executable("Main.py")]
)
