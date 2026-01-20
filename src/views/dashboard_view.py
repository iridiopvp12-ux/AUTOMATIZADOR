import flet as ft

class DashboardView(ft.Column):
    def __init__(self):
        super().__init__()
        self.controls = [
            ft.Text("Dashboard", size=30, weight="bold"),
            ft.Divider(),
            ft.Row([
                self.build_stat_card("Clientes Ativos", "120", ft.Icons.PEOPLE),
                self.build_stat_card("Processos Pendentes", "15", ft.Icons.PENDING_ACTIONS, "orange"),
                self.build_stat_card("Processos Concluídos", "1050", ft.Icons.CHECK_CIRCLE, "green"),
            ], wrap=True, spacing=20)
        ]

    def build_stat_card(self, title, value, icon, color="blue"):
        return ft.Card(
            content=ft.Container(
                width=250,
                padding=20,
                content=ft.Column([
                    ft.Icon(icon, size=40, color=color),
                    ft.Text(value, size=40, weight="bold"),
                    ft.Text(title, size=16, color="grey")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
