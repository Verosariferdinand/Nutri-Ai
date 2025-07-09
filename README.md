# 🥗 Nutri AI – Personalized Nutrition Dashboard

**Nutri AI** adalah aplikasi web interaktif berbasis Flask yang membantu pengguna memantau asupan kalori dan protein harian mereka berdasarkan profil tubuh, aktivitas, dan tujuan kebugaran. Aplikasi ini dirancang untuk mendukung proses *bulking*, *cutting*, maupun *maintenance* gizi.

---

## 🚀 Fitur Utama

- 🔐 **User Authentication** — Registrasi & login aman dengan hashing password.
- 🧠 **Perhitungan BMR & TDEE Otomatis** — Berdasarkan umur, berat badan, tinggi badan, jenis kelamin, aktivitas, dan tipe tubuh.
- 📸 **Upload Foto Makanan** — Bisa input makanan dengan gambar.
- 🍱 **Input & Kategori Makanan** — Input makanan sesuai waktu makan: pagi, siang, sore, malam.
- 📊 **Dashboard Kalori & Protein** — Visualisasi target dan progres harian.
- 🧾 **Laporan Harian Otomatis** — Rekam histori gizi pengguna secara harian.
- ⏰ **Reset Otomatis 24 Jam** — Menggunakan `APScheduler` untuk reset data harian secara otomatis.

---

## 🏗️ Teknologi yang Digunakan

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate
- **Database**: SQLite
- **Scheduler**: APScheduler
- **Security**: Werkzeug (Password Hashing)
- **Templating**: Jinja2 (HTML + CSS untuk Frontend)

---

## ⚙️ Instalasi

1. **Clone repository** ini:
   ```bash
   git clone https://github.com/Verosariferdinand/Nutri-Ai.git
   cd Nutri-Ai
   ```
  Atau bisa download via rar di link berikut <br>
  **GitHub:** [https://github.com/Verosariferdinand/Nutri-Ai](https://github.com/Verosariferdinand/Nutri-Ai)

2. **🐍Install Python**: <br>
Pastikan Python 3.8 atau lebih baru sudah terpasang. <br> 
👉 [Klik di sini untuk download Python](https://www.python.org/downloads/)

3. **Jalankan requirements**: <br>
ketik di bawah ini untuk menjalankan requirements <br>
  ```bash
  pip install -r requirements.txt
```

4. **Jalankan Sourcecode**: <br>
Masuk folder nutri Ai, Jalankan perintah ini di terminal
```bash
python app.py
```

5. **Masuk Ke Localhost**: <br>
Masuk ke pencarian internet (seperti chrome, firefox, dll), lalu ketik seperti berikut
```
Localhost:5000
```

---
🧠 Perhitungan Gizi
BMR dihitung dengan rumus Mifflin-St Jeor.

TDEE disesuaikan berdasarkan aktivitas harian dan tipe tubuh:

Ectomorph → +20%

Mesomorph → normal

Endomorph → -20%

Target kalori & protein otomatis ditentukan berdasarkan tujuan: bulking, cutting, atau maintain.

📌 Catatan Tambahan
Pastikan folder static/images sudah tersedia agar upload file berhasil.

Scheduler berjalan secara background untuk reset data harian secara otomatis.

🤝 Kontribusi
Pull request sangat diterima! Jika kamu punya ide atau perbaikan, silakan open issue atau fork dan kirim PR.

📄 Lisensi
MIT License. Bebas digunakan dan dimodifikasi. <br>
___
🙌 Dibuat oleh <br>
Verosariferdinand – GitHub Profile <br>
M. Sulthon Abiyyu <br>
Amalia Rossa Annjani <br>
Indri Arianti Wibowo <br>
Brigide Tirenia Loresta <br>
===


