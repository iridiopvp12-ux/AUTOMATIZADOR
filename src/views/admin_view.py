import flet as ft
from src.utils.database import create_user, get_connection, log_action

class AdminView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

        self.users_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Usuário")),
                ft.DataColumn(ft.Text("Admin")),
                ft.DataColumn(ft.Text("Permissões")),
            ],
            rows=[]
        )

        self.controls = [
            ft.Row([
                ft.Text("Gerenciamento de Usuários", size=24, weight="bold"),
                ft.IconButton(ft.Icons.REFRESH, on_click=self.refresh_users)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.ElevatedButton("Criar Novo Usuário", icon=ft.Icons.ADD, on_click=self.open_create_dialog),
            ft.Container(height=20),
            self.users_table
        ]

        # Dialog components
        self.new_username = ft.TextField(label="Nome de Usuário")
        self.new_password = ft.TextField(label="Senha", password=True, can_reveal_password=True)
        self.is_admin_check = ft.Switch(label="É Administrador?")
        self.perm_dashboard = ft.Checkbox(label="Dashboard", value=True)
        self.perm_sped = ft.Checkbox(label="Automação SPED")
        self.perm_settings = ft.Checkbox(label="Configurações")

        self.create_dialog = ft.AlertDialog(
            title=ft.Text("Novo Usuário"),
            content=ft.Column([
                self.new_username,
                self.new_password,
                self.is_admin_check,
                ft.Text("Permissões de Acesso:"),
                self.perm_dashboard,
                self.perm_sped,
                self.perm_settings
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dialog),
                ft.ElevatedButton("Salvar", on_click=self.save_user)
            ]
        )

    def did_mount(self):
        self.refresh_users(None)

    def refresh_users(self, e):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, is_admin, permissions FROM users")
        rows = cursor.fetchall()
        conn.close()

        self.users_table.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(r[0]))),
                ft.DataCell(ft.Text(r[1])),
                ft.DataCell(ft.Icon(ft.Icons.CHECK if r[2] else ft.Icons.CLOSE, color="green" if r[2] else "red")),
                ft.DataCell(ft.Text(r[3] if r[3] else "-")),
            ]) for r in rows
        ]
        self.update()

    def open_create_dialog(self, e):
        self.new_username.value = ""
        self.new_password.value = ""
        self.is_admin_check.value = False
        self.perm_dashboard.value = True
        self.perm_sped.value = False
        self.perm_settings.value = False
        # Use page property from control (available after mount)
        if self.page:
            self.page.dialog = self.create_dialog
            self.create_dialog.open = True
            self.page.update()

    def close_dialog(self, e):
        self.create_dialog.open = False
        if self.page:
            self.page.update()

    def save_user(self, e):
        if not self.page:
            return

        if not self.new_username.value or not self.new_password.value:
            self.page.snack_bar = ft.SnackBar(ft.Text("Preencha usuário e senha!"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        perms = []
        if self.perm_dashboard.value: perms.append("dashboard")
        if self.perm_sped.value: perms.append("sped")
        if self.perm_settings.value: perms.append("settings")

        perms_str = ",".join(perms)

        success = create_user(
            self.new_username.value,
            self.new_password.value,
            self.is_admin_check.value,
            perms_str
        )

        if success:
            log_action(f"Admin created new user: {self.new_username.value}")
            self.close_dialog(None)
            self.refresh_users(None)
            self.page.snack_bar = ft.SnackBar(ft.Text("Usuário criado com sucesso!"))
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Erro: Usuário já existe!"))

        self.page.snack_bar.open = True
        self.page.update()
