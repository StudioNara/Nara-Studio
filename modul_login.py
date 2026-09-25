import flet as ft

class LoginPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/login")
        self.page = page

        # Inisialisasi default kredensial jika belum ada di session
        if not self.page.session.get("admin_username"):
            self.page.session.set("admin_username", "admin")
        if not self.page.session.get("admin_password"):
            self.page.session.set("admin_password", "admin")

        self.txt_username = ft.TextField(
            label="Username Admin", 
            width=300, 
            dense=True,
            text_size=13
        )
        self.txt_password = ft.TextField(
            label="Password Admin", 
            password=True, 
            can_reveal_password=True, 
            width=300, 
            dense=True,
            text_size=13
        )
        self.lbl_error = ft.Text("", color="red", size=12)

        # Dialog Reset Password
        self.txt_tanggal_reset = ft.TextField(
            label="Masukkan Tanggal", 
            dense=True
        )
        self.lbl_reset_error = ft.Text("", color="red", size=12)

        self.reset_dialog = ft.AlertDialog(
            title=ft.Text("Reset Password Admin"),
            content=ft.Container(
                width=350,
                content=ft.Column(
                    [
                        ft.Text("Verifikasi keamanan untuk mereset akun admin ke default:"),
                        self.txt_tanggal_reset,
                        self.lbl_reset_error
                    ],
                    tight=True,
                    spacing=10
                )
            ),
            actions=[
                ft.TextButton("Batal", on_click=lambda _: self.page.close(self.reset_dialog)),
                ft.ElevatedButton("Reset Kredensial", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, on_click=self.verifikasi_reset)
            ]
        )

        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("NARA STUDIO", size=40, weight="bold", color="#2c3e50"),
                                                
                        ft.Divider(height=20, color="transparent"),
                        
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Login", weight="bold", size=14, color="#1e293b"),
                                    self.txt_username,
                                    self.txt_password,
                                    self.lbl_error,
                                    ft.ElevatedButton(
                                        "Masuk", 
                                        width=300, 
                                        bgcolor="#3498db", 
                                        color="white",
                                        on_click=self.login_admin
                                    ),
                                    ft.TextButton(
                                        "Lupa Password?", 
                                        on_click=self.open_reset_dialog
                                    )
                                ],
                                spacing=8,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            bgcolor="#f8fafc",
                            padding=15,
                            border_radius=8,
                            border=ft.border.all(1, "#e2e8f0")
                        ),

                        ft.OutlinedButton(
                            "Masuk sebagai Guest", 
                            width=300,
                            icon=ft.Icons.VISIBILITY,
                            on_click=self.login_guest
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        ]

    def login_admin(self, e):
        username_input = (self.txt_username.value or "").strip()
        password_input = (self.txt_password.value or "").strip()

        valid_user = self.page.session.get("admin_username") or "admin"
        valid_pass = self.page.session.get("admin_password") or "admin"

        if username_input == valid_user and password_input == valid_pass:
            self.page.session.set("user_role", "admin")
            self.page.go("/dashboard")
        else:
            self.lbl_error.value = "Username atau password admin salah!"
            self.page.update()

    def login_guest(self, e):
        self.page.session.set("user_role", "guest")
        self.page.go("/dashboard")

    def open_reset_dialog(self, e):
        self.txt_tanggal_reset.value = ""
        self.lbl_reset_error.value = ""
        self.page.open(self.reset_dialog)

    def verifikasi_reset(self, e):
        input_tanggal = (self.txt_tanggal_reset.value or "").strip()

        if input_tanggal.lower() == "16 november 1964":
            self.page.session.set("admin_username", "admin")
            self.page.session.set("admin_password", "admin")
            
            self.page.close(self.reset_dialog)
            self.lbl_error.color = ft.Colors.GREEN
            self.lbl_error.value = "Kredensial berhasil di-reset ke default! (admin / admin)"
            self.page.update()
        else:
            self.lbl_reset_error.value = "Tanggal yang dimasukkan salah!"
            self.page.update()