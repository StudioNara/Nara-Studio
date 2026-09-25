import flet as ft
from modul_login import LoginPage
from modul_dashboard import DashboardPage
from modul_boardgame import BoardGamePage
from modul_ilustrasi import IlustrasiPage
from modul_setting import SettingPage
from utils import load_data

def main(page: ft.Page):
    page.title = "Nara Studio Developer Tracker"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # Kategori responsif web (opsional: matikan fixed window agar luwes di HP/iOS)
    page.padding = 0

    # Inisialisasi State Global
    page.session.set("db", load_data())
    page.session.set("user_role", None)
    page.session.set("active_project_index", None)

    def route_change(e):
        page.views.clear()
        user_role = page.session.get("user_role")

        if page.route in ["/login", "/"]:
            page.views.append(LoginPage(page))
        elif page.route == "/dashboard":
            if not user_role:
                page.go("/login")
                return
            page.views.append(DashboardPage(page))
        elif page.route == "/boardgame":
            if not user_role:
                page.go("/login")
                return
            page.views.append(BoardGamePage(page))
        elif page.route == "/ilustrasi":
            if not user_role:
                page.go("/login")
                return
            page.views.append(IlustrasiPage(page))
        elif page.route == "/setting":
            if user_role != "admin":
                page.go("/dashboard")
                return
            page.views.append(SettingPage(page))
        
        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

if __name__ == "__main__":
    # Ubah view menjadi WEB_BROWSER dan port sesuai kebutuhan
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)