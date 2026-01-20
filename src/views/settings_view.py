import flet as ft

class SettingsView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page

        # Determine initial value based on current theme mode
        is_dark = self.main_page.theme_mode == ft.ThemeMode.DARK

        self.controls = [
            ft.Text("Configurações", size=30, weight="bold"),
            ft.Divider(),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.DARK_MODE),
                title=ft.Text("Tema Escuro"),
                trailing=ft.Switch(value=is_dark, on_change=self.toggle_theme)
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.LANGUAGE),
                title=ft.Text("Idioma"),
                subtitle=ft.Text("Português (Brasil)")
            )
        ]

    def toggle_theme(self, e):
        if self.main_page.theme_mode == ft.ThemeMode.DARK:
            self.main_page.theme_mode = ft.ThemeMode.LIGHT
        else:
            self.main_page.theme_mode = ft.ThemeMode.DARK
        self.main_page.update()
