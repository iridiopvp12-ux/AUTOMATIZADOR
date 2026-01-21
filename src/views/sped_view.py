import flet as ft

class SpedView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_instance = page
        self.expand = True

        # State
        self.active_tab_label = "Menu"
        self.open_tabs = ["Menu"] # List of labels

        # UI Components
        self.tabs_row = ft.Row(scroll=ft.ScrollMode.AUTO)
        self.content_area = ft.Container(expand=True, padding=20)

        self.controls = [
            ft.Container(
                content=self.tabs_row,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
            ),
            self.content_area
        ]

        # Cache for contents
        self.tab_contents = {}

        # Initialize Menu Content
        self.init_menu()

        # Render initial state
        self.render_tabs()
        self.set_content("Menu")

    def init_menu(self):
        menu_content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Automações SPED", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("Selecione uma das ferramentas abaixo para iniciar.", color=ft.Colors.GREY_600),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row(
                    wrap=True,
                    spacing=20,
                    run_spacing=20,
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        self.create_automation_card(
                            "SPED Contribuições",
                            ft.Icons.DESCRIPTION,
                            "Leitura e geração de planilhas de contribuições.",
                            self.open_sped_contribuicoes
                        ),
                        self.create_automation_card(
                            "Filtro por Data",
                            ft.Icons.DATE_RANGE,
                            "Filtrar arquivos SPED por intervalo de datas.",
                            self.placeholder_click("Filtro por Data")
                        ),
                        self.create_automation_card(
                            "Extrator de Chaves",
                            ft.Icons.VPN_KEY,
                            "Extrair chaves de acesso dos arquivos.",
                            self.placeholder_click("Extrator de Chaves")
                        ),
                    ]
                )
            ]
        )
        self.tab_contents["Menu"] = menu_content

    def create_automation_card(self, title, icon, description, on_click):
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

    def render_tabs(self):
        self.tabs_row.controls = []
        for label in self.open_tabs:
            is_active = (label == self.active_tab_label)
            self.tabs_row.controls.append(
                self.create_tab_button(label, is_active)
            )
        try:
            self.tabs_row.update()
        except Exception:
            pass

    def create_tab_button(self, label, is_active):
        color = ft.Colors.PRIMARY if is_active else ft.Colors.BLACK
        border_width = 2 if is_active else 0
        bg_color = ft.Colors.BLUE_50 if is_active else ft.Colors.TRANSPARENT

        icon = ft.Icons.MENU if label == "Menu" else ft.Icons.DESCRIPTION

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=bg_color,
            border=ft.border.only(bottom=ft.BorderSide(border_width, color)),
            on_click=lambda e: self.switch_tab(label),
            ink=True,
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=16, color=color),
                    ft.Text(label, color=color, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
        )

    def switch_tab(self, label):
        if label != self.active_tab_label:
            self.active_tab_label = label
            self.render_tabs()
            self.set_content(label)

    def set_content(self, label):
        if label in self.tab_contents:
            self.content_area.content = self.tab_contents[label]
            try:
                self.content_area.update()
            except Exception:
                pass

    def placeholder_click(self, feature_name):
        def handler(e):
            self.page_instance.snack_bar = ft.SnackBar(content=ft.Text(f"Abrindo: {feature_name}"))
            self.page_instance.snack_bar.open = True
            self.page_instance.update()
        return handler

    def open_sped_contribuicoes(self, e):
        target_label = "SPED Contribuições"

        if target_label not in self.open_tabs:
            self.open_tabs.append(target_label)
            # Create content
            self.tab_contents[target_label] = self.create_sped_contribuicoes_content()

        self.switch_tab(target_label)

    def create_sped_contribuicoes_content(self):
        return ft.Column(
            controls=[
                ft.Text("SPED Contribuições", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Enviar Arquivos",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda _: print("Enviar Arquivos clicked")
                        ),
                        ft.ElevatedButton(
                            "Gerar Relatório",
                            icon=ft.Icons.ASSESSMENT,
                            on_click=lambda _: print("Gerar Relatório clicked")
                        )
                    ]
                ),
                ft.Container(
                    margin=ft.margin.only(top=20),
                    content=ft.Text("Área de logs ou status aparecerá aqui...", color=ft.Colors.GREY)
                )
            ]
        )
