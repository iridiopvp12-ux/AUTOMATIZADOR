import flet as ft
from src.utils.database import create_user, get_connection
import traceback

class AdminView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        
        self.main_page = page
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

        # Tabela de Usuários
        self.users_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Usuário")),
                ft.DataColumn(ft.Text("Admin")),
                ft.DataColumn(ft.Text("Permissões")),
            ],
            rows=[]
        )

        # Campos do Formulário
        self.new_username = ft.TextField(label="Nome de Usuário")
        self.new_password = ft.TextField(label="Senha", password=True, can_reveal_password=True)
        self.is_admin_check = ft.Switch(label="É Administrador?", value=False)
        self.perm_dashboard = ft.Checkbox(label="Dashboard", value=True)
        self.perm_sped = ft.Checkbox(label="Automação SPED")
        self.perm_settings = ft.Checkbox(label="Configurações")

        self.controls = [
            ft.Row([
                ft.Text("Gerenciamento de Usuários", size=24, weight="bold"),
                ft.IconButton(ft.Icons.REFRESH, on_click=self.refresh_users)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.ElevatedButton(
                "Criar Novo Usuário", 
                icon=ft.Icons.ADD, 
                on_click=self.open_create_dialog, 
                style=ft.ButtonStyle(bgcolor=ft.Colors.PRIMARY, color=ft.Colors.WHITE)
            ),
            ft.Container(height=20),
            self.users_table
        ]

    def did_mount(self):
        self.refresh_users(None)

    def refresh_users(self, e):
        try:
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
        except Exception as ex:
            print(f"Erro ao atualizar tabela: {ex}")

    def open_create_dialog(self, e):
        # 1. Limpa os campos
        self.new_username.value = ""
        self.new_password.value = ""
        self.is_admin_check.value = False
        self.perm_dashboard.value = True
        self.perm_sped.value = False
        self.perm_settings.value = False
        
        # 2. Cria o diálogo (Modal)
        # Importante: Criamos uma nova instância aqui para garantir que não haja conflito
        self.dialog_obj = ft.AlertDialog(
            title=ft.Text("Novo Usuário"),
            content=ft.Column([
                self.new_username,
                self.new_password,
                self.is_admin_check,
                ft.Divider(),
                ft.Text("Permissões:", weight="bold"),
                self.perm_dashboard,
                self.perm_sped,
                self.perm_settings
            ], tight=True, width=400),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dialog),
                ft.ElevatedButton("Salvar", on_click=self.save_user)
            ]
        )

        # 3. MÉTODO MODERNO: Usa page.open() em vez de page.dialog = ...
        self.main_page.open(self.dialog_obj)
        print("DEBUG: Modal aberto via page.open()")

    def close_dialog(self, e):
        # Fecha usando o método moderno
        self.main_page.close(self.dialog_obj)

    def save_user(self, e):
        if not self.new_username.value or not self.new_password.value:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Preencha usuário e senha!"), bgcolor="red")
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return

        perms = []
        if self.perm_dashboard.value: perms.append("dashboard")
        if self.perm_sped.value: perms.append("sped")
        if self.perm_settings.value: perms.append("settings")
        perms_str = ",".join(perms)

        try:
            success = create_user(
                self.new_username.value,
                self.new_password.value,
                self.is_admin_check.value,
                perms_str
            )

            if success:
                self.close_dialog(None)
                self.refresh_users(None)
                self.main_page.snack_bar = ft.SnackBar(ft.Text("Usuário criado com sucesso!"), bgcolor="green")
            else:
                self.main_page.snack_bar = ft.SnackBar(ft.Text("Erro: Usuário já existe!"), bgcolor="orange")

        except Exception as ex:
            print(f"ERRO: {ex}")
            traceback.print_exc()
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"Erro interno: {ex}"), bgcolor="red")

        self.main_page.snack_bar.open = True
        self.main_page.update()