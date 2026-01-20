import flet as ft
from src.utils.database import get_total_users
import os
import datetime

class DashboardView(ft.Column):
    def __init__(self):
        super().__init__()

        # Calculate stats
        total_users = get_total_users()
        sessions_today = self.count_sessions_today()

        self.controls = [
            ft.Text("Dashboard", size=30, weight="bold"),
            ft.Divider(),
            ft.Row([
                self.build_stat_card("Usuários Cadastrados", str(total_users), ft.Icons.PEOPLE),
                self.build_stat_card("Sessões Hoje", str(sessions_today), ft.Icons.ACCESS_TIME, "orange"),
                self.build_stat_card("Status do Sistema", "Online", ft.Icons.CHECK_CIRCLE, "green"),
            ], wrap=True, spacing=20)
        ]

    def count_sessions_today(self):
        log_dir = "logs"
        if not os.path.exists(log_dir):
            return 0

        today_str = datetime.datetime.now().strftime("%Y%m%d")
        count = 0
        try:
            for filename in os.listdir(log_dir):
                # Format: session_{username}_{timestamp}.txt
                # timestamp: YYYYMMDD_HHMMSS
                if filename.startswith("session_") and filename.endswith(".txt"):
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        # The timestamp part might be split further if username has underscores,
                        # but we know timestamp is at the end: ..._YYYYMMDD_HHMMSS.txt
                        # Let's extract date from filename robustly
                        # session_username_20230101_120000.txt
                        # Date part is likely index -2 if split by _
                        date_part = parts[-2]
                        if date_part == today_str:
                            count += 1
        except Exception as e:
            print(f"Error counting sessions: {e}")
            return 0

        return count

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
