import flet as ft

class SettingPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/setting")
        self.page = page

        # Mengambil kredensial dari session (default: admin / admin)
        current_user = self.page.session.get("admin_username") or "admin"
        current_pass = self.page.session.get("admin_password") or "admin"

        self.txt_username = ft.TextField(
            label="Username Admin Baru",
            value=current_user,
            dense=True,
            width=350
        )
        self.txt_password = ft.TextField(
            label="Password Admin Baru",
            value=current_pass,
            password=True,
            can_reveal_password=True,
            dense=True,
            width=350
        )
        self.lbl_status = ft.Text("", size=12, color=ft.Colors.GREEN)

        self.controls = [
            ft.AppBar(
                title=ft.Text("Pengaturan Sistem Nara Studio"), 
                bgcolor="#e5e9f0", 
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/dashboard"))
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Pengaturan Akun Admin", size=18, weight="bold"),
                    ft.Divider(),
                    self.txt_username,
                    self.txt_password,
                    ft.ElevatedButton(
                        "Simpan Perubahan Kredensial", 
                        icon=ft.Icons.SAVE,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                        on_click=self.simpan_kredensial
                    ),
                    self.lbl_status,
                    
                    ft.Container(height=20),
                    ft.Text("Konfigurasi Akun & Sinkronisasi Data", size=18, weight="bold"),
                    ft.Divider(),
                    ft.TextField(label="Akun Google Terhubung", value="Belum Terhubung", read_only=True, width=350),
                    ft.ElevatedButton(
                        "Hubungkan Akun Google", 
                        icon=ft.Icons.ACCOUNT_CIRCLE,
                        on_click=self.hubungkan_google
                    )
                ], spacing=10),
                padding=20,
                expand=True
            )
        ]

    def simpan_kredensial(self, e):
        new_user = self.txt_username.value.strip()
        new_pass = self.txt_password.value.strip()

        if not new_user or not new_pass:
            self.lbl_status.color = ft.Colors.RED
            self.lbl_status.value = "Username dan password tidak boleh kosong!"
        else:
            self.page.session.set("admin_username", new_user)
            self.page.session.set("admin_password", new_pass)
            self.lbl_status.color = ft.Colors.GREEN
            self.lbl_status.value = "Kredensial admin berhasil diperbarui!"
        
        self.page.update()

    def hubungkan_google(self, e):
        # Membuka halaman login Google di window/tab baru
        self.page.launch_url("https://accounts.google.com")