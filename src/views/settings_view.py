import flet as ft

class SettingsView(ft.Column):
    def __init__(self):
        super().__init__()
        self.controls = [
            ft.Text("Configurações", size=30, weight="bold"),
            ft.Divider(),
            ft.ListTile(
                leading=ft.Icon(ft.icons.DARK_MODE),
                title=ft.Text("Tema Escuro"),
                trailing=ft.Switch(value=False, on_change=lambda e: print("Theme toggle"))
            ),
            ft.ListTile(
                leading=ft.Icon(ft.icons.LANGUAGE),
                title=ft.Text("Idioma"),
                subtitle=ft.Text("Português (Brasil)")
            )
        ]
