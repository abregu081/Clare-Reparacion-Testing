import flet as ft

def main(page: ft.Page):
    page.title = "Ventana Básica"
    page.window_width = 300
    page.window_height = 200
    
    # Etiqueta
    label = ft.Text("Hola, esta es una ventana básica")
    
    # Botón de cierre
    boton_cerrar = ft.ElevatedButton("Cerrar", on_click=lambda _: page.window_close())
    
    # Agregar elementos a la página
    page.add(label, boton_cerrar)
    
ft.app(target=main)