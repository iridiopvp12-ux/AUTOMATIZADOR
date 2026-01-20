import flet as ft
from src.utils.database import get_user_by_username, verify_password
from src.utils.logger import start_session_log, log_action

class LoginView(ft.Container):
    def __init__(self, page: ft.Page, on_login_success):
        super().__init__()
        self.main_page = page
        self.on_login_success = on_login_success
        self.alignment = ft.Alignment(0, 0)
        self.expand = True

        self.username_input = ft.TextField(label="Usuário", width=300)
        self.password_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)
        self.error_text = ft.Text(color="red")

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Card(
                    content=ft.Container(
                        padding=40,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20,
                            controls=[
                                ft.Text("Contabilidade System", size=24, weight="bold", color=ft.Colors.PRIMARY),
                                ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=64, color=ft.Colors.PRIMARY),
                                self.username_input,
                                self.password_input,
                                self.error_text,
                                ft.ElevatedButton(
                                    text="Entrar",
                                    width=300,
                                    style=ft.ButtonStyle(
                                        padding=20,
                                    ),
                                    on_click=self.handle_login
                                )
                            ]
                        )
                    )
                )
            ]
        )

    def handle_login(self, e):
        username = self.username_input.value
        password = self.password_input.value

        if not username or not password:
            self.error_text.value = "Por favor, preencha todos os campos."
            self.update()
            return

        user = get_user_by_username(username)

        if user and verify_password(user[2], password):
            # user structure: (id, username, password_hash, is_admin, permissions)
            user_data = {
                "id": user[0],
                "username": user[1],
                "is_admin": bool(user[3]),
                "permissions": user[4]
            }

            # Start Logging
            start_session_log(username)
            log_action("Login realizado com sucesso.")

            self.on_login_success(user_data)
        else:
            self.error_text.value = "Usuário ou senha inválidos."
            self.update()
