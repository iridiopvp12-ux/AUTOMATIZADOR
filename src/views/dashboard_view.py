import flet as ft
from src.utils.database import get_total_users
import os
import datetime
import glob

class DashboardView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

        # Container para estatísticas (Cards)
        self.stats_row = ft.Row(wrap=True, spacing=20)
        
        # Container para Atividades Recentes (Lista)
        self.activity_column = ft.Column(spacing=10)

        # Gráfico de Sessões
        self.chart = ft.BarChart(
            bar_groups=[],
            border=ft.border.all(1, ft.Colors.TRANSPARENT),
            left_axis=ft.ChartAxis(
                labels_size=40, title=ft.Text("Sessões"), title_size=20
            ),
            bottom_axis=ft.ChartAxis(
                labels=[],
                labels_size=40,
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.Colors.GREY_300, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_800),
            max_y=10,
            interactive=True,
            expand=True,
        )

        self.controls = [
            ft.Row([
                ft.Text("Dashboard", size=30, weight="bold"),
                ft.IconButton(ft.Icons.REFRESH, on_click=self.refresh_data, tooltip="Atualizar Dados")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            
            # Área de Cards
            ft.Container(content=self.stats_row, padding=ft.padding.only(bottom=20)),
            
            ft.Row([
                # Área de Logs Recentes
                ft.Container(
                    content=ft.Column([
                        ft.Text("Atividades Recentes", size=20, weight="bold"),
                        self.activity_column
                    ], scroll=ft.ScrollMode.AUTO),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    expand=1,
                    height=400
                ),
                # Área do Gráfico
                ft.Container(
                    content=ft.Column([
                        ft.Text("Sessões (Últimos 7 dias)", size=20, weight="bold"),
                        self.chart
                    ]),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    expand=1,
                    height=400
                )
            ], spacing=20)
        ]

    def did_mount(self):
        self.refresh_data(None)

    def refresh_data(self, e):
        """Atualiza todos os dados da tela"""
        # 1. Carregar Estatísticas
        total_users = get_total_users()
        sessions_today = self.count_sessions_today()
        
        # Recria os cards
        self.stats_row.controls = [
            self.build_stat_card("Usuários Cadastrados", str(total_users), ft.Icons.PEOPLE, "blue"),
            self.build_stat_card("Sessões Hoje", str(sessions_today), ft.Icons.ACCESS_TIME, "orange"),
            # Simulação de status do banco de dados
            self.build_stat_card("Banco de Dados", "Conectado", ft.Icons.STORAGE, "green"),
        ]
        
        # 2. Carregar Logs Recentes
        self.load_recent_activity()
        
        # 3. Atualizar Gráfico
        self.update_chart_data()

        self.update()

    def update_chart_data(self):
        data = self.get_last_7_days_sessions()

        self.chart.bar_groups = []
        labels = []
        max_val = 0

        for i, (day_label, count) in enumerate(data):
            self.chart.bar_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=count,
                            width=20,
                            color=ft.Colors.BLUE,
                            tooltip=f"{day_label}: {count} sessões",
                            border_radius=ft.border_radius.vertical(top=5),
                        )
                    ],
                )
            )
            labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(day_label, size=10)))
            if count > max_val: max_val = count

        self.chart.bottom_axis.labels = labels
        self.chart.max_y = max_val + 2 if max_val > 0 else 5
        self.chart.update()

    def get_last_7_days_sessions(self):
        """Retorna lista de tuplas [(Data, Count)] dos últimos 7 dias"""
        log_dir = "logs"
        today = datetime.datetime.now()
        data = []

        # Gera lista dos últimos 7 dias
        for i in range(6, -1, -1):
            date = today - datetime.timedelta(days=i)
            date_str = date.strftime("%Y%m%d")
            label = date.strftime("%d/%m")

            count = 0
            if os.path.exists(log_dir):
                files = glob.glob(os.path.join(log_dir, f"session_*{date_str}.txt"))
                count = len(files)

            data.append((label, count))

        return data

    def count_sessions_today(self):
        """Conta quantos arquivos de log foram criados/modificados hoje"""
        log_dir = "logs"
        if not os.path.exists(log_dir): return 0

        today_str = datetime.datetime.now().strftime("%Y%m%d")
        count = 0
        try:
            # Lista todos os arquivos .txt na pasta logs
            files = glob.glob(os.path.join(log_dir, "session_*.txt"))
            for f in files:
                # Verifica se o nome do arquivo contém a data de hoje
                if today_str in f:
                    count += 1
        except Exception as e:
            print(f"Erro ao contar sessões: {e}")
        return count

    def load_recent_activity(self):
        """Lê as últimas linhas dos 5 arquivos de log mais recentes"""
        self.activity_column.controls.clear()
        log_dir = "logs"
        
        if not os.path.exists(log_dir):
            self.activity_column.controls.append(ft.Text("Nenhum log encontrado."))
            return

        try:
            # Pega todos os logs e ordena pelo tempo de modificação (mais recente primeiro)
            list_of_files = glob.glob(os.path.join(log_dir, "*.txt"))
            list_of_files.sort(key=os.path.getmtime, reverse=True)
            
            # Pega os top 5 arquivos mais recentes
            recent_files = list_of_files[:5]
            
            for file_path in recent_files:
                filename = os.path.basename(file_path)
                # Tenta extrair usuário do nome do arquivo (session_USUARIO_data.txt)
                try:
                    parts = filename.split('_')
                    user = parts[1] if len(parts) > 1 else "Desconhecido"
                except:
                    user = "Sistema"

                # Lê a última linha não vazia do arquivo
                last_action = "Iniciou sessão"
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        # Pega a última linha que não seja apenas quebra de linha
                        for line in reversed(lines):
                            if line.strip() and not line.startswith("Session started") and not line.startswith("-"):
                                last_action = line.strip()
                                break
                
                # Adiciona à lista visual
                self.activity_column.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.GREY),
                        title=ft.Text(f"Usuário: {user}"),
                        subtitle=ft.Text(last_action, size=12, color=ft.Colors.GREY_700),
                        dense=True
                    )
                )
                self.activity_column.controls.append(ft.Divider(height=1, thickness=0.5))

        except Exception as e:
            self.activity_column.controls.append(ft.Text(f"Erro ao ler logs: {e}", color="red"))

    def build_stat_card(self, title, value, icon, color="blue"):
        return ft.Card(
            elevation=4,
            content=ft.Container(
                width=220,
                padding=15,
                border_radius=10,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, size=30, color=color),
                        ft.Text(title, size=14, color="grey", weight="bold")
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Container(height=10),
                    ft.Text(value, size=28, weight="bold", color=ft.Colors.BLACK87),
                ])
            )
        )