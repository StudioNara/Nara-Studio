import flet as ft

class DashboardPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/dashboard")
        self.page = page

        # Mengambil role dari session secara aman (tanpa argumen ke-2)
        raw_role = self.page.session.get("user_role")
        
        # Normalisasi ke lowercase dan penanganan default "guest"
        if raw_role:
            user_role = str(raw_role).lower()
        else:
            user_role = "guest"

        def go_page(route_name):
            self.page.go(route_name)

        # Kartu Navigasi Utama
        cards = [
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon("sports_esports", size=40, color="white"),
                            ft.Text("BOARD GAME", weight="bold", color="white")
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    bgcolor="#e74c3c",
                    width=180,
                    height=150,
                    padding=20,
                    on_click=lambda _: go_page("/boardgame")
                )
            ),
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon("brush", size=40, color="white"),
                            ft.Text("ILUSTRASI", weight="bold", color="white")
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    bgcolor="#3498db",
                    width=180,
                    height=150,
                    padding=20,
                    on_click=lambda _: go_page("/ilustrasi")
                )
            ),
        ]

        # Fitur/Menu Setting hanya ditampilkan untuk Role Admin
        if user_role == "admin":
            cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon("settings", size=40, color="#2c3e50"),
                                ft.Text("SETTING", weight="bold", color="#2c3e50")
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        bgcolor="#ffffff",
                        width=180,
                        height=150,
                        padding=20,
                        on_click=lambda _: go_page("/setting")
                    )
                )
            )

        role_badge_color = "#27ae60" if user_role == "admin" else "#7f8c8d"

        self.controls = [
            ft.AppBar(
                title=ft.Row([
                    ft.Text("Nara Studio - Dashboard"),
                    ft.Container(
                        content=ft.Text(f"Role: {user_role.upper()}", size=11, color="white", weight="bold"),
                        bgcolor=role_badge_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=4
                    )
                ], spacing=10),
                bgcolor="#e5e9f0", 
                actions=[
                    ft.IconButton("logout", tooltip="Keluar", on_click=lambda _: self.page.go("/login"))
                ]
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("PILIH MODUL UTAMA", size=22, weight="bold", color="#2c3e50"),
                        ft.Divider(height=20, color="transparent"),
                        ft.Row(cards, alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                expand=True,
                alignment=ft.alignment.center
            )
        ]