import flet as ft

class SpedView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_instance = page  # Store page reference if needed for overlays
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

        # Helper to create an automation card
        def create_automation_card(title, icon, description, on_click):
            return ft.Card(
                elevation=2,
                content=ft.Container(
                    width=300,
                    height=200,
                    padding=20,
                    ink=True,
                    on_click=on_click,
                    border_radius=10,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icon, size=40, color=ft.Colors.PRIMARY),
                            ft.Text(title, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                            ft.Text(description, size=14, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                        ]
                    )
                )
            )

        # Placeholder handler
        def on_card_click(feature_name):
            def handler(e):
                self.page_instance.snack_bar = ft.SnackBar(content=ft.Text(f"Abrindo: {feature_name}"))
                self.page_instance.snack_bar.open = True
                self.page_instance.update()
            return handler

        self.controls = [
            ft.Text("Automações SPED", size=30, weight=ft.FontWeight.BOLD),
            ft.Text("Selecione uma das ferramentas abaixo para iniciar.", color=ft.Colors.GREY_600),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

            ft.Row(
                wrap=True,
                spacing=20,
                run_spacing=20,
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    create_automation_card(
                        "SPED Contribuições",
                        ft.Icons.DESCRIPTION,
                        "Leitura e geração de planilhas de contribuições.",
                        on_card_click("SPED Contribuições")
                    ),
                    create_automation_card(
                        "Filtro por Data",
                        ft.Icons.DATE_RANGE,
                        "Filtrar arquivos SPED por intervalo de datas.",
                        on_card_click("Filtro por Data")
                    ),
                    create_automation_card(
                        "Extrator de Chaves",
                        ft.Icons.VPN_KEY,
                        "Extrair chaves de acesso dos arquivos.",
                        on_card_click("Extrator de Chaves")
                    ),
                ]
            )
        ]
