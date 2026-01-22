import flet as ft
from src.views.login_view import LoginView
from src.views.dashboard_view import DashboardView
from src.views.admin_view import AdminView
from src.views.sped_view import SpedView
from src.views.settings_view import SettingsView
from src.utils.database import initialize_db
from src.utils.logger import log_action

def main(page: ft.Page):
    # App configuration
    page.title = "Sistema Contabilidade"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0

    # Initialize DB (creates admin if needed)
    initialize_db()

    # Shared Services
    # file_picker moved to SpedView

    # State variables
    current_user = None

    def logout(e):
        nonlocal current_user
        log_action(f"User logged out: {current_user['username']}")
        current_user = None
        page.clean()
        page.add(LoginView(page, on_login_success))
        page.update()

    def get_destination(icon, label, selected_icon=None):
        return ft.NavigationRailDestination(
            icon=icon,
            selected_icon=selected_icon,
            label=label
        )

    def on_nav_change(e):
        index = e.control.selected_index
        # destinations are rebuilt based on permissions, so index maps 1:1 to content_map keys
        # We need to map index back to the specific view

        # Get the label of the selected destination
        selected_label = rail.destinations[index].label

        # Map label to content
        if selected_label == "Dashboard":
            page_content.content = DashboardView()
        elif selected_label == "Admin":
            page_content.content = AdminView(page)
        elif selected_label == "SPED":
            page_content.content = SpedView(page)
        elif selected_label == "Configurações":
            page_content.content = SettingsView(page)

        page_content.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        # extended=True,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[],
        on_change=on_nav_change
    )

    page_content = ft.Container(expand=True, padding=20)

    def on_login_success(user):
        nonlocal current_user
        current_user = user

        # Build Navigation based on permissions
        dests = []

        # Always show Dashboard if permitted or Admin
        permissions = user.get('permissions', '').split(',')
        is_admin = user.get('is_admin', False)

        # Helper to check permission
        def has_perm(p):
            return is_admin or p in permissions or "all" in permissions

        # 1. Dashboard
        if has_perm("dashboard"):
            dests.append(get_destination(ft.Icons.DASHBOARD_OUTLINED, "Dashboard", ft.Icons.DASHBOARD))

        # 2. Admin (Only is_admin)
        if is_admin:
            dests.append(get_destination(ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, "Admin", ft.Icons.ADMIN_PANEL_SETTINGS))

        # 3. SPED
        if has_perm("sped"):
            dests.append(get_destination(ft.Icons.DESCRIPTION_OUTLINED, "SPED", ft.Icons.DESCRIPTION))

        # 4. Settings
        if has_perm("settings"):
            dests.append(get_destination(ft.Icons.SETTINGS_OUTLINED, "Configurações", ft.Icons.SETTINGS))

        rail.destinations = dests
        if dests:
            rail.selected_index = 0 # Select first item

        # Logout button at bottom of rail (simulated via footer or a separate button in rail?)
        # Flet NavigationRail has trailing, but it's typically for action button.
        # We'll put logout in trailing or leading.

        rail.trailing = ft.IconButton(ft.Icons.LOGOUT, on_click=logout, tooltip="Sair")

        # Initial view
        if dests:
            first_label = dests[0].label
            if first_label == "Dashboard":
                page_content.content = DashboardView()
            elif first_label == "Admin":
                page_content.content = AdminView(page)
            elif first_label == "SPED":
                page_content.content = SpedView(page)
            elif first_label == "Configurações":
                page_content.content = SettingsView(page)
        else:
            page_content.content = ft.Text("Sem permissões de acesso.")

        page.clean()
        page.add(
            ft.Row(
                [
                    rail,
                    ft.VerticalDivider(width=1),
                    page_content
                ],
                expand=True
            )
        )
        page.update()

    # Start with Login View
    page.add(LoginView(page, on_login_success))

if __name__ == "__main__":
    ft.app(main)
