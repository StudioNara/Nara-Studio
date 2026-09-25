import os
import json

DATA_FILE = "nara_studio_data.json"

def load_data():
    default_data = {
        "admin_auth": {"username": "Admin", "password": "1234"},
        "projects": [],
        "illustrations": [],
        "commissions": [],
        "settings": {"google_account": "Belum Terhubung", "sync_mode": "Otomatis (Real-time)"}
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_data.items():
                if k not in data: data[k] = v
            return data
    except Exception:
        return default_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

SOP_PHASES_DETAIL = [
    {
        "phase": "PHASE 01 — CONCEPT (Durasi: 1–3 hari)",
        "tasks": [
            "Mengetahui inti aksi pemain (core gameplay/action).",
            "Mengetahui kondisi dan cara pemain meraih kemenangan.",
            "Menentukan komponen utama yang dibutuhkan.",
            "Memiliki batasan skala/cakupan game (scope).",
            "Bisa merangkum dan menjelaskan game dalam waktu ±30 detik."
        ]
    },
    {
        "phase": "PHASE 02 — UGLY PROTOTYPE (Durasi: 3–5 hari)",
        "tasks": [
            "Game bisa dilakukan setup dari awal.",
            "Sesi permainan bisa dimulai dengan lancar.",
            "Bisa menyelesaikan satu putaran/permainan penuh.",
            "Kondisi menang/kalah dapat terpicu dengan benar.",
            "Berhasil mengidentifikasi masalah atau hambatan desain pertama."
        ]
    },
    {
        "phase": "PHASE 03 — PLAYTEST (Durasi: 1–2 minggu)",
        "tasks": [
            "Masalah terbesar dari mekanik telah teridentifikasi.",
            "Tidak ada strategi yang terbukti merusak jalannya game (broken strategy).",
            "Game memberikan pengalaman yang konsisten di setiap sesi.",
            "Mengetahui aspek apa saja yang masih perlu iterasi/perbaikan."
        ]
    },
    {
        "phase": "PHASE 04 — DEVELOPMENT & BALANCE (Durasi: 1 minggu)",
        "tasks": [
            "Core loop (lingkaran aktivitas utama) sudah stabil.",
            "Solusi untuk masalah-masalah utama sudah diterapkan.",
            "Komponen utama telah ditentukan secara pasti.",
            "Jumlah komponen/kartu berada di angka yang relatif final.",
            "Struktur giliran (turn structure) sudah final.",
            "Kondisi kemenangan sudah dikunci (final).",
            "Perubahan selanjutnya dipastikan hanya berupa penyesuaian kecil (tweaks)."
        ]
    },
    {
        "phase": "PHASE 05 — GRAPHIC DIRECTION (Durasi: 2–3 hari)",
        "tasks": [
            "Palet warna utama telah dipilih.",
            "Font/tipografi utama telah ditentukan.",
            "Gaya ilustrasi dan visual sudah disepakati.",
            "Struktur tata letak komponen (layout/hierarchy) jelas.",
            "Contoh komponen (sample component) menunjukkan konsistensi visual."
        ]
    },
    {
        "phase": "PHASE 06 — ILLUSTRATION & ASSETS (Durasi: 1–2 minggu)",
        "tasks": [
            "Ilustrasi kartu dan elemen visual utama selesai.",
            "Ikon, token, dan penanda visual lainnya sudah dibuat.",
            "Latar belakang, papan (jika ada), dan bagian belakang kartu (card backs) selesai.",
            "Desain penutup kotak (box art) selesai.",
            "Ilustrasi pendukung untuk buku aturan (rulebook) terpenuhi.",
            "Seluruh aset visual utama konsisten dan sesuai dengan tata letak final."
        ]
    },
    {
        "phase": "PHASE 07 — GRAPHIC PRODUCTION (Durasi: 3–5 hari)",
        "tasks": [
            "Card (Kartu): Ukuran, bleed, dan safe area sesuai standar cetak.",
            "Card (Kartu): Tipografi, ikon, penanda belakang, dan perataan (alignment) rapi serta mudah dibaca.",
            "Board / Komponen Papan (Jika ada): Ukuran, grid, label, dan hierarki visual sudah tepat.",
            "Token / Komponen Pendukung: Ukuran proporsional, mudah dibaca, dan konsisten.",
            "File Print-Ready: Resolusi gambar optimal dan mode warna sudah sesuai (CMYK/RGB).",
            "File Print-Ready: Garis potong (crop marks) dan penamaan file terorganisir dengan baik.",
            "File Print-Ready: Seluruh komponen telah memiliki versi digital yang siap cetak (print-ready)."
        ]
    },
    {
        "phase": "PHASE 08 — RULEBOOK & BOX (Durasi: 3–5 hari)",
        "tasks": [
            "Uji Coba Rulebook (Blind Test): Pemain baru bisa melakukan setup mandiri tanpa arahan desainer.",
            "Uji Coba Rulebook (Blind Test): Pemain baru bisa memulai dan menjalankan giliran dengan benar.",
            "Uji Coba Rulebook (Blind Test): Pemain baru paham cara menentukan akhir game dan menghitung skor.",
            "Box (Kotak Game): Bagian depan memuat judul, ilustrasi utama, dan deskripsi singkat.",
            "Box (Kotak Game): Bagian belakang memuat sinopsis, cara bermain singkat, daftar komponen, jumlah pemain, durasi, dan batas usia."
        ]
    },
    {
        "phase": "PHASE 09 — FINAL PROTOTYPE TEST / DEFINISI SELESAI (Durasi: 2–3 hari)",
        "tasks": [
            "Gameplay terbukti asyik dan playable.",
            "Sistem mekanik stabil tanpa celah fatal.",
            "Komponen inti lengkap dan final.",
            "Seluruh ilustrasi dan tata letak grafis selesai.",
            "Buku aturan (rulebook) dan kotak (box) selesai.",
            "Prototipe fisik berhasil dicetak, dirakit, dan diuji penuh secara mandiri tanpa bantuan desainer."
        ]
    }
]