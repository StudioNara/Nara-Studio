import flet as ft
import datetime
import shutil
import os

class StateGaleri:
    def __init__(self):
        self.items = [
            {
                "id": "1",
                "title": "Character Concept Art",
                "tags": ["#concept", "#character", "#digital"],
                "date": "2026-09-20",
                "files": [
                    "https://picsum.photos/id/1025/600/800",
                    "https://picsum.photos/id/1062/600/800",
                    "https://picsum.photos/id/1074/600/800"
                ]
            },
            {
                "id": "2",
                "title": "Environment Sketch",
                "tags": ["#bg", "#landscape"],
                "date": "2026-09-22",
                "files": [
                    "https://picsum.photos/id/1015/800/600"
                ]
            }
        ]
        self.selection_mode = False
        self.selected_ids = set()
        self.search_query = ""

class StateReferensi:
    def __init__(self):
        self.groups = [
            {
                "id": "ref_1",
                "title": "Anatomi Tangan & Pose",
                "tags": ["#anatomy", "#hands", "#pose"],
                "files": [
                    "https://picsum.photos/id/1069/500/700",
                    "https://picsum.photos/id/1074/500/700",
                    "https://picsum.photos/id/1084/500/700",
                    "https://picsum.photos/id/1080/500/700",
                    "https://picsum.photos/id/1081/500/700",
                    "https://picsum.photos/id/1082/500/700"
                ]
            }
        ]
        self.search_query = ""

class IlustrasiPage(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/ilustrasi")
        self.page = page
        
        self.galeri_state = StateGaleri()
        self.ref_state = StateReferensi()
        self.active_tab = "Galeri"

        self.preview_files = []
        self.preview_index = 0
        self.preview_title = ""

        self.preview_img = ft.Image(fit=ft.ImageFit.CONTAIN, height=380)
        self.preview_title_text = ft.Text("", weight="bold", size=16)
        self.preview_counter_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
        self.thumbnail_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        
        # Tombol Download Khusus Admin di Preview
        self.btn_download_preview = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            tooltip="Download Gambar Ukuran Asli",
            icon_color=ft.Colors.BLUE_700,
            on_click=self.download_current_preview_image
        )

        self.preview_dlg = ft.AlertDialog(
            content=ft.Container(
                width=800,
                height=560,
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            self.preview_title_text,
                            self.preview_counter_text
                        ], spacing=10),
                        self.btn_download_preview
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=10),
                    ft.Container(
                        content=ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.ARROW_LEFT,
                                icon_size=32,
                                tooltip="Sebelumnya (Arrow Left)",
                                on_click=lambda _: self.nav_preview(-1)
                            ),
                            self.preview_img,
                            ft.IconButton(
                                icon=ft.Icons.ARROW_RIGHT,
                                icon_size=32,
                                tooltip="Selanjutnya (Arrow Right)",
                                on_click=lambda _: self.nav_preview(1)
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        expand=True,
                        alignment=ft.alignment.center
                    ),
                    ft.Divider(height=10),
                    # Slider / Row Thumbnail
                    ft.Container(
                        content=self.thumbnail_row,
                        height=70,
                        alignment=ft.alignment.center
                    )
                ], spacing=5)
            ),
            actions=[ft.TextButton("Tutup", on_click=lambda _: self.close_dialog(self.preview_dlg))]
        )

        # File Pickers
        self.picker_galeri = ft.FilePicker(on_result=self.on_galeri_files_picked)
        self.picker_ref_add = ft.FilePicker(on_result=self.on_ref_files_picked)
        self.picker_ref_edit = ft.FilePicker(on_result=self.on_ref_edit_files_picked)
        self.picker_download = ft.FilePicker(on_result=self.on_download_path_selected)
        
        for picker in [self.picker_galeri, self.picker_ref_add, self.picker_ref_edit, self.picker_download]:
            if picker not in self.page.overlay:
                self.page.overlay.append(picker)

        self.page.on_keyboard_event = self.on_keyboard_press

        self.sidebar = self.build_sidebar()
        self.topbar = ft.Container()
        self.main_content = ft.Container(expand=True, padding=15)
        
        self.build_layout()

    def build_sidebar(self):
        return ft.Container(
            width=200,
            bgcolor=ft.Colors.GREY_100,
            padding=10,
            border=ft.border.only(right=ft.border.BorderSide(1, ft.Colors.GREY_300)),
            content=ft.Column(
                [
                    ft.Text("MENU ILUSTRASI", weight="bold", size=12, color=ft.Colors.GREY_600),
                    ft.Divider(height=10),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.GRID_VIEW, size=20),
                        title=ft.Text("Galeri", size=14),
                        selected=(self.active_tab == "Galeri"),
                        on_click=lambda _: self.switch_tab("Galeri")
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.BOOKMARKS, size=20),
                        title=ft.Text("Referensi", size=14),
                        selected=(self.active_tab == "Referensi"),
                        on_click=lambda _: self.switch_tab("Referensi")
                    )
                ],
                spacing=5
            )
        )

    def switch_tab(self, tab_name):
        self.active_tab = tab_name
        self.sidebar = self.build_sidebar()
        self.build_layout()
        self.page.update()

    def build_layout(self):
        back_route = "/dashboard"
        self.topbar = self.build_topbar(back_route)
        
        if self.active_tab == "Galeri":
            content_view = self.build_galeri_view()
        else:
            content_view = self.build_referensi_view()

        self.main_content.content = content_view

        self.controls = [
            ft.Row(
                [
                    self.sidebar,
                    ft.Column(
                        [
                            self.topbar,
                            self.main_content
                        ],
                        expand=True,
                        spacing=0
                    )
                ],
                expand=True,
                spacing=0
            )
        ]

    def build_topbar(self, back_route):
        search_field = ft.TextField(
            hint_text="Cari berdasarkan Judul atau #tag...",
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            prefix_icon=ft.Icons.SEARCH,
            width=400,
            on_change=self.on_search_change
        )

        is_admin = self.page.session.get("user_role") == "admin"
        actions = []

        if is_admin:
            if self.active_tab == "Galeri":
                if self.galeri_state.selection_mode:
                    is_disabled = len(self.galeri_state.selected_ids) == 0
                    actions = [
                        ft.TextButton("Batal", on_click=self.toggle_galeri_selection_mode),
                        ft.ElevatedButton(
                            "Hapus Terpilih",
                            bgcolor=ft.Colors.RED,
                            color=ft.Colors.WHITE,
                            disabled=is_disabled,
                            on_click=self.delete_selected_galeri
                        )
                    ]
                else:
                    actions = [
                        ft.IconButton(ft.Icons.CHECK_BOX_OUTLINED, tooltip="Pilih Banyak", on_click=self.toggle_galeri_selection_mode),
                        ft.ElevatedButton(
                            "Tambah Karya",
                            icon=ft.Icons.ADD,
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE,
                            on_click=self.open_add_galeri_dialog
                        )
                    ]
            else:
                actions = [
                    ft.ElevatedButton(
                        "Tambah Grup Referensi",
                        icon=ft.Icons.ADD_A_PHOTO,
                        bgcolor=ft.Colors.TEAL,
                        color=ft.Colors.WHITE,
                        on_click=self.open_add_ref_dialog
                    )
                ]

        return ft.Container(
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.GREY_300)),
            content=ft.Row(
                [
                    ft.IconButton(ft.Icons.HOME, tooltip="Kembali ke Dashboard", on_click=lambda _: self.page.go(back_route)),
                    search_field,
                    ft.Row(actions, spacing=10)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

    def build_galeri_view(self):
        q = self.galeri_state.search_query.lower()
        items = []
        for item in self.galeri_state.items:
            in_title = q in item["title"].lower()
            in_tags = any(q in t.lower() for t in item["tags"])
            if not q or in_title or in_tags:
                items.append(item)

        if not items:
            return ft.Container(
                content=ft.Text("Tidak ada karya yang ditemukan.", color=ft.Colors.GREY_500),
                alignment=ft.alignment.center,
                expand=True
            )

        grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=250,
            spacing=15,
            run_spacing=15,
            child_aspect_ratio=0.8
        )

        for item in items:
            grid.controls.append(self.build_galeri_card(item))

        return grid

    def build_galeri_card(self, item):
        is_selected = item["id"] in self.galeri_state.selected_ids
        cover_image = item["files"][0] if item["files"] else "https://picsum.photos/200/300"
        total_files = len(item["files"])

        stack_controls = [
            ft.Image(src=cover_image, fit=ft.ImageFit.COVER, width=250, height=180),
        ]

        if total_files > 1:
            stack_controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.COLLECTIONS, size=12, color=ft.Colors.WHITE),
                        ft.Text(f"{total_files}", size=11, color=ft.Colors.WHITE, weight="bold")
                    ], spacing=3, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=ft.Colors.BLACK54,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                    left=8,
                    top=8
                )
            )

        if self.galeri_state.selection_mode:
            stack_controls.append(
                ft.Container(
                    padding=5,
                    alignment=ft.alignment.top_right,
                    content=ft.Checkbox(
                        value=is_selected,
                        on_change=lambda e, item_id=item["id"]: self.toggle_item_selection(item_id)
                    )
                )
            )

        card_content = ft.Card(
            content=ft.Container(
                padding=10,
                content=ft.Column(
                    [
                        ft.Stack(stack_controls, height=180),
                        ft.Text(item["title"], weight="bold", size=14, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(" ".join(item["tags"]), size=10, color=ft.Colors.BLUE_700),
                        ft.Text(item["date"], size=10, color=ft.Colors.GREY_500),
                    ],
                    spacing=5
                )
            )
        )

        return ft.Container(
            content=card_content,
            on_click=lambda _: self.open_preview(item["files"], item["title"])
        )

    def build_referensi_view(self):
        q = self.ref_state.search_query.lower()
        groups = []
        for g in self.ref_state.groups:
            in_title = q in g["title"].lower()
            in_tags = any(q in t.lower() for t in g["tags"])
            if not q or in_title or in_tags:
                groups.append(g)

        if not groups:
            return ft.Container(
                content=ft.Text("Tidak ada grup referensi.", color=ft.Colors.GREY_500),
                alignment=ft.alignment.center,
                expand=True
            )

        col = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=20)
        for g in groups:
            col.controls.append(self.build_ref_group_row(g))

        return col

    def build_ref_group_row(self, group):
        is_admin = self.page.session.get("user_role") == "admin"
        
        row_images = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10)
        for idx, img_url in enumerate(group["files"]):
            stack_controls = [
                ft.Container(
                    content=ft.Image(
                        src=img_url, 
                        width=120, 
                        height=120, 
                        fit=ft.ImageFit.COVER, 
                        border_radius=8
                    ),
                    on_click=self.make_preview_handler(group["files"], group["title"], idx),
                    ink=True
                )
            ]

            if is_admin:
                stack_controls.append(
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=12,
                            icon_color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLACK54,
                            tooltip="Hapus gambar ini",
                            on_click=self.make_delete_handler(group, img_url)
                        ),
                        right=2,
                        top=2
                    )
                )

            img_card = ft.Stack(
                stack_controls,
                width=120,
                height=120
            )
            row_images.controls.append(img_card)

        header_actions = []
        if is_admin:
            header_actions = [
                ft.IconButton(ft.Icons.EDIT, icon_size=18, on_click=lambda e, g=group: self.open_edit_ref_dialog(g)),
                ft.IconButton(ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.RED, tooltip="Hapus Grup Referensi", on_click=lambda e, g=group: self.delete_ref_group(g))
            ]

        return ft.Container(
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(group["title"], weight="bold", size=16),
                                    ft.Text(" ".join(group["tags"]), size=12, color=ft.Colors.TEAL_700)
                                ],
                                spacing=2
                            ),
                            ft.Row(header_actions)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(height=10),
                    row_images
                ]
            )
        )

    def make_preview_handler(self, files, title, index):
        return lambda e: self.open_preview(files, title, index)

    def make_delete_handler(self, group, img_url):
        return lambda e: self.delete_single_ref_image(group, img_url)

    def delete_single_ref_image(self, group, img_url):
        if self.page.session.get("user_role") != "admin":
            return
        if img_url in group["files"]:
            group["files"].remove(img_url)
            self.build_layout()
            self.page.update()

    def open_preview(self, files, title, start_index=0):
        if not files:
            return
        self.preview_files = files
        self.preview_index = start_index
        self.preview_title = title
        
        # Aktifkan/nonaktifkan tombol download tergantung role admin
        is_admin = self.page.session.get("user_role") == "admin"
        self.btn_download_preview.visible = is_admin

        self.update_preview_content()
        self.page.open(self.preview_dlg)

    def download_current_preview_image(self, e):
        if self.page.session.get("user_role") != "admin":
            return

        if not self.preview_files or not (0 <= self.preview_index < len(self.preview_files)):
            return

        current_path = self.preview_files[self.preview_index]

        # Jika berupa URL web, buka langsung di browser untuk diunduh
        if current_path.startswith("http://") or current_path.startswith("https://"):
            self.page.launch_url(current_path)
            return

        # Jika file lokal, buka Save File Picker untuk menentukan lokasi simpan
        file_name = os.path.basename(current_path)
        self.download_source_file = current_path
        self.picker_download.save_file(file_name=file_name)

    def on_download_path_selected(self, e: ft.FilePickerResultEvent):
        if e.path and hasattr(self, "download_source_file") and self.download_source_file:
            try:
                shutil.copyfile(self.download_source_file, e.path)
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Gambar berhasil diunduh dalam ukuran asli!")))
            except Exception as ex:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Gagal mengunduh: {str(ex)}")))

    def select_preview_index(self, index):
        self.preview_index = index
        self.update_preview_content()
        self.page.update()

    def update_preview_content(self):
        if 0 <= self.preview_index < len(self.preview_files):
            self.preview_img.src = self.preview_files[self.preview_index]
            self.preview_title_text.value = self.preview_title
            self.preview_counter_text.value = f"{self.preview_index + 1} / {len(self.preview_files)}"

            # Render Thumbnail Slider
            self.thumbnail_row.controls.clear()
            for idx, img_url in enumerate(self.preview_files):
                is_active = (idx == self.preview_index)
                border_style = ft.border.all(2, ft.Colors.BLUE) if is_active else ft.border.all(1, ft.Colors.GREY_300)
                
                thumb = ft.Container(
                    content=ft.Image(src=img_url, width=60, height=60, fit=ft.ImageFit.COVER, border_radius=4),
                    border=border_style,
                    border_radius=6,
                    padding=2,
                    on_click=lambda e, i=idx: self.select_preview_index(i),
                    ink=True
                )
                self.thumbnail_row.controls.append(thumb)

    def nav_preview(self, delta):
        if not self.preview_files:
            return
        self.preview_index = (self.preview_index + delta) % len(self.preview_files)
        self.update_preview_content()
        self.page.update()

    def on_keyboard_press(self, e: ft.KeyboardEvent):
        if getattr(self.preview_dlg, "open", False):
            if e.key == "Arrow Left":
                self.nav_preview(-1)
            elif e.key == "Arrow Right":
                self.nav_preview(1)

    def close_dialog(self, dlg):
        self.page.close(dlg)

    def on_search_change(self, e):
        q = e.control.value
        if self.active_tab == "Galeri":
            self.galeri_state.search_query = q
        else:
            self.ref_state.search_query = q
        self.build_layout()
        self.page.update()

    def toggle_galeri_selection_mode(self, e=None):
        if self.page.session.get("user_role") != "admin":
            return
        self.galeri_state.selection_mode = not self.galeri_state.selection_mode
        self.galeri_state.selected_ids.clear()
        self.build_layout()
        self.page.update()

    def toggle_item_selection(self, item_id):
        if item_id in self.galeri_state.selected_ids:
            self.galeri_state.selected_ids.remove(item_id)
        else:
            self.galeri_state.selected_ids.add(item_id)
        self.build_layout()
        self.page.update()

    def delete_selected_galeri(self, e):
        if self.page.session.get("user_role") != "admin":
            return
        self.galeri_state.items = [
            item for item in self.galeri_state.items 
            if item["id"] not in self.galeri_state.selected_ids
        ]
        self.galeri_state.selected_ids.clear()
        self.galeri_state.selection_mode = False
        self.build_layout()
        self.page.update()

    def open_add_galeri_dialog(self, e):
        if self.page.session.get("user_role") != "admin":
            return
        
        self.temp_picked_files = []
        self.txt_galeri_title = ft.TextField(label="Judul Karya", dense=True)
        self.txt_galeri_tags = ft.TextField(label="Tags (pisahkan koma)", hint_text="#concept, #digital", dense=True)
        self.lbl_galeri_files = ft.Text("Belum ada file dipilih", size=12, color=ft.Colors.GREY_600)

        dlg = ft.AlertDialog(
            title=ft.Text("Tambah Karya Galeri"),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    self.txt_galeri_title,
                    self.txt_galeri_tags,
                    ft.ElevatedButton("Pilih Gambar", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: self.picker_galeri.pick_files(allow_multiple=True)),
                    self.lbl_galeri_files
                ], tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("Batal", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("Simpan", bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, on_click=lambda _: self.save_galeri_item(dlg))
            ]
        )
        self.page.open(dlg)

    def on_galeri_files_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.temp_picked_files = [f.path for f in e.files]
            self.lbl_galeri_files.value = f"{len(e.files)} file dipilih"
            self.page.update()

    def save_galeri_item(self, dlg):
        title = self.txt_galeri_title.value.strip()
        if not title:
            return

        raw_tags = self.txt_galeri_tags.value.split(",")
        tags = [t.strip() if t.strip().startswith("#") else f"#{t.strip()}" for t in raw_tags if t.strip()]

        files = self.temp_picked_files if hasattr(self, 'temp_picked_files') and self.temp_picked_files else ["https://picsum.photos/600/800"]

        new_item = {
            "id": str(datetime.datetime.now().timestamp()),
            "title": title,
            "tags": tags,
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "files": files
        }

        self.galeri_state.items.insert(0, new_item)
        self.close_dialog(dlg)
        self.build_layout()
        self.page.update()

    def open_add_ref_dialog(self, e):
        if self.page.session.get("user_role") != "admin":
            return

        self.temp_picked_ref_files = []
        self.txt_ref_title = ft.TextField(label="Judul Referensi", dense=True)
        self.txt_ref_tags = ft.TextField(label="Tags (pisahkan koma)", hint_text="#anatomy, #pose", dense=True)
        self.lbl_ref_files = ft.Text("Belum ada file dipilih", size=12, color=ft.Colors.GREY_600)

        dlg = ft.AlertDialog(
            title=ft.Text("Tambah Grup Referensi"),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    self.txt_ref_title,
                    self.txt_ref_tags,
                    ft.ElevatedButton("Pilih Gambar", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: self.picker_ref_add.pick_files(allow_multiple=True)),
                    self.lbl_ref_files
                ], tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("Batal", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("Simpan", bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE, on_click=lambda _: self.save_ref_group(dlg))
            ]
        )
        self.page.open(dlg)

    def on_ref_files_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.temp_picked_ref_files = [f.path for f in e.files]
            self.lbl_ref_files.value = f"{len(e.files)} file dipilih"
            self.page.update()

    def save_ref_group(self, dlg):
        title = self.txt_ref_title.value.strip()
        if not title:
            return

        raw_tags = self.txt_ref_tags.value.split(",")
        tags = [t.strip() if t.strip().startswith("#") else f"#{t.strip()}" for t in raw_tags if t.strip()]

        files = self.temp_picked_ref_files if hasattr(self, 'temp_picked_ref_files') and self.temp_picked_ref_files else ["https://picsum.photos/500/700"]

        new_group = {
            "id": f"ref_{datetime.datetime.now().timestamp()}",
            "title": title,
            "tags": tags,
            "files": files
        }

        self.ref_state.groups.insert(0, new_group)
        self.close_dialog(dlg)
        self.build_layout()
        self.page.update()

    def open_edit_ref_dialog(self, group):
        if self.page.session.get("user_role") != "admin":
            return

        self.editing_ref_group = group
        self.temp_edit_ref_files = list(group["files"])

        self.txt_edit_ref_title = ft.TextField(label="Judul Referensi", value=group["title"], dense=True)
        self.txt_edit_ref_tags = ft.TextField(label="Tags", value=", ".join(group["tags"]), dense=True)
        self.lbl_edit_ref_files = ft.Text(f"Total gambar: {len(self.temp_edit_ref_files)}", size=12, color=ft.Colors.GREY_600)

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Grup Referensi"),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    self.txt_edit_ref_title,
                    self.txt_edit_ref_tags,
                    ft.ElevatedButton("Tambah Gambar Baru", icon=ft.Icons.ADD_PHOTO_ALTERNATE, on_click=lambda _: self.picker_ref_edit.pick_files(allow_multiple=True)),
                    self.lbl_edit_ref_files
                ], tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("Batal", on_click=lambda _: self.close_dialog(dlg)),
                ft.ElevatedButton("Update", bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE, on_click=lambda _: self.update_ref_group(dlg))
            ]
        )
        self.page.open(dlg)

    def on_ref_edit_files_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            new_paths = [f.path for f in e.files]
            self.temp_edit_ref_files.extend(new_paths)
            self.lbl_edit_ref_files.value = f"Total gambar: {len(self.temp_edit_ref_files)}"
            self.page.update()

    def update_ref_group(self, dlg):
        if not hasattr(self, 'editing_ref_group'):
            return

        title = self.txt_edit_ref_title.value.strip()
        if not title:
            return

        raw_tags = self.txt_edit_ref_tags.value.split(",")
        tags = [t.strip() if t.strip().startswith("#") else f"#{t.strip()}" for t in raw_tags if t.strip()]

        self.editing_ref_group["title"] = title
        self.editing_ref_group["tags"] = tags
        self.editing_ref_group["files"] = self.temp_edit_ref_files

        self.close_dialog(dlg)
        self.build_layout()
        self.page.update()

    def delete_ref_group(self, group):
        if self.page.session.get("user_role") != "admin":
            return
        self.ref_state.groups = [g for g in self.ref_state.groups if g["id"] != group["id"]]
        self.build_layout()
        self.page.update()