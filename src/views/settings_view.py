import flet as ft
import shutil
import os
from datetime import datetime

class SettingsView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page

        # Configura File Picker para backup
        self.backup_picker = ft.FilePicker(on_result=self.on_backup_result)
        if self.backup_picker not in self.main_page.overlay:
            self.main_page.overlay.append(self.backup_picker)
            self.main_page.update()

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
            ),
            ft.Divider(),
            ft.Text("Dados", size=20, weight="bold"),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.STORAGE),
                title=ft.Text("Backup do Banco de Dados"),
                subtitle=ft.Text("Salvar cópia de segurança do sistema."),
                trailing=ft.ElevatedButton("Fazer Backup", on_click=self.request_backup)
            )
        ]

    def request_backup(self, e):
        self.backup_picker.save_file(
            dialog_title="Salvar Backup do Banco",
            file_name=f"contabilidade_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            allowed_extensions=["db"]
        )

    def on_backup_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            try:
                db_source = "contabilidade.db"
                if os.path.exists(db_source):
                    shutil.copy(db_source, e.path)
                    self.main_page.snack_bar = ft.SnackBar(ft.Text("Backup realizado com sucesso!"), bgcolor="green")
                else:
                    self.main_page.snack_bar = ft.SnackBar(ft.Text("Erro: Banco de dados original não encontrado."), bgcolor="red")
            except Exception as ex:
                self.main_page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar backup: {ex}"), bgcolor="red")

            self.main_page.snack_bar.open = True
            self.main_page.update()

    def toggle_theme(self, e):
        if self.main_page.theme_mode == ft.ThemeMode.DARK:
            self.main_page.theme_mode = ft.ThemeMode.LIGHT
        else:
            self.main_page.theme_mode = ft.ThemeMode.DARK
        self.main_page.update()
