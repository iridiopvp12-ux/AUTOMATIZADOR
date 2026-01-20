import flet as ft

class SpedView(ft.Column):
    def __init__(self):
        super().__init__()
        self.controls = [
            ft.Text("Automação SPED Contribuições", size=30, weight="bold"),
            ft.Divider(),
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Módulo de Leitura e Geração de Planilhas", size=18),
                    ft.Text("Este módulo permitirá ler os totalizadores e gerar a planilha final.", color="grey"),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Iniciar Leitura SPED",
                        icon=ft.icons.UPLOAD_FILE,
                        on_click=lambda e: print("Feature not implemented yet")
                    )
                ])
            )
        ]
