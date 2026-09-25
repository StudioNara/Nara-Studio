import flet as ft
from utils import SOP_PHASES_DETAIL, save_data
from datetime import datetime, timedelta
import os
import shutil
import base64

def get_image_base64(path):
    """Fungsi pembantu untuk mengubah file gambar lokal menjadi format Base64"""
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
    return None

class BoardGamePage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/boardgame")
        self.page = page
        
        db = self.page.session.get("db")
        self.projects = db.get("projects", []) if db else []
        active_idx = self.page.session.get("active_project_index")
        self.active_project_index = active_idx if active_idx is not None and len(self.projects) > 0 else (0 if self.projects else None)

        self.search_query = ""
        self.status_filter = "All Status"
        self.sort_field = "Judul"
        self.sort_asc = True
        
        self.asset_sort_field = "Tanggal"
        self.asset_sort_asc = False

        self.active_menu = "overview"
        
        self.is_delete_mode = False
        self.selected_assets_to_delete = set()
        self.preview_index = 0

        self.file_picker = ft.FilePicker(on_result=self.on_files_picked)
        self.page.overlay.append(self.file_picker)

        self.date_picker = ft.DatePicker(on_change=self.handle_date_selected)
        self.page.overlay.append(self.date_picker)

        self.playtest_date_picker = ft.DatePicker(on_change=self.handle_playtest_date_selected)
        self.page.overlay.append(self.playtest_date_picker)
        self.temp_playtest_date_field = None

        self.page.on_keyboard_event = self.handle_keyboard

        self.content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=15)
        self.build_ui()

    def build_ui(self):
        self.project_list_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=5)
        raw_role = self.page.session.get("user_role")
        user_role = str(raw_role).lower() if raw_role else "guest"
        is_admin = (user_role == "admin")
        
        filter_dropdown = ft.Dropdown(
            label="Filter Status",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            value="All Status",
            options=[
                ft.dropdown.Option("All Status"),
                ft.dropdown.Option("Active"),
                ft.dropdown.Option("Inactive"),
                ft.dropdown.Option("Pause"),
                ft.dropdown.Option("Terminate"),
                ft.dropdown.Option("End")
            ],
            text_size=12,
            dense=True,
            on_change=self.on_filter_change,
            expand=True
        )

        self.sort_dropdown = ft.Dropdown(
            label="Sort By",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            options=[
                ft.dropdown.Option("Judul"),
                ft.dropdown.Option("Sisa Hari"),
                ft.dropdown.Option("Jumlah Pemain"),
                ft.dropdown.Option("Durasi")
            ],
            text_size=12,
            dense=True,
            on_change=self.on_sort_change,
            expand=True
        )

        search_field = ft.TextField(
            hint_text="Cari proyek...",
            text_size=12,
            dense=True,
            on_change=self.on_search_change,
            expand=True
        )

        logo_back_btn = ft.IconButton(
            icon="home", 
            icon_size=20, 
            icon_color="#2c3e50",
            on_click=lambda _: self.page.go("/dashboard"), 
            tooltip="Dashboard"
        )

        header_actions = [logo_back_btn]
        if is_admin:
            header_actions.append(
                ft.IconButton("create_new_folder", icon_size=18, bgcolor="#2ecc71", icon_color="white", tooltip="Buat Proyek Baru", on_click=self.modal_tambah_proyek)
            )

        role_indicator = ft.Container(
            content=ft.Text(f"Akses: {user_role.upper()}", size=10, color="white", weight="bold"),
            bgcolor="#27ae60" if is_admin else "#7f8c8d",
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=4
        )

        sidebar_content = ft.Column([
            ft.Row(header_actions, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            role_indicator,
            ft.Divider(height=10),
            
            ft.Row([
                ft.Icon("filter_list", size=18, color="#7f8c8d"),
                filter_dropdown
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=8),
            
            ft.Row([
                ft.Icon("sort", size=18, color="#7f8c8d"),
                self.sort_dropdown
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=8),
            
            ft.Row([
                ft.Icon("search", size=18, color="#7f8c8d"),
                search_field
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=8),
            
            ft.Divider(height=10),
            ft.Text("Daftar Proyek", size=11, weight="bold", color="#1e293b"),
            self.project_list_col
        ], expand=True, spacing=8)

        sidebar = ft.Container(
            content=sidebar_content,
            width=280, 
            bgcolor="#f8fafc", 
            padding=12
        )

        menu_rail = ft.Container(
            content=ft.Column([
                ft.Text("Menu", size=10, weight="bold", color="#2c3e50"),
                ft.Divider(height=5),
                ft.IconButton("list", icon_size=18, tooltip="Overview", on_click=lambda _: self.switch_menu("overview")),
                ft.IconButton("checklist", icon_size=18, tooltip="Checklist", on_click=lambda _: self.switch_menu("checklist")),
                ft.IconButton("image", icon_size=18, tooltip="Assets", on_click=lambda _: self.switch_menu("assets")),
                ft.IconButton("description", icon_size=18, tooltip="Playtest Log", on_click=lambda _: self.switch_menu("playtest")),
                ft.IconButton("lightbulb", icon_size=18, tooltip="Idea Board", on_click=lambda _: self.switch_menu("idea")),
                ft.IconButton("info", icon_size=18, tooltip="Informasi Proyek", on_click=lambda _: self.switch_menu("about")),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=50, 
            bgcolor="#edf2f7", 
            padding=5
        )

        self.refresh_project_list()
        self.render_main_content()

        self.controls = [
            ft.Row([
                sidebar,
                menu_rail,
                ft.VerticalDivider(width=1),
                self.content_area
            ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)
        ]

    def switch_menu(self, menu_name):
        self.active_menu = menu_name
        self.is_delete_mode = False
        self.selected_assets_to_delete.clear()
        self.render_main_content()

    def handle_keyboard(self, e: ft.KeyboardEvent):
        if hasattr(self, "current_preview_dialog") and self.current_preview_dialog and self.current_preview_dialog.open:
            if self.active_project_index is not None and 0 <= self.active_project_index < len(self.projects):
                proj = self.projects[self.active_project_index]
                media_list = proj.get("media", [])
                if len(media_list) > 1:
                    if e.key == "Arrow Left":
                        self.preview_index = (self.preview_index - 1) % len(media_list)
                        self.refresh_preview_content()
                    elif e.key == "Arrow Right":
                        self.preview_index = (self.preview_index + 1) % len(media_list)
                        self.refresh_preview_content()

    def refresh_project_list(self):
        self.project_list_col.controls.clear()
        
        filtered = []
        for idx, proj in enumerate(self.projects):
            nama = proj.get("nama", "").lower()
            status = proj.get("status", "Active")
            
            if self.search_query and self.search_query not in nama:
                continue
            if self.status_filter != "All Status" and status != self.status_filter:
                continue
            filtered.append((idx, proj))

        if self.sort_field == "Judul":
            filtered.sort(key=lambda x: x[1].get("nama", "").lower(), reverse=not self.sort_asc)
        elif self.sort_field == "Sisa Hari":
            def get_sisa_hari(item):
                proj = item[1]
                deadline = proj.get("deadline", "-")
                if deadline and deadline != "-":
                    try:
                        dl_date = datetime.strptime(deadline, "%Y-%m-%d")
                        return (dl_date - datetime.now()).days
                    except:
                        pass
                return 999999
            filtered.sort(key=get_sisa_hari, reverse=not self.sort_asc)
        elif self.sort_field == "Jumlah Pemain":
            def get_players(item):
                proj = item[1]
                try:
                    return int(proj.get("min_player", 2))
                except:
                    return 2
            filtered.sort(key=get_players, reverse=not self.sort_asc)
        elif self.sort_field == "Durasi":
            def get_duration(item):
                proj = item[1]
                try:
                    return int(proj.get("min_duration", 10))
                except:
                    return 10
            filtered.sort(key=get_duration, reverse=not self.sort_asc)

        for idx, proj in filtered:
            nama = proj.get("nama", f"Proyek #{idx+1}")
            is_selected = (self.active_project_index == idx)
            icon_name = "folder_open" if is_selected else "folder"
            
            btn = ft.Container(
                content=ft.Row([
                    ft.Icon(icon_name, size=16, color="white" if is_selected else "#7f8c8d"),
                    ft.Text(nama, size=12, color="white" if is_selected else "#2c3e50", weight="bold" if is_selected else "normal", no_wrap=True)
                ], spacing=8),
                bgcolor="#3498db" if is_selected else "transparent",
                padding=8,
                border_radius=5,
                ink=True,
                on_click=lambda e, i=idx: self.select_project(i)
            )
            self.project_list_col.controls.append(btn)
        self.page.update()

    def select_project(self, idx):
        self.active_project_index = idx
        self.page.session.set("active_project_index", idx)
        self.active_menu = "checklist"
        self.is_delete_mode = False
        self.selected_assets_to_delete.clear()
        self.refresh_project_list()
        self.render_main_content()

    def on_search_change(self, e):
        self.search_query = e.control.value.lower()
        self.refresh_project_list()

    def on_filter_change(self, e):
        self.status_filter = e.control.value
        self.refresh_project_list()

    def on_sort_change(self, e):
        val = e.control.value
        if not val:
            return
        if val == self.sort_field:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_field = val
            self.sort_asc = True
        e.control.value = None
        e.control.label = f"Sort: {self.sort_field} ({'↑' if self.sort_asc else '↓'})"
        self.refresh_project_list()

    def render_main_content(self):
        self.content_area.controls.clear()
        if self.active_menu == "overview":
            self.render_overview_content()
        elif self.active_menu == "assets":
            self.render_assets_content()
        elif self.active_menu == "playtest":
            self.render_playtest_content()
        elif self.active_menu == "idea":
            self.render_idea_board_content()
        elif self.active_menu == "about":
            self.render_about_content()
        else:
            self.render_project_content()

    def modal_tambah_proyek(self, e):
        if self.page.session.get("user_role") != "admin":
            return

        txt_nama = ft.TextField(
            label="Judul Proyek", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            text_size=12, 
            dense=True
        )
        txt_min_player = ft.TextField(
            label="Min Pemain", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value="1", 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_max_player = ft.TextField(
            label="Max Pemain", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value="4", 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_min_duration = ft.TextField(
            label="Min Durasi", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value="30", 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_max_duration = ft.TextField(
            label="Max Durasi", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value="60", 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_genre = ft.TextField(
            label="Genre / Tema", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            text_size=12, 
            dense=True
        )
        
        dd_status = ft.Dropdown(
            label="Status Proyek",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            value="Active",
            options=[
                ft.dropdown.Option("Active"),
                ft.dropdown.Option("Inactive"),
                ft.dropdown.Option("Pause"),
                ft.dropdown.Option("Terminate"),
                ft.dropdown.Option("End")
            ],
            text_size=12,
            dense=True
        )

        component_options = [
            "Bag", "Board", "Card", "Dial", "Dice", "Dry-erase Board/Card", 
            "Envelope", "Grid Mat", "Marker", "Meeple", "Miniature", 
            "Plastic Stand", "Player Screen", "Resource", "Spinner", 
            "Standee", "Stickers", "Tile", "Timer", "Token", "Tracker", 
            "Wheel", "Wooden Pieces"
        ]

        component_rows = []
        components_container = ft.Column([], spacing=8)
        
        dlg_tambah = ft.Ref[ft.AlertDialog]()

        def rebuild_component_ui():
            components_container.controls.clear()
            for item in component_rows:
                if item is not None:
                    components_container.controls.append(item["row"])
            if dlg_tambah.current:
                dlg_tambah.current.update()

        def tambah_baris_komponen(e=None):
            dropdown_komponen = ft.Dropdown(
                label="Komponen",
                label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
                options=[ft.dropdown.Option(opt) for opt in component_options],
                text_size=12,
                dense=True,
                expand=True
            )
            txt_jumlah = ft.TextField(
                label="Jumlah",
                label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
                value="1",
                text_size=12,
                dense=True,
                width=80
            )
            
            row_container = ft.Row(spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            item_data = {
                "dropdown": dropdown_komponen,
                "jumlah": txt_jumlah,
                "row": row_container
            }
            
            def hapus_baris(e):
                if item_data in component_rows:
                    component_rows.remove(item_data)
                rebuild_component_ui()

            btn_hapus = ft.IconButton(
                icon="close",
                icon_size=16,
                icon_color="#1e293b",
                tooltip="Hapus Baris",
                on_click=hapus_baris
            )

            row_container.controls = [
                dropdown_komponen,
                txt_jumlah,
                btn_hapus
            ]

            component_rows.append(item_data)
            rebuild_component_ui()

        tambah_baris_komponen()

        btn_tambah_komponen = ft.ElevatedButton(
            text="Tambah Komponen",
            icon="add",
            bgcolor="#f1f5f9",
            color="#2c3e50",
            on_click=tambah_baris_komponen
        )

        def simpan_proyek(e):
            nama = txt_nama.value.strip()
            if not nama:
                return
            
            components_data = []
            for item in component_rows:
                if item is not None:
                    comp_name = item["dropdown"].value
                    comp_qty = item["jumlah"].value
                    if comp_name:
                        components_data.append({
                            "komponen": comp_name,
                            "jumlah": comp_qty
                        })

            default_deadline = (datetime.now() + timedelta(weeks=8)).strftime("%Y-%m-%d")

            new_proj = {
                "nama": nama,
                "min_player": txt_min_player.value,
                "max_player": txt_max_player.value,
                "min_duration": txt_min_duration.value,
                "max_duration": txt_max_duration.value,
                "genre": txt_genre.value,
                "deadline": default_deadline,
                "status": dd_status.value,
                "summary": "",
                "components": components_data,
                "tasks": {},
                "media": [],
                "playtests": [],
                "ideas": []
            }
            
            self.projects.append(new_proj)
            db = self.page.session.get("db")
            save_data(db)
            
            if dlg_tambah.current:
                dlg_tambah.current.open = False
            self.active_project_index = len(self.projects) - 1
            self.page.session.set("active_project_index", self.active_project_index)
            self.refresh_project_list()
            self.render_main_content()

        def batal_simpan(e):
            if dlg_tambah.current:
                dlg_tambah.current.open = False
                self.page.update()

        dialog_content = ft.AlertDialog(
            ref=dlg_tambah,
            modal=True,
            title=ft.Text("Buat Proyek Board Game Baru", size=14, weight="bold", color="#1e293b"),
            content=ft.Container(
                content=ft.Column([
                    txt_nama,
                    dd_status,
                    ft.Text("Jumlah Pemain:", size=11, color="#1e293b", weight="bold"),
                    ft.Row([txt_min_player, txt_max_player], spacing=10),
                    ft.Text("Durasi Permainan (menit):", size=11, color="#1e293b", weight="bold"),
                    ft.Row([txt_min_duration, txt_max_duration], spacing=10),
                    txt_genre,
                    ft.Divider(height=10),
                    ft.Text("Komponen Proyek:", size=11, weight="bold", color="#1e293b"),
                    components_container,
                    btn_tambah_komponen
                ], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO),
                width=420,
                height=480
            ),
            actions=[
                ft.TextButton("Batal", on_click=batal_simpan),
                ft.ElevatedButton("Buat Proyek", bgcolor="#3498db", color="white", on_click=simpan_proyek)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dialog_content)
        dialog_content.open = True
        self.page.update()

    def render_overview_content(self):
        statuses = ["Active", "Inactive", "Pause", "Terminate", "End"]
        status_colors = {
            "Active": "#2EAD62",
            "Inactive": "#3B82F6",
            "Pause": "#F2B84B",
            "Terminate": "#D64545",
            "End": "#6B7280"
        }
        
        status_groups = {st: [] for st in statuses}
        for idx, proj in enumerate(self.projects):
            st = proj.get("status", "Active")
            if st not in status_groups:
                status_groups[st] = []
            
            if "tasks" not in proj: proj["tasks"] = {}
            
            total_tasks = 0
            completed_tasks = 0
            for phase in SOP_PHASES_DETAIL:
                tasks = phase.get("tasks", [])
                total_tasks += len(tasks)
                for task in tasks:
                    if proj["tasks"].get(task, False):
                        completed_tasks += 1
                        
            progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

            deadline = proj.get("deadline", "-")
            sisa_hari_val = 999999
            sisa_hari_str = "-"
            if deadline and deadline != "-":
                try:
                    dl_date = datetime.strptime(deadline, "%Y-%m-%d")
                    delta = (dl_date - datetime.now()).days
                    sisa_hari_val = delta
                    if delta >= 0:
                        sisa_hari_str = f"Sisa {delta} Hari"
                    else:
                        sisa_hari_str = f"Lewat {abs(delta)} Hari"
                except:
                    pass

            status_groups[st].append({
                "index": idx,
                "nama": proj.get("nama", "Tanpa Nama"),
                "progress": progress_pct,
                "sisa_hari_val": sisa_hari_val,
                "sisa_hari_str": sisa_hari_str
            })

        for st in statuses:
            status_groups[st].sort(key=lambda x: (x["sisa_hari_val"], -x["progress"], x["nama"].lower()))

        overview_columns = []
        for st in statuses:
            projs = status_groups[st]
            count = len(projs)
            bg_color = status_colors.get(st, "#6B7280")

            header_box = ft.Container(
                content=ft.Row([
                    ft.Text(st, weight="bold", size=14, color="white"),
                    ft.Container(
                        content=ft.Text(str(count), size=12, color=bg_color, weight="bold"),
                        bgcolor="white",
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=10
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=bg_color,
                padding=10,
                border_radius=6,
                width=220
            )

            proj_items_controls = [header_box]
            if count == 0:
                proj_items_controls.append(ft.Text("Tidak ada proyek", size=11, italic=True, color="#1e293b"))
            else:
                for p in projs:
                    item_ref = p["index"]
                    proj_items_controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(p["nama"], size=12, weight="bold", color="#2c3e50", no_wrap=True),
                                ft.Row([
                                    ft.Text(f"Progress: {p['progress']}%", size=11, color="#2EAD62", weight="bold"),
                                    ft.Text(f"• {p['sisa_hari_str']}", size=11, color="#D64545", weight="bold")
                                ], spacing=4)
                            ], spacing=2),
                            padding=ft.padding.symmetric(horizontal=4, vertical=6),
                            border_radius=4,
                            ink=True,
                            on_click=lambda e, i=item_ref: self.select_project(i)
                        )
                    )

            overview_columns.append(
                ft.Column(
                    proj_items_controls,
                    spacing=6,
                    width=220,
                    horizontal_alignment=ft.CrossAxisAlignment.START
                )
            )

        row_overview = ft.Row(overview_columns, scroll=ft.ScrollMode.AUTO, spacing=15, vertical_alignment=ft.CrossAxisAlignment.START)
        
        self.content_area.alignment = ft.MainAxisAlignment.START
        self.content_area.controls.clear()
        self.content_area.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("Overview", size=24, weight="bold", color="#2c3e50"),
                    ft.Divider(height=10),
                    row_overview
                ], spacing=15, tight=True, alignment=ft.MainAxisAlignment.START),
                padding=20,
                alignment=ft.alignment.top_left
            )
        )
        self.page.update()

    def render_about_content(self):
        is_admin = self.page.session.get("user_role") == "admin"
        self.content_area.alignment = ft.MainAxisAlignment.START
        self.content_area.controls.clear()

        if self.active_project_index is None or not self.projects or self.active_project_index >= len(self.projects):
            self.content_area.controls.append(
                ft.Container(
                    content=ft.Text("Silakan pilih atau buat proyek terlebih dahulu dari panel kiri.", color="#1e293b"),
                    padding=20
                )
            )
            self.page.update()
            return

        proj = self.projects[self.active_project_index]

        header_actions_list = [ft.Text("About", size=24, weight="bold", color="#2c3e50")]
        if is_admin:
            btn_edit = ft.IconButton(
                icon="edit",
                icon_size=18,
                icon_color="#3498db",
                tooltip="Edit Informasi Proyek",
                on_click=self.modal_edit_proyek
            )
            btn_delete = ft.IconButton(
                icon="delete",
                icon_size=18,
                icon_color="#e74c3c",
                tooltip="Hapus Proyek",
                on_click=self.modal_konfirmasi_hapus_proyek
            )
            header_actions_list.append(ft.Row([btn_edit, btn_delete], spacing=0))

        header_actions = ft.Row(header_actions_list, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        nama = proj.get("nama", "Tanpa Judul")
        status = proj.get("status", "Active")
        min_p = proj.get("min_player", "1")
        max_p = proj.get("max_player", "4")
        min_d = proj.get("min_duration", "10")
        max_d = proj.get("max_duration", "30")
        deadline = proj.get("deadline", "-")
        genre = proj.get("genre", "-")
        summary = proj.get("summary", "")
        components = proj.get("components", [])

        sisa_hari_str = "(Sisa Waktu: Tidak Diatur)"
        if deadline and deadline != "-":
            try:
                dl_date = datetime.strptime(deadline, "%Y-%m-%d")
                delta = (dl_date - datetime.now()).days
                if delta >= 0:
                    sisa_hari_str = f"(Sisa Waktu: {delta} Hari)"
                else:
                    sisa_hari_str = f"(Lewat Waktu: {abs(delta)} Hari)"
            except:
                pass

        comp_str = ", ".join([f"{c.get('jumlah', '1')}x {c.get('komponen', '')}" for c in components]) if components else "Belum ada komponen diatur."

        card_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon("extension", size=20, color="#2c3e50"),
                        ft.Text(nama, size=16, weight="bold", color="#2c3e50"),
                    ], spacing=8),
                    ft.Container(
                        content=ft.Text(f"Status Dev: {status}", size=11, weight="bold", color="white"),
                        bgcolor="#3498db",
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=4
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(height=10),
                
                ft.Row([
                    ft.Icon("group", size=16, color="#7f8c8d"),
                    ft.Text("Jumlah Pemain:", size=12, weight="bold", color="#7f8c8d"),
                    ft.Text(f"{min_p} - {max_p} Pemain", size=12, color="#2c3e50")
                ], spacing=6),

                ft.Row([
                    ft.Icon("timer", size=16, color="#7f8c8d"),
                    ft.Text("Target Durasi:", size=12, weight="bold", color="#7f8c8d"),
                    ft.Text(f"{min_d} - {max_d} Menit", size=12, color="#2c3e50")
                ], spacing=6),

                ft.Row([
                    ft.Icon("hourglass_empty", size=16, color="#7f8c8d"),
                    ft.Text("Target Deadline:", size=12, weight="bold", color="#7f8c8d"),
                    ft.Text(f"{deadline}  {sisa_hari_str}", size=12, color="#27ae60" if "Sisa" in sisa_hari_str else "#e74c3c")
                ], spacing=6),

                ft.Row([
                    ft.Icon("category", size=16, color="#7f8c8d"),
                    ft.Text("Genre / Tema:", size=12, weight="bold", color="#7f8c8d"),
                    ft.Text(f"{genre if genre else '-'}", size=12, color="#2c3e50")
                ], spacing=6),

                ft.Row([
                    ft.Icon("inventory", size=16, color="#7f8c8d"),
                    ft.Text("Komponen:", size=12, weight="bold", color="#7f8c8d"),
                    ft.Text(f"{comp_str}", size=12, color="#2c3e50")
                ], spacing=6),

                ft.Divider(height=10),

                ft.Column([
                    ft.Row([
                        ft.Icon("description", size=16, color="#7f8c8d"),
                        ft.Text("Deskripsi / Theme & Concept / Ringkasan:", size=12, weight="bold", color="#7f8c8d")
                    ], spacing=6),
                    ft.Container(
                        content=ft.Text(summary if summary else "Belum ada deskripsi singkat proyek.", size=12, italic=not summary, color="#2c3e50" if summary else "#1e293b"),
                        padding=ft.padding.only(left=22)
                    )
                ], spacing=6)

            ], spacing=10),
            bgcolor="white",
            border=ft.border.all(1, "#cbd5e1"),
            border_radius=8,
            padding=16
        )

        self.content_area.controls.append(
            ft.Container(
                content=ft.Column([
                    header_actions,
                    ft.Divider(height=5, color="transparent"),
                    card_content
                ], spacing=10, tight=True, alignment=ft.MainAxisAlignment.START),
                padding=20,
                alignment=ft.alignment.top_left
            )
        )
        self.page.update()

    def modal_edit_proyek(self, e):
        if self.page.session.get("user_role") != "admin":
            return

        proj = self.projects[self.active_project_index]

        txt_nama = ft.TextField(
            label="Judul Proyek", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value=proj.get("nama", ""), 
            text_size=12, 
            dense=True
        )
        dd_status = ft.Dropdown(
            label="Status Proyek",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            value=proj.get("status", "Active"),
            options=[
                ft.dropdown.Option("Active"),
                ft.dropdown.Option("Inactive"),
                ft.dropdown.Option("Pause"),
                ft.dropdown.Option("Terminate"),
                ft.dropdown.Option("End")
            ],
            text_size=12,
            dense=True
        )
        txt_min_player = ft.TextField(
            label="Min Pemain", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value=str(proj.get("min_player", "1")), 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_max_player = ft.TextField(
            label="Max Pemain", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value=str(proj.get("max_player", "4")), 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_min_duration = ft.TextField(
            label="Min Durasi", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value=str(proj.get("min_duration", "30")), 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_max_duration = ft.TextField(
            label="Max Durasi", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value=str(proj.get("max_duration", "60")), 
            text_size=12, 
            dense=True, 
            width=100
        )
        txt_genre = ft.TextField(
            label="Genre / Tema", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value=proj.get("genre", ""), 
            text_size=12, 
            dense=True
        )
        txt_summary = ft.TextField(
            label="Ringkasan / Deskripsi Board Game", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"), 
            value=proj.get("summary", ""), 
            multiline=True,
            min_lines=3,
            max_lines=5,
            text_size=12, 
            dense=True
        )

        component_options = [
            "Bag", "Board", "Card", "Dial", "Dice", "Dry-erase Board/Card", 
            "Envelope", "Grid Mat", "Marker", "Meeple", "Miniature", 
            "Plastic Stand", "Player Screen", "Resource", "Spinner", 
            "Standee", "Stickers", "Tile", "Timer", "Token", "Tracker", 
            "Wheel", "Wooden Pieces"
        ]

        component_rows = []
        components_container = ft.Column([], spacing=8)

        dlg_edit = ft.Ref[ft.AlertDialog]()

        def rebuild_component_ui():
            components_container.controls.clear()
            for item in component_rows:
                if item is not None:
                    components_container.controls.append(item["row"])
            if dlg_edit.current:
                dlg_edit.current.update()

        def tambah_baris_komponen(comp_val="", qty_val="1"):
            dropdown_komponen = ft.Dropdown(
                label="Komponen",
                label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
                value=comp_val if comp_val in component_options else None,
                options=[ft.dropdown.Option(opt) for opt in component_options],
                text_size=12,
                dense=True,
                expand=True
            )
            txt_jumlah = ft.TextField(
                label="Jumlah",
                label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
                value=str(qty_val),
                text_size=12,
                dense=True,
                width=80
            )
            
            row_container = ft.Row(spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            item_data = {
                "dropdown": dropdown_komponen,
                "jumlah": txt_jumlah,
                "row": row_container
            }

            def hapus_baris(e):
                if item_data in component_rows:
                    component_rows.remove(item_data)
                rebuild_component_ui()

            btn_hapus = ft.IconButton(
                icon="close",
                icon_size=16,
                icon_color="#1e293b",
                tooltip="Hapus Baris",
                on_click=hapus_baris
            )

            row_container.controls = [
                dropdown_komponen,
                txt_jumlah,
                btn_hapus
            ]

            component_rows.append(item_data)
            rebuild_component_ui()

        existing_comps = proj.get("components", [])
        if existing_comps:
            for c in existing_comps:
                tambah_baris_komponen(c.get("komponen", ""), c.get("jumlah", "1"))
        else:
            tambah_baris_komponen()

        btn_tambah_komponen = ft.ElevatedButton(
            text="Tambah Komponen",
            icon="add",
            bgcolor="#f1f5f9",
            color="#2c3e50",
            on_click=lambda _: tambah_baris_komponen()
        )

        def simpan_edit_proyek(e):
            nama = txt_nama.value.strip()
            if not nama:
                return

            components_data = []
            for item in component_rows:
                if item is not None:
                    comp_name = item["dropdown"].value
                    comp_qty = item["jumlah"].value
                    if comp_name:
                        components_data.append({
                            "komponen": comp_name,
                            "jumlah": comp_qty
                        })

            proj["nama"] = nama
            proj["status"] = dd_status.value
            proj["min_player"] = txt_min_player.value
            proj["max_player"] = txt_max_player.value
            proj["min_duration"] = txt_min_duration.value
            proj["max_duration"] = txt_max_duration.value
            proj["genre"] = txt_genre.value
            proj["summary"] = txt_summary.value
            proj["components"] = components_data

            db = self.page.session.get("db")
            save_data(db)

            if dlg_edit.current:
                dlg_edit.current.open = False
            self.refresh_project_list()
            self.render_about_content()

        def batal_edit_proyek(e):
            if dlg_edit.current:
                dlg_edit.current.open = False
                self.page.update()

        dialog_edit_content = ft.AlertDialog(
            ref=dlg_edit,
            modal=True,
            title=ft.Text("Edit Informasi Proyek Board Game", size=14, weight="bold", color="#1e293b"),
            content=ft.Container(
                content=ft.Column([
                    txt_nama,
                    dd_status,
                    ft.Text("Jumlah Pemain:", size=11, color="#1e293b", weight="bold"),
                    ft.Row([txt_min_player, txt_max_player], spacing=10),
                    ft.Text("Durasi Permainan (menit):", size=11, color="#1e293b", weight="bold"),
                    ft.Row([txt_min_duration, txt_max_duration], spacing=10),
                    txt_genre,
                    txt_summary,
                    ft.Divider(height=10),
                    ft.Text("Komponen Proyek:", size=11, weight="bold", color="#1e293b"),
                    components_container,
                    btn_tambah_komponen
                ], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO),
                width=420,
                height=480
            ),
            actions=[
                ft.TextButton("Batal", on_click=batal_edit_proyek),
                ft.ElevatedButton("Simpan Perubahan", bgcolor="#3498db", color="white", on_click=simpan_edit_proyek)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dialog_edit_content)
        dialog_edit_content.open = True
        self.page.update()

    def modal_konfirmasi_hapus_proyek(self, e):
        if self.page.session.get("user_role") != "admin":
            return

        proj = self.projects[self.active_project_index]
        nama_proyek = proj.get("nama", "proyek ini")

        def eksekusi_hapus(e):
            self.projects.pop(self.active_project_index)
            db = self.page.session.get("db")
            save_data(db)

            dlg_del.open = False
            self.active_project_index = 0 if len(self.projects) > 0 else None
            self.page.session.set("active_project_index", self.active_project_index)
            self.refresh_project_list()
            self.render_main_content()

        def batal_hapus(e):
            dlg_del.open = False
            self.page.update()

        dlg_del = ft.AlertDialog(
            modal=True,
            title=ft.Text("Konfirmasi Hapus Proyek", size=14, weight="bold", color="#1e293b"),
            content=ft.Text(f'Anda yakin akan menghapus proyek "{nama_proyek}"?', size=12, color="#1e293b"),
            actions=[
                ft.TextButton("Batal", on_click=batal_hapus),
                ft.ElevatedButton("Ya, Hapus", bgcolor="#e74c3c", color="white", on_click=eksekusi_hapus)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dlg_del)
        dlg_del.open = True
        self.page.update()

    def render_project_content(self):
        is_admin = self.page.session.get("user_role") == "admin"
        self.content_area.alignment = ft.MainAxisAlignment.START
        self.content_area.controls.clear()

        if self.active_project_index is None or not self.projects or self.active_project_index >= len(self.projects):
            self.content_area.controls.append(
                ft.Container(
                    content=ft.Text("Silakan pilih atau buat proyek terlebih dahulu dari panel kiri.", color="#1e293b"),
                    padding=20
                )
            )
            self.page.update()
            return

        proj = self.projects[self.active_project_index]
        if "tasks" not in proj:
            proj["tasks"] = {}

        total_tasks = 0
        completed_tasks = 0
        for phase in SOP_PHASES_DETAIL:
            tasks = phase.get("tasks", [])
            total_tasks += len(tasks)
            for t in tasks:
                if proj["tasks"].get(t, False):
                    completed_tasks += 1
        
        progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

        active_phase_name = "Selesai"
        for phase_idx, phase in enumerate(SOP_PHASES_DETAIL):
            tasks = phase.get("tasks", [])
            phase_done = all(proj["tasks"].get(t, False) for t in tasks)
            if not phase_done:
                p_name = phase.get("phase") or phase.get("nama") or phase.get("title") or f"Phase {phase_idx+1}"
                active_phase_name = f"Phase 0{phase_idx+1}: {p_name}" if phase_idx < 9 else f"Phase {phase_idx+1}: {p_name}"
                break

        deadline = proj.get("deadline", "-")
        sisa_hari_str = "-"
        if deadline and deadline != "-":
            try:
                dl_date = datetime.strptime(deadline, "%Y-%m-%d")
                delta = (dl_date - datetime.now()).days
                if delta >= 0:
                    sisa_hari_str = f"Sisa {delta} Hari"
                else:
                    sisa_hari_str = f"Lewat {abs(delta)} Hari"
            except:
                pass

        deadline_actions = [
            ft.Icon("flag", size=14, color="#e11d48"),
            ft.Text(f"Target Deadline: {deadline}", size=12, weight="bold", color="#e11d48"),
            ft.Text(f"•  ⏳ {sisa_hari_str}", size=12, color="#2563eb", weight="bold"),
        ]

        if is_admin:
            deadline_row = ft.Row([
                ft.Row(deadline_actions, spacing=6),
                ft.IconButton(
                    icon="notifications",
                    icon_size=18,
                    icon_color="#d97706",
                    tooltip="Atur Deadline (Kalender)",
                    on_click=lambda _: self.open_date_picker()
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        else:
            deadline_row = ft.Row(deadline_actions, spacing=6)

        top_status_card = ft.Container(
            content=ft.Column([
                ft.Row([
		ft.Text(f"Status: [{proj.get('status', 'Active')}]  |  Fase Aktif: {active_phase_name}  |  Progress: {progress_pct}%", weight="bold", size=13, color="#1e293b"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Row([
                    ft.Text(f"👥 Pemain: {proj.get('min_player', '1')}-{proj.get('max_player', '4')}  |  ⏱️ Durasi: {proj.get('min_duration', '30')}-{proj.get('max_duration', '60')} menit  |  🎲 Komponen: {len(proj.get('components', []))} Item", size=11, color="#64748b")
                ], spacing=10),
                
                ft.ProgressBar(value=progress_pct / 100.0, color="#3b82f6", bgcolor="#e2e8f0", height=6),
                
                deadline_row
            ], spacing=8),
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#cbd5e1"),
            border_radius=8,
            padding=12
        )

        checklist_controls = []
        for phase_idx, phase in enumerate(SOP_PHASES_DETAIL):
            phase_name = phase.get("phase") or phase.get("nama") or phase.get("title") or f"Phase {phase_idx+1}"
            tasks = phase.get("tasks", [])
            
            task_checkboxes = []
            for t in tasks:
                is_checked = proj["tasks"].get(t, False)
                chk = ft.Checkbox(
                    label=t,
                    value=is_checked,
                    disabled=not is_admin,
                    on_change=lambda e, task_n=t: self.update_task_status(task_n, e.control.value)
                )
                task_checkboxes.append(chk)

            phase_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Icon("flag", size=14, color="#e11d48"),
                            ft.Text(f"Phase {phase_idx+1:02d}: {phase_name}", weight="bold", size=13, color="#1e293b")
                        ], spacing=6),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=5, color="transparent"),
                    ft.Column(task_checkboxes, spacing=4)
                ], spacing=4),
                bgcolor="white",
                border=ft.border.all(1, "#e2e8f0"),
                border_radius=8,
                padding=12
            )
            checklist_controls.append(phase_card)

        self.content_area.controls.append(
            ft.Container(
                content=ft.Column([
                    top_status_card,
                    ft.Divider(height=5, color="transparent"),
                    ft.Column(checklist_controls, spacing=10)
                ], spacing=10, tight=True, alignment=ft.MainAxisAlignment.START),
                padding=20,
                alignment=ft.alignment.top_left
            )
        )
        self.page.update()

    def open_date_picker(self):
        if self.page.session.get("user_role") == "admin":
            self.date_picker.open = True
            self.page.update()

    def handle_date_selected(self, e):
        if e.control.value and self.active_project_index is not None and self.page.session.get("user_role") == "admin":
            proj = self.projects[self.active_project_index]
            val = e.control.value
            if isinstance(val, datetime):
                proj["deadline"] = val.strftime("%Y-%m-%d")
            else:
                proj["deadline"] = str(val)[:10]
            
            db = self.page.session.get("db")
            save_data(db)
            self.render_project_content()
            self.refresh_project_list()

    def update_task_status(self, task_name, value):
        if self.active_project_index is not None and self.page.session.get("user_role") == "admin":
            proj = self.projects[self.active_project_index]
            if "tasks" not in proj:
                proj["tasks"] = {}
            proj["tasks"][task_name] = value
            
            db = self.page.session.get("db")
            save_data(db)
            self.render_project_content()

    def render_playtest_content(self):
        is_admin = self.page.session.get("user_role") == "admin"
        self.content_area.alignment = ft.MainAxisAlignment.START
        self.content_area.controls.clear()

        if self.active_project_index is None or not self.projects or self.active_project_index >= len(self.projects):
            self.content_area.controls.append(
                ft.Container(
                    content=ft.Text("Silakan pilih proyek terlebih dahulu.", color="#1e293b"),
                    padding=20
                )
            )
            self.page.update()
            return

        proj = self.projects[self.active_project_index]
        if "playtests" not in proj:
            proj["playtests"] = []

        playtests = proj["playtests"]

        def parse_playtest_date(pt):
            date_val = pt.get("tanggal", "")
            try:
                return datetime.strptime(date_val, "%Y-%m-%d")
            except:
                return datetime.min

        sorted_playtests = sorted(playtests, key=parse_playtest_date, reverse=True)

        title_actions = [ft.Text("Playtest Log", size=24, weight="bold", color="#2c3e50")]
        if is_admin:
            title_actions.append(
                ft.IconButton(
                    icon="add",
                    icon_size=18,
                    bgcolor="#2ecc71",
                    icon_color="white",
                    tooltip="Tambah Playtest Log",
                    on_click=self.modal_tambah_playtest
                )
            )

        title_row = ft.Row(title_actions, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        log_controls = []
        if len(sorted_playtests) == 0:
            log_controls.append(
                ft.Container(
                    content=ft.Text("Belum ada riwayat Playtest", size=12, italic=True, color="#1e293b"),
                    padding=10
                )
            )
        else:
            for pt in sorted_playtests:
                orig_index = playtests.index(pt)
                
                tanggal = pt.get("tanggal", "-")
                pemain = pt.get("pemain", "-")
                durasi = pt.get("durasi", "-")
                pemenang = pt.get("pemenang", "-")
                catatan = pt.get("catatan", "-")

                card_actions = [
                    ft.Row([
                        ft.Icon("calendar_today", size=14, color="#3b82f6"),
                        ft.Text(f"Tanggal: {tanggal}", size=12, weight="bold", color="#1e293b"),
                        ft.Text(" | ", color="grey"),
                        ft.Icon("group", size=14, color="#64748b"),
                        ft.Text(f"Pemain: {pemain} orang", size=12, color="#64748b"),
                        ft.Text(" | ", color="grey"),
                        ft.Icon("timer", size=14, color="#64748b"),
                        ft.Text(f"Durasi: {durasi} Mins", size=12, color="#64748b"),
                    ], spacing=6)
                ]

                if is_admin:
                    card_actions.append(
                        ft.IconButton(
                            icon="close",
                            icon_size=16,
                            icon_color="#e74c3c",
                            tooltip="Hapus Log",
                            on_click=lambda e, idx=orig_index: self.hapus_playtest(idx)
                        )
                    )

                card = ft.Container(
                    content=ft.Column([
                        ft.Row(card_actions, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Row([
                            ft.Icon("emoji_events", size=14, color="#d97706"),
                            ft.Text(f"Pemenang / Skor: {pemenang}", size=12, weight="bold", color="#d97706")
                        ], spacing=6),
                        
                        ft.Row([
                            ft.Icon("description", size=14, color="#64748b"),
                            ft.Text(f"Catatan: {catatan}", size=12, color="#475569")
                        ], spacing=6)
                    ], spacing=6),
                    bgcolor="white",
                    border=ft.border.all(1, "#cbd5e1"),
                    border_radius=8,
                    padding=12
                )
                log_controls.append(card)

        self.content_area.controls.append(
            ft.Container(
                content=ft.Column([
                    title_row,
                    ft.Divider(height=10),
                    ft.Column(log_controls, spacing=10)
                ], spacing=10, tight=True, alignment=ft.MainAxisAlignment.START),
                padding=20,
                alignment=ft.alignment.top_left
            )
        )
        self.page.update()

    def modal_tambah_playtest(self, e):
        if self.page.session.get("user_role") != "admin":
            return

        txt_tanggal = ft.TextField(
            label="Tanggal Playtest (YYYY-MM-DD)",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            value=datetime.now().strftime("%Y-%m-%d"),
            text_size=12,
            dense=True,
            expand=True
        )

        def open_pt_datepicker(e):
            self.temp_playtest_date_field = txt_tanggal
            self.playtest_date_picker.open = True
            self.page.update()

        btn_calendar = ft.IconButton(
            icon="calendar_month",
            icon_size=20,
            icon_color="#3b82f6",
            tooltip="Pilih dari Kalender",
            on_click=open_pt_datepicker
        )

        txt_pemain = ft.TextField(
            label="Jumlah Pemain",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            hint_text="misal: 4",
            text_size=12,
            dense=True
        )
        txt_durasi = ft.TextField(
            label="Durasi (Menit)",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            hint_text="misal: 45",
            text_size=12,
            dense=True
        )
        txt_pemenang = ft.TextField(
            label="Pemenang / Skor Akhir",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            hint_text="misal: Pemain A (25 Poin)",
            text_size=12,
            dense=True
        )
        txt_catatan = ft.TextField(
            label="Catatan Sesi Playtest",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            multiline=True,
            min_lines=3,
            max_lines=5,
            text_size=12,
            dense=True
        )

        def simpan_playtest_log(e):
            tanggal = txt_tanggal.value.strip()
            pemain = txt_pemain.value.strip()
            durasi = txt_durasi.value.strip()
            pemenang = txt_pemenang.value.strip()
            catatan = txt_catatan.value.strip()

            if not tanggal:
                return

            new_log = {
                "tanggal": tanggal,
                "pemain": pemain,
                "durasi": durasi,
                "pemenang": pemenang,
                "catatan": catatan
            }

            proj = self.projects[self.active_project_index]
            if "playtests" not in proj:
                proj["playtests"] = []
            proj["playtests"].append(new_log)

            db = self.page.session.get("db")
            save_data(db)

            dlg_pt.open = False
            self.render_playtest_content()

        def batal_simpan_pt(e):
            dlg_pt.open = False
            self.page.update()

        dlg_pt = ft.AlertDialog(
            modal=True,
            title=ft.Text("Tambah Playtest Log", size=14, weight="bold", color="#1e293b"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([txt_tanggal, btn_calendar], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    txt_pemain,
                    txt_durasi,
                    txt_pemenang,
                    txt_catatan
                ], spacing=10, tight=True),
                width=380,
                height=380
            ),
            actions=[
                ft.TextButton("Batal", on_click=batal_simpan_pt),
                ft.ElevatedButton("Simpan Playtest Log", bgcolor="#3498db", color="white", on_click=simpan_playtest_log)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dlg_pt)
        dlg_pt.open = True
        self.page.update()

    def handle_playtest_date_selected(self, e):
        if e.control.value and self.temp_playtest_date_field:
            val = e.control.value
            if isinstance(val, datetime):
                self.temp_playtest_date_field.value = val.strftime("%Y-%m-%d")
            else:
                self.temp_playtest_date_field.value = str(val)[:10]
            self.temp_playtest_date_field.update()

    def hapus_playtest(self, index):
        if self.active_project_index is not None and self.page.session.get("user_role") == "admin":
            proj = self.projects[self.active_project_index]
            playtests = proj.get("playtests", [])
            if 0 <= index < len(playtests):
                playtests.pop(index)
                db = self.page.session.get("db")
                save_data(db)
                self.render_playtest_content()

    def render_idea_board_content(self):
        is_admin = self.page.session.get("user_role") == "admin"
        self.content_area.alignment = ft.MainAxisAlignment.START
        self.content_area.controls.clear()

        if self.active_project_index is None or not self.projects or self.active_project_index >= len(self.projects):
            self.content_area.controls.append(
                ft.Container(
                    content=ft.Text("Silakan pilih proyek terlebih dahulu.", color="#1e293b"),
                    padding=20
                )
            )
            self.page.update()
            return

        proj = self.projects[self.active_project_index]
        if "ideas" not in proj:
            proj["ideas"] = []

        ideas = proj["ideas"]

        def parse_idea_date(item):
            date_val = item.get("tanggal", "")
            try:
                return datetime.strptime(date_val, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    return datetime.strptime(date_val, "%Y-%m-%d")
                except:
                    return datetime.min

        sorted_ideas = sorted(ideas, key=parse_idea_date, reverse=True)

        title_actions = [ft.Text("Idea Board", size=24, weight="bold", color="#2c3e50")]
        if is_admin:
            title_actions.append(
                ft.IconButton(
                    icon="add",
                    icon_size=18,
                    bgcolor="#2ecc71",
                    icon_color="white",
                    tooltip="Tambah Ide / Mekanik Baru",
                    on_click=self.modal_tambah_ide
                )
            )

        title_row = ft.Row(title_actions, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        idea_controls = []
        if len(sorted_ideas) == 0:
            idea_controls.append(
                ft.Container(
                    content=ft.Text("Belum ada ide yang dicatat.", size=12, italic=True, color="#1e293b"),
                    padding=10,
                    alignment=ft.alignment.center
                )
            )
        else:
            status_colors = {
                "Pending": "#3b82f6",
                "Diuji": "#f97316",
                "Dibuang": "#6b7280",
                "Approve": "#22c55e"
            }

            for item in sorted_ideas:
                orig_index = ideas.index(item)
                
                judul = item.get("judul", "-")
                status = item.get("status", "Pending")
                deskripsi = item.get("deskripsi", "-")
                
                badge_color = status_colors.get(status, "#3b82f6")

                status_badge = ft.Container(
                    content=ft.Text(f"Status: {status}", size=12, weight="bold", color="white"),
                    bgcolor=badge_color,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=6
                )

                card_header_right = [status_badge]
                if is_admin:
                    card_header_right.append(
                        ft.IconButton(
                            icon="close",
                            icon_size=16,
                            icon_color="#e74c3c",
                            tooltip="Hapus Ide",
                            on_click=lambda e, idx=orig_index: self.hapus_ide(idx)
                        )
                    )

                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Row([
                                ft.Icon("lightbulb", size=16, color="#d97706"),
                                ft.Text(judul, size=13, weight="bold", color="#1e293b"),
                            ], spacing=8),
                            ft.Row(card_header_right, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Container(
                            content=ft.Text(deskripsi, size=12, color="#475569"),
                            padding=ft.padding.only(left=24)
                        )
                    ], spacing=6),
                    bgcolor="white",
                    border=ft.border.all(1, "#cbd5e1"),
                    border_radius=8,
                    padding=12
                )
                idea_controls.append(card)

        self.content_area.controls.append(
            ft.Container(
                content=ft.Column([
                    title_row,
                    ft.Divider(height=10),
                    ft.Column(idea_controls, spacing=10)
                ], spacing=10, tight=True, alignment=ft.MainAxisAlignment.START),
                padding=20,
                alignment=ft.alignment.top_left
            )
        )
        self.page.update()

    def modal_tambah_ide(self, e):
        if self.page.session.get("user_role") != "admin":
            return

        txt_judul = ft.TextField(
            label="Judul Ide / Mekanik",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            hint_text="misal: Mekanik Drafting Kartu Elemen",
            text_size=12,
            dense=True
        )
        
        dd_status = ft.Dropdown(
            label="Status Ide",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            value="Pending",
            options=[
                ft.dropdown.Option("Pending"),
                ft.dropdown.Option("Diuji"),
                ft.dropdown.Option("Dibuang"),
                ft.dropdown.Option("Approve")
            ],
            text_size=12,
            dense=True
        )

        txt_deskripsi = ft.TextField(
            label="Deskripsi / Catatan Detail",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            multiline=True,
            min_lines=4,
            max_lines=6,
            text_size=12,
            dense=True
        )

        def simpan_ide(e):
            judul = txt_judul.value.strip()
            status = dd_status.value
            deskripsi = txt_deskripsi.value.strip()

            if not judul:
                return

            new_idea = {
                "judul": judul,
                "status": status,
                "deskripsi": deskripsi,
                "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            proj = self.projects[self.active_project_index]
            if "ideas" not in proj:
                proj["ideas"] = []
            proj["ideas"].append(new_idea)

            db = self.page.session.get("db")
            save_data(db)

            dlg_idea.open = False
            self.render_idea_board_content()

        def batal_simpan_ide(e):
            dlg_idea.open = False
            self.page.update()

        dlg_idea = ft.AlertDialog(
            modal=True,
            title=ft.Text("Tambah Ide / Mekanik Baru", size=14, weight="bold", color="#1e293b"),
            content=ft.Container(
                content=ft.Column([
                    txt_judul,
                    dd_status,
                    txt_deskripsi
                ], spacing=10, tight=True),
                width=380,
                height=320
            ),
            actions=[
                ft.TextButton("Batal", on_click=batal_simpan_ide),
                ft.ElevatedButton("Simpan Ide", bgcolor="#3498db", color="white", on_click=simpan_ide)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dlg_idea)
        dlg_idea.open = True
        self.page.update()

    def hapus_ide(self, index):
        if self.active_project_index is not None and self.page.session.get("user_role") == "admin":
            proj = self.projects[self.active_project_index]
            ideas = proj.get("ideas", [])
            if 0 <= index < len(ideas):
                ideas.pop(index)
                db = self.page.session.get("db")
                save_data(db)
                self.render_idea_board_content()

    def on_asset_sort_change(self, e):
        val = e.control.value
        if not val:
            return
        if val == self.asset_sort_field:
            self.asset_sort_asc = not self.asset_sort_asc
        else:
            self.asset_sort_field = val
            self.asset_sort_asc = (val == "Nama")
        e.control.value = None
        e.control.label = f"Sort: {self.asset_sort_field} ({'↑' if self.asset_sort_asc else '↓'})"
        self.render_assets_content()

    def render_assets_content(self):
        is_admin = self.page.session.get("user_role") == "admin"
        self.content_area.alignment = ft.MainAxisAlignment.START
        self.content_area.controls.clear()

        if self.active_project_index is None or not self.projects or self.active_project_index >= len(self.projects):
            self.content_area.controls.append(
                ft.Container(
                    content=ft.Text("Silakan pilih proyek terlebih dahulu.", color="#1e293b"),
                    padding=20
                )
            )
            self.page.update()
            return

        proj = self.projects[self.active_project_index]
        if "media" not in proj:
            proj["media"] = []

        media_list = proj["media"]

        title_text = ft.Text("Assets", size=24, weight="bold", color="#2c3e50")

        asset_sort_dropdown = ft.Dropdown(
            label=f"Sort: {self.asset_sort_field} ({'↑' if self.asset_sort_asc else '↓'})",
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            options=[
                ft.dropdown.Option("Tanggal"),
                ft.dropdown.Option("Nama"),
                ft.dropdown.Option("Tipe")
            ],
            text_size=12,
            dense=True,
            width=160,
            on_change=self.on_asset_sort_change
        )

        if is_admin:
            btn_add_file = ft.IconButton(
                icon="add",
                icon_size=18,
                bgcolor="#2ecc71",
                icon_color="white",
                tooltip="Tambah Asset File",
                on_click=lambda _: self.file_picker.pick_files(allow_multiple=True)
            )

            if not self.is_delete_mode:
                btn_delete_action = ft.IconButton(
                    icon="delete",
                    icon_size=18,
                    bgcolor="#e74c3c",
                    icon_color="white",
                    tooltip="Hapus Asset",
                    on_click=self.enter_delete_mode
                )
                action_row = ft.Row([
                    ft.Row([btn_add_file, btn_delete_action], spacing=6),
                    asset_sort_dropdown
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            else:
                has_selection = len(self.selected_assets_to_delete) > 0
                btn_cancel_del = ft.ElevatedButton(
                    text="Batal",
                    on_click=self.cancel_delete_mode,
                    bgcolor="#95a5a6",
                    color="white"
                )
                btn_confirm_del = ft.ElevatedButton(
                    text="Hapus",
                    on_click=self.execute_delete_assets,
                    bgcolor="#e74c3c",
                    color="white",
                    opacity=1.0 if has_selection else 0.35,
                    disabled=not has_selection
                )
                action_row = ft.Row([
                    ft.Row([btn_add_file, ft.Row([btn_cancel_del, btn_confirm_del], spacing=6)], spacing=6),
                    asset_sort_dropdown
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        else:
            action_row = ft.Row([
                ft.Text(""), 
                asset_sort_dropdown
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        for idx, item in enumerate(media_list):
            if isinstance(item, str):
                path = item
                name = os.path.basename(path)
                ext = os.path.splitext(name)[1].lower()
                kat = "Image" if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] else "Document"
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                date_str = datetime.now().strftime("%Y-%m-%d")
                media_list[idx] = {
                    "path": path,
                    "name": name,
                    "kat": kat,
                    "ext": ext,
                    "date": date_str,
                    "timestamp": now_str
                }
            else:
                path = item.get("path", "")
                name = item.get("name", os.path.basename(path) if path else "File")
                ext = item.get("ext", os.path.splitext(name)[1].lower())
                kat = item.get("kat", "Image" if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] else "Document")
                date_str = item.get("date", datetime.now().strftime("%Y-%m-%d"))
                timestamp = item.get("timestamp", f"{date_str} 00:00")
                
                item["ext"] = ext
                item["kat"] = kat
                item["date"] = date_str
                item["timestamp"] = timestamp

        grouped_by_date = {}
        for idx, item in enumerate(media_list):
            d_str = item.get("date", datetime.now().strftime("%Y-%m-%d"))
            if d_str not in grouped_by_date:
                grouped_by_date[d_str] = []
            grouped_by_date[d_str].append((idx, item))

        for d_str in grouped_by_date:
            if self.asset_sort_field == "Nama":
                grouped_by_date[d_str].sort(key=lambda x: x[1].get("name", "").lower(), reverse=not self.asset_sort_asc)
            elif self.asset_sort_field == "Tipe":
                grouped_by_date[d_str].sort(key=lambda x: (x[1].get("ext", ""), x[1].get("name", "").lower()), reverse=not self.asset_sort_asc)
            elif self.asset_sort_field == "Tanggal":
                grouped_by_date[d_str].sort(key=lambda x: x[1].get("timestamp", ""), reverse=not self.asset_sort_asc)

        sorted_dates = sorted(grouped_by_date.keys(), reverse=True)

        sections_controls = []
        if len(media_list) == 0:
            sections_controls.append(ft.Text("Belum ada asset media.", size=12, italic=True, color="#1e293b"))
        else:
            for date_str in sorted_dates:
                items_in_date = grouped_by_date[date_str]
                
                grid_cards = []
                for idx, item in items_in_date:
                    path = item.get("path", "")
                    name = item.get("name", os.path.basename(path))
                    kat = item.get("kat", "Image")
                    is_image = (kat == "Image" or (path and path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))))
                    is_selected = idx in self.selected_assets_to_delete

                    if is_image:
                        b64_data = get_image_base64(path)
                        if b64_data:
                            thumb_content = ft.Image(src_base64=b64_data, width=90, height=90, fit=ft.ImageFit.COVER, error_content=ft.Icon("broken_image", size=30, color="grey"))
                        else:
                            thumb_content = ft.Icon("broken_image", size=30, color="grey")
                    else:
                        thumb_content = ft.Column([
                            ft.Icon("insert_drive_file", size=36, color="#3498db"),
                            ft.Text("DOC", size=10, weight="bold", color="#3498db")
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

                    thumbnail_container = ft.Container(
                        content=ft.Stack([
                            ft.Container(
                                content=thumb_content,
                                alignment=ft.alignment.center,
                                padding=5
                            ),
                            *( [
                                ft.Container(
                                    content=ft.Checkbox(
                                        value=is_selected,
                                        on_change=lambda e, i=idx: self.toggle_select_asset(i, e.control.value)
                                    ),
                                    alignment=ft.alignment.top_right,
                                    padding=2
                                )
                              ] if self.is_delete_mode else [] )
                        ]),
                        width=100,
                        height=100,
                        bgcolor="#ffffff" if is_image else "#e2e8f0",
                        border=ft.border.all(2, "#3498db" if is_selected else "#cbd5e1"),
                        border_radius=6,
                    )

                    card_content = ft.Container(
                        content=ft.Column([
                            thumbnail_container,
                            ft.Text(
                                name,
                                size=11,
                                color="#1e293b",
                                weight="bold",
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                text_align=ft.TextAlign.CENTER,
                            )
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=100,
                        ink=not self.is_delete_mode,
                        on_click=lambda e, i=idx: self.open_preview(i) if not self.is_delete_mode else None
                    )
                    grid_cards.append(card_content)

                date_header = ft.Row([
                    ft.Icon("calendar_today", size=14, color="#3b82f6"),
                    ft.Text(f"Tanggal: {date_str}", size=12, weight="bold", color="#1e293b")
                ], spacing=6)

                section_container = ft.Column([
                    date_header,
                    ft.Row(grid_cards, wrap=True, spacing=10, run_spacing=10),
                    ft.Divider(height=15, color="transparent")
                ], spacing=6)

                sections_controls.append(section_container)

        self.content_area.controls.append(
            ft.Container(
                content=ft.Column([
                    title_text,
                    action_row,
                    ft.Divider(height=10),
                    *sections_controls
                ], spacing=15, tight=True, alignment=ft.MainAxisAlignment.START),
                padding=20,
                alignment=ft.alignment.top_left
            )
        )
        self.page.update()

    def on_files_picked(self, e: ft.FilePickerResultEvent):
        if e.files and self.active_project_index is not None and self.page.session.get("user_role") == "admin":
            proj = self.projects[self.active_project_index]
            if "media" not in proj:
                proj["media"] = []
            
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            timestamp_str = now.strftime("%Y-%m-%d %H:%M")

            for f in e.files:
                path = f.path
                name = f.name
                ext = os.path.splitext(name)[1].lower()
                kat = "Image" if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] else "Document"
                proj["media"].append({
                    "path": path,
                    "name": name,
                    "kat": kat,
                    "ext": ext,
                    "date": today_str,
                    "timestamp": timestamp_str
                })
            
            db = self.page.session.get("db")
            save_data(db)
            self.render_assets_content()

    def enter_delete_mode(self, e):
        if self.page.session.get("user_role") == "admin":
            self.is_delete_mode = True
            self.selected_assets_to_delete.clear()
            self.render_assets_content()

    def cancel_delete_mode(self, e):
        self.is_delete_mode = False
        self.selected_assets_to_delete.clear()
        self.render_assets_content()

    def toggle_select_asset(self, idx, value):
        if value:
            self.selected_assets_to_delete.add(idx)
        else:
            self.selected_assets_to_delete.discard(idx)
        self.render_assets_content()

    def execute_delete_assets(self, e):
        if self.active_project_index is not None and self.page.session.get("user_role") == "admin":
            proj = self.projects[self.active_project_index]
            media_list = proj.get("media", [])
            
            sorted_indices = sorted(list(self.selected_assets_to_delete), reverse=True)
            for idx in sorted_indices:
                if 0 <= idx < len(media_list):
                    media_list.pop(idx)
            
            db = self.page.session.get("db")
            save_data(db)
        
        self.is_delete_mode = False
        self.selected_assets_to_delete.clear()
        self.render_assets_content()

    def open_preview(self, index):
        is_admin = self.page.session.get("user_role") == "admin"
        self.preview_index = index
        proj = self.projects[self.active_project_index]
        media_list = proj.get("media", [])
        if not media_list or index >= len(media_list):
            return

        self.preview_content_container = ft.Container(expand=True, alignment=ft.alignment.center)
        self.preview_footer_text = ft.Text("", size=12, weight="bold")

        top_actions = []
        # Mengunci opsi download hanya untuk Admin
        if is_admin:
            top_actions.append(
                ft.IconButton(icon="download", icon_size=16, tooltip="Unduh File", on_click=lambda _: self.download_current_file())
            )
            top_actions.insert(0, ft.IconButton(icon="edit", icon_size=16, tooltip="Ubah Nama", on_click=lambda _: self.open_rename_dialog(self.preview_index)))

        self.current_preview_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Text("Pratinjau Media", weight="bold", color="#1e293b"),
                ft.Row(top_actions, spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=self.preview_content_container,
                        width=500,
                        height=400,
                        alignment=ft.alignment.center,
                        bgcolor="#1e293b",
                        border_radius=8,
                        padding=5
                    ),
                    ft.Row([
                        ft.IconButton(icon="chevron_left", icon_color="#2c3e50", on_click=self.prev_preview, tooltip="Sebelumnya"),
                        self.preview_footer_text,
                        ft.IconButton(icon="chevron_right", icon_color="#2c3e50", on_click=self.next_preview, tooltip="Berikutnya"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], tight=True, spacing=10),
                width=520,
                height=480
            ),
            actions=[
                ft.TextButton("Tutup", on_click=self.close_preview)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.refresh_preview_content()

        self.page.overlay.append(self.current_preview_dialog)
        self.current_preview_dialog.open = True
        self.page.update()

    def close_preview(self, e):
        if hasattr(self, "current_preview_dialog") and self.current_preview_dialog:
            self.current_preview_dialog.open = False
            self.page.update()

    def prev_preview(self, e):
        proj = self.projects[self.active_project_index]
        media_list = proj.get("media", [])
        if media_list:
            self.preview_index = (self.preview_index - 1) % len(media_list)
            self.refresh_preview_content()

    def next_preview(self, e):
        proj = self.projects[self.active_project_index]
        media_list = proj.get("media", [])
        if media_list:
            self.preview_index = (self.preview_index + 1) % len(media_list)
            self.refresh_preview_content()

    def refresh_preview_content(self):
        proj = self.projects[self.active_project_index]
        media_list = proj.get("media", [])
        if not media_list or not hasattr(self, "preview_content_container"):
            return

        item = media_list[self.preview_index]
        path = item.get("path", "")
        name = item.get("name", os.path.basename(path))
        kat = item.get("kat", "Image")

        is_image = kat == "Image" or path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))

        if is_image:
            b64_data = get_image_base64(path)
            if b64_data:
                self.preview_content_container.content = ft.Image(
                    src_base64=b64_data, 
                    fit=ft.ImageFit.CONTAIN, 
                    expand=True,
                    error_content=ft.Column([
                        ft.Icon("broken_image", size=48, color="grey"),
                        ft.Text("Gagal memuat base64 gambar", size=11, color="grey")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            else:
                self.preview_content_container.content = ft.Icon("broken_image", size=48, color="grey")
        else:
            self.preview_content_container.content = ft.Column([
                ft.Icon("insert_drive_file", size=64, color="#3498db"),
                ft.Text("Dokumen:", size=13, weight="bold", color="white"),
                ft.Text(name, size=14, italic=True, color="#cbd5e1", text_align=ft.TextAlign.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)

        if hasattr(self, "preview_footer_text"):
            self.preview_footer_text.value = f"({self.preview_index + 1}/{len(media_list)}) - {name}"

        if hasattr(self, "page") and hasattr(self, "current_preview_dialog") and self.current_preview_dialog and self.current_preview_dialog.open:
            self.current_preview_dialog.update()

    def open_rename_dialog(self, target_index=None):
        if self.page.session.get("user_role") != "admin":
            return

        idx = target_index if target_index is not None else self.preview_index
        proj = self.projects[self.active_project_index]
        media_list = proj.get("media", [])
        if not media_list or idx >= len(media_list):
            return

        item = media_list[idx]
        current_name = item.get("name", "")

        txt_rename = ft.TextField(
            label="Nama Baru", 
            label_style=ft.TextStyle(size=11, color="#1e293b", weight="bold"),
            value=current_name, 
            text_size=12, 
            dense=True
        )

        def save_rename(e):
            new_name = txt_rename.value.strip()
            if new_name:
                item["name"] = new_name
                item["ext"] = os.path.splitext(new_name)[1].lower()
                db = self.page.session.get("db")
                save_data(db)
                dlg_rename.open = False
                self.render_assets_content()
                if hasattr(self, "current_preview_dialog") and self.current_preview_dialog and self.current_preview_dialog.open:
                    self.refresh_preview_content()

        def cancel_rename(e):
            dlg_rename.open = False
            self.page.update()

        dlg_rename = ft.AlertDialog(
            modal=True,
            title=ft.Text("Ubah Nama", size=14, color="#1e293b", weight="bold"),
            content=txt_rename,
            actions=[
                ft.TextButton("Batal", on_click=cancel_rename),
                ft.ElevatedButton("Simpan", bgcolor="#3498db", color="white", on_click=save_rename)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.page.overlay.append(dlg_rename)
        dlg_rename.open = True
        self.page.update()

    def download_current_file(self):
        if self.page.session.get("user_role") != "admin":
            return

        proj = self.projects[self.active_project_index]
        media_list = proj.get("media", [])
        if not media_list:
            return

        item = media_list[self.preview_index]
        src_path = item.get("path", "")
        name = item.get("name", os.path.basename(src_path))

        if src_path and os.path.exists(src_path):
            try:
                download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                if not os.path.exists(download_dir):
                    download_dir = os.getcwd()
                dest_path = os.path.join(download_dir, name)
                shutil.copyfile(src_path, dest_path)
                
                self.page.snack_bar = ft.SnackBar(ft.Text(f"File berhasil diunduh ke: {dest_path}"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Gagal mengunduh file: {str(ex)}"))
                self.page.snack_bar.open = True
                self.page.update()