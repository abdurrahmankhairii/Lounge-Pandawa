# Arjuna Smart Lounge App

Dokumentasi Resmi Proyek Sistem Manajemen Lounge Terintegrasi untuk Balai Kesehatan Penerbangan. Sistem ini dirancang untuk menjawab tantangan operasional dengan berfokus pada **Keamanan (Security-First)**, **Skalabilitas (Scalability)**, dan **Kemudahan Penggunaan (Simplicity & Aesthetic)**.

---

## 1. Background & General Information
Arjuna Smart Lounge App adalah platform digital terintegrasi yang dirancang khusus untuk mengelola operasional Arjuna VIP Lounge di Balai Kesehatan Penerbangan, Kementerian Perhubungan. Fasilitas lounge sering kali menghadapi tantangan berupa *overbooking*, ketidakaturan antrian, pengelolaan pemesanan makanan (F&B) yang masih manual, dan kurangnya pemisahan akses yang jelas. 

Aplikasi ini hadir untuk mendigitalisasi seluruh proses dari hulu ke hilir dengan menerapkan arsitektur *Clean Architecture* dan *Security-First*, menggunakan stack teknologi terkini untuk memastikan operasional tanpa hambatan dengan antarmuka yang modern, responsif, dan bernuansa **elegan (Light Blue / Glassmorphism)**.

---

## 2. Fitur & Solusi Utama Terimplementasi
Sistem ini telah berhasil dibangun secara komprehensif, mengimplementasikan seluruh kebutuhan sistem dari backend hingga frontend:

### Backend (FastAPI + PostgreSQL + Redis)
- **Arsitektur Utama**: Setup sentralisasi di `main.py`, manajemen variabel via `config.py`, serta pool koneksi asinkron (PostgreSQL dan Redis) di `database.py`.
- **Security & Autentikasi**: Implementasi **Role-Based Access Control (RBAC)**, Token **JWT** (access & refresh), hashing *password* dengan **bcrypt**, skema 2FA (TOTP), serta dependensi keamanan ketat (`require_roles`) di `security.py` dan `auth.py`.
- **Database Models & Schemas**: Implementasi relasi seluruh tabel menggunakan SQLAlchemy asinkron (`models.py`) dan validasi request/response menggunakan Pydantic (`schemas.py`).
- **Distributed Lock (Anti-Collision Booking)**: Diimplementasikan pada `booking_service.py` untuk menjamin **tidak ada double booking** dalam satu *time slot* yang sama melalui *atomicity* Redis `SETNX`.
- **Sistem Antrian WAR (Waiting-Assign-Release)**: Antrian FIFO terjamin yang dibangun di `queue_service.py` memanfaatkan *Redis Sorted Sets (ZADD, ZPOPMIN)* dan eksekusi atomik *Lua Scripting* untuk meminimalisasi *race-condition*.
- **Midtrans Payment & F&B**: Layanan `payment_service.py` dan `menu.py` terintegrasi lengkap dengan webhook untuk mengelola pemesanan digital F&B lounge.
- **RESTful API Endpoints**: Pemisahan router endpoint yang modular untuk `/auth`, `/bookings`, `/queue`, `/menu`, `/orders`, `/staff`, dan `/admin`.

### Frontend (Next.js 14 + Tailwind CSS + Shadcn UI)
Dibangun menggunakan Next.js App Router dengan desain *vibrant*, dinamis, dan sangat estetis (tema *light blue* + *glassmorphism*).
- **Middleware Keamanan**: `src/middleware.ts` dipasang untuk filter akses JWT yang tersegregasi secara ketat antara rute public, `/staff`, dan `/admin`.
- **Aplikasi Tamu (Guest)**:
  - **Landing Page**: Micro-animation, hero section *glassmorphism*, fitur informatif, dan *Call-to-Action* yang modern.
  - **Online Booking**: Sistem kalender slot waktu interaktif.
  - **Konfirmasi Booking**: Penerbitan *QR Code* (via `qrcode.react`) untuk validasi check-in.
  - **Digital Menu**: Katalog makanan & minuman dengan fitur *shopping cart* yang persisten (menggunakan status `Zustand`).
- **Portal Pelayanan (Staff Area)**:
  - **Walk-in & Capacity Widget**: Dashboard untuk registrasi langsung di tempat yang dilengkapi widget progress bar kapasitas lounge *real-time* (berubah dari biru ke kuning, hingga merah ketika penuh).
- **Display Antrian Publik (Kiosk/TV)**:
  - Layar interaktif (`/queue/display`) dengan efek kedip untuk panggilan nomor saat ini, daftar tunggu, animasi *marquee*, dan *live update* setiap 3 detik.
- **Dashboard Administrator**:
  - Manajemen katalog F&B (CRUD) yang interaktif, laporan operasional, dan pengelolaan role/pengguna.

### Docker Infrastructure
Proyek disatukan menggunakan *Infrastructure as Code* via Docker Compose (`docker-compose.yml`) yang mengatur container PostgreSQL, Redis, Backend (Uvicorn), dan Frontend (Next dev) sekaligus.

---

## 3. Project Structure

```text
Lounge-Pandawa/
├── backend/                  # REST API Backend
│   ├── app/
│   │   ├── api/v1/endpoints/ # Route Controllers (auth.py, bookings.py, queue.py, dll)
│   │   ├── core/             # Konfigurasi, Security JWT, koneksi DB (config.py, security.py, database.py)
│   │   ├── models/           # SQLAlchemy ORM Models (models.py)
│   │   ├── schemas/          # Pydantic validation (schemas.py)
│   │   ├── services/         # Business Logic (booking_service.py, queue_service.py, dll)
│   │   └── main.py           # Entry point aplikasi FastAPI
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Aplikasi Next.js
│   ├── src/
│   │   ├── app/              # App Router Pages
│   │   │   ├── (public)/     # Landing, Booking, Menu
│   │   │   ├── admin/        # Layout & Dashboard Administrator
│   │   │   ├── staff/        # Layout & Dashboard Staff (Walk-in, Queue)
│   │   │   ├── queue/        # Kiosk / TV Display
│   │   │   ├── layout.tsx, globals.css, providers.tsx
│   │   ├── components/ui/    # Komponen Shadcn UI
│   │   ├── hooks/            # Custom React Hooks
│   │   └── lib/              # Utils, Axios interceptor, Zustand store (store.ts)
│   ├── Dockerfile.dev
│   ├── tailwind.config.ts
│   └── components.json
├── docker-compose.yml        # Orchestration
└── README.md
```

---

## 4. Struktur & Relasi Database (PostgreSQL)

Database menggunakan model relasional dengan skema terpusat:
- **User**: Tabel utama kredensial.
- **Role & UserRole**: Pemetaan *Many-to-Many* untuk *Role-Based Access Control*.
- **TimeSlot**: Master slot waktu operasional.
- **Booking**: Reservasi per sesi. Relasi ke *User* (opsional, jika tamu mendaftar) dan *TimeSlot*. Memiliki status (`pending`, `confirmed`, `checked_in`, `completed`, `cancelled`).
- **MenuCategory & MenuItem**: Katalog F&B. Relasi *One-to-Many*.
- **Order & OrderItem**: Transaksi pemesanan makanan/minuman selama di lounge. Relasi ke *Booking*.
- **Payment**: Sistem pencatatan pembayaran (Midtrans). Relasi *One-to-One* ke *Order*.
- **QueueLog**: Sejarah perpindahan status *Waiting*, *Calling*, *Serving*, *Completed*.
- **AuditLog**: Rekam jejak seluruh aktivitas manajerial (untuk akuntabilitas).
- **LoungeSettings**: *Key-Value store* konfigurasi dinamis aplikasi.

---

## 5. Alur Bisnis (Business Flow)

1. **Alur Booking (Reservasi)**:
   - User melihat *TimeSlot* yang tersedia.
   - User mengirim formulir reservasi. Sistem mengeksekusi `booking_service.py` untuk mengunci slot sementara (`Redis SETNX`).
   - Kapasitas di-update. Sistem men-*generate* `booking_code` dan QR Code.
2. **Alur Check-in & Queue (Antrian)**:
   - Tamu tiba di *receptionist* dan menunjukkan QR.
   - Resepsionis menekan tombol "Check In" atau meng-input Walk-in.
   - Sistem mendaftarkan tamu ke antrian *Redis Sorted Set* berdasarkan *timestamp*.
   - Tamu diarahkan menunggu atau masuk. TV Display (`/queue/display`) membaca status antrian.
   - Saat siap, Staf memanggil tamu. Status berubah ke `serving`.
3. **Alur Pemesanan F&B (Digital Menu)**:
   - Tamu menggunakan *smartphone* di mejanya untuk mengakses `/menu`.
   - Menambah makanan ke keranjang, lalu *Checkout*.
   - Staf Dapur (KDS - *Kitchen Display System*) menerima *Order* secara realtime. Makanan diantar, dan status pesanan diperbarui.

---

## 6. Port Network (Penting)
Untuk menghindari *collision* dengan port standar `3000` (React) dan `8000` (FastAPI) yang umumnya sudah dipakai oleh service lain di OS, project ini menggunakan set port terdedikasi:

| Service | Protocol / Port Eksternal (Host) | Port Internal Container |
| :--- | :--- | :--- |
| **Frontend App** | `http://localhost:3555` | 3000 |
| **Backend API** | `http://localhost:8555` | 8000 |
| **PostgreSQL** | `localhost:5455` | 5432 |
| **Redis** | `localhost:6355` | 6379 |

---

## 7. Cara Menjalankan & Menggunakan (How to Run)

### Prasyarat:
Pastikan **Docker** dan **Docker Compose** telah terinstal di sistem Anda.

### Menjalankan Development Server:
1. Buka Terminal pada *root directory* proyek (`Lounge-Pandawa`).
2. Eksekusi perintah infrastruktur:
   ```bash
   docker-compose up --build -d
   ```
3. Tunggu proses instalasi *NPM packages* dan instalasi dependensi *Python* selesai di dalam container.
4. Aplikasi sudah dapat diakses melalui browser Anda:
   - **Frontend App (Public & Tamu):** [http://localhost:3555](http://localhost:3555)
   - **Display Antrian TV:** [http://localhost:3555/queue/display](http://localhost:3555/queue/display)
   - **Portal Admin & Staf:** [http://localhost:3555/admin](http://localhost:3555/admin) / [http://localhost:3555/staff](http://localhost:3555/staff)
   - **Swagger Backend API Docs:** [http://localhost:8555/docs](http://localhost:8555/docs)

*Catatan: Saat aplikasi pertama kali di-build (`lifespan` FastAPI trigger), akun `SUPER_ADMIN` akan dibuat secara otomatis dengan email `admin@arjunalounge.id` dan password `Admin@2025!`.*

---

## 8. Panduan Deployment Production (How to Deploy)

Untuk men-*deploy* aplikasi ini di VPS atau *Cloud Environment*:

1.  **Siapkan Server (VM/VPS)** (Ubuntu 22.04 direkomendasikan).
2.  Install `docker` dan `docker-compose`.
3.  Ubah variabel di `.env` (atau langsung di environment file server Anda):
    - `APP_ENV=production`
    - `DEBUG=False`
    - Atur `SECRET_KEY` dengan *random string* panjang.
    - Atur ulang `CORS_ORIGINS` ke domain asli Anda (misal: `https://arjunalounge.id`).
4.  Siapkan Reverse Proxy (seperti NGINX atau Traefik) untuk menangani *SSL/HTTPS* dan merutekan *traffic* masuk ke port `3555` (Frontend) dan `/api` ke port `8555` (Backend).
5.  Untuk Frontend Next.js, Anda dapat mengoptimalkan build dengan menambahkan argumen production build (`npm run build && npm run start` alih-alih `npm run dev`) di dalam *Dockerfile production*.
6.  Jalankan `docker-compose -f docker-compose.prod.yml up -d` (Buat compose file spesifik prod).

---
*Dikembangkan secara komprehensif oleh Tim AI berdasarkan spesifikasi teknis PT Pandawa Cipta Jaya.*