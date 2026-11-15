# EmberLine — Production Deployment & Pipeline Guide

Panduan komprehensif arsitektur, pemrosesan data, konfigurasi lingkungan, deployment server, serta pemeliharaan sistem EmberLine.

---

## 1. Arsitektur Sistem

EmberLine dirancang dengan arsitektur terpisah (*decoupled architecture*) untuk menjamin integritas ilmiah, keandalan performa, dan kemudahan deployment:

```
[ NASA FIRMS Satellites ]
  - MODIS C6.1 (Aqua) 1 km
  - VIIRS VNP14IMG (S-NPP) 375 m
             │
             ▼
  ┌─────────────────────────────────────────────────────────┐
  │                   Pipeline Ilmiah                       │
  │  1. fetch_firms.py         (Pengunduhan & Validasi)     │
  │  2. grid.py                (Binning Spasial 0,1°)       │
  │  3. match.py               (Kolokasi Spasio-Temporal)   │
  │  4. harmonize.py           (Kalibrasi Regresi Log-Ratio)│
  │  5. calendar_climatology.py(Klimatologi 366-Hari C-06)  │
  │  6. windows.py             (Jendela Kritis Musiman)     │
  │  7. populate_realistic_osm (Verifikasi Daratan OSM)     │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼ (Artefak Versi JSON & CSV)
  ┌─────────────────────────────────────────────────────────┐
  │                 artifacts/ (17 Wilayah)                 │
  │  - accepted_series.csv     - baseline_series.csv        │
  │  - calendar.json & .csv    - windows.json               │
  │  - grid.json               - detections.json            │
  │  - run_manifest.json       - model_manifest.json        │
  └──────────────────────────┬──────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │                 Backend: FastAPI (api/app.py)           │
  │  - Port 8300 (Local / Reverse Proxy)                    │
  │  - Menyajikan data tanpa dependensi komputasi berat     │
  │  - Telemetri AI (Groq / Grok) terintegrasi              │
  └──────────────────────────┬──────────────────────────────┘
                             │ (REST JSON / CORS)
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │                 Frontend: React + Vite (web/)           │
  │  - Single Page Application (SPA)                        │
  │  - Leaflet Map (Canvas GPU Accelerated)                 │
  │  - Scrollytelling & Visualisasi Aksesibel (WCAG >= 90)  │
  └─────────────────────────────────────────────────────────┘
```

---

## 2. Prasyarat Sistem

### Spesifikasi Perangkat Keras (Minimum & Rekomendasi)
- **CPU**: 2 core (minimum), 4 core atau lebih (direkomendasikan untuk eksekusi pipeline paralel).
- **RAM**: 4 GB (minimum untuk serving API + Frontend), 8–16 GB (direkomendasikan saat memproses data FIRMS multi-tahun berukuran besar).
- **Penyimpanan**: Minimal 10 GB ruang kosong SSD untuk cache data mentah dan artefak 17 wilayah.

### Perangkat Lunak
- **Sistem Operasi**: Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9), macOS, atau Windows 10/11.
- **Python**: Versi 3.10, 3.11, atau 3.12.
- **Node.js**: Versi 18 LTS atau 20 LTS (dengan npm >= 9).
- **Reverse Proxy**: Nginx atau Caddy (untuk deployment produksi).

---

## 3. Instalasi dan Setup Lingkungan

### A. Kloning Repositori
```bash
git clone https://github.com/Mirekan/emberline.git
cd emberline
```

### B. Konfigurasi Lingkungan Python (Backend)
```bash
# Membuat virtual environment
python -m venv .venv

# Aktivasi virtual environment:
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Instal dependensi runtime backend & pipeline
pip install --upgrade pip
pip install -r requirements.txt
pip install -r api/requirements.txt
```

### C. Konfigurasi Frontend (Node.js)
```bash
cd web
npm install
cd ..
```

### D. Pengaturan Environment Variables (`.env`)
Salin file template `.env.example` ke `.env`:
```bash
cp .env.example .env
```
Buka `.env` dan sesuaikan parameter berikut:
```ini
# Port Layanan API Backend
EMBERLINE_API_PORT=8300
EMBERLINE_API_HOST=127.0.0.1

# Kunci API NASA FIRMS (Wajib jika ingin mengunduh data mentah baru)
FIRMS_MAP_KEY=your_nasa_firms_map_key_here

# Kunci Provider AI untuk Analisis Telemetri Satelit (Opsional)
GROQ_API_KEY=your_groq_api_key_here
XAI_API_KEY=your_xai_grok_key_here

# Pengaturan Lingkungan
ENVIRONMENT=production
# CORS terbuka untuk semua origin browser; konfigurasi origin tidak diperlukan.
```

---

## 4. Alur Pipeline Data & Reproduktibilitas

Jika ingin meregenerasi seluruh data observasi satelit secara mandiri dari awal:

### Langkah 1: Ekstraksi Data Mentah FIRMS
Mengambil data arsip sensor MODIS (Aqua) dan VIIRS (S-NPP):
```bash
python pipeline/fetch_firms.py --aoi riau --start-year 2012 --end-year 2026
```

### Langkah 2: Binning Spasial dan Kolokasi Sensor
Memetakan titik panas ke dalam kisi 0,1° dan mencocokkan pasangan overpass MODIS vs VIIRS:
```bash
python pipeline/grid.py --aoi riau
python pipeline/match.py --aoi riau
```

### Langkah 3: Kalibrasi Regresi & Deret Terharmonisasi (B2)
Menghitung rasio estimasi dan interval ketidakpastian:
```bash
python pipeline/harmonize.py --aoi riau
```

### Langkah 4: Penyusunan Siklus Klimatologi & Jendela Kritis
Membangun siklus 366 hari C-06 dan mengidentifikasi jendela kebakaran kritis:
```bash
python pipeline/calendar_climatology.py --aoi riau
python pipeline/windows.py --aoi riau
```

### Langkah 5: Pemotongan Poligon Daratan OpenStreetMap (OSM)
Menghilangkan titik-titik di wilayah perairan dan mengelompokkan deteksi pada bioma rentan riil:
```bash
python scripts/populate_realistic_osm_detections.py
```

### Langkah 6: Validasi Integritas Artefak
Memastikan seluruh file memenuhi skema kontrak EmberLine:
```bash
python scripts/validate_all.py
```

---

## 5. Pengujian & Verifikasi Kualitas (Quality Assurance)

Sebelum melakukan deployment, jalankan seluruh pengujian otomatis:

```bash
# 1. Tes Unit Endpoint & Logika Deret Waktu
python -m pytest tests/test_api_series.py

# 2. Tes Integritas Kontrak C-06 Kalender Klimatologi (17/17 Checks)
python tests/test_calendar.py

# 3. Tes Aksesibilitas dan Interaktivitas Peta
python tests/test_fire_map_tooltips.py
python tests/test_fire_map_provinces.py

# 4. Tes Komprehensif Seluruh Endpoint (17 Wilayah x 6 Endpoint = 102 Pengecekan)
python scripts/test_all_endpoints.py

# 5. Tes Kompilasi Tipe dan Build Aset Frontend
npm --prefix web run build
```

Seluruh pengujian di atas wajib berstatus **PASS / 100% Lulus**.

---

## 6. Prosedur Deployment Produksi

### Opsi A: Deployment Systemd + Nginx (Rekomendasi VM / VPS)

#### 1. Konfigurasi Layanan Backend Systemd (`/etc/systemd/system/emberline-api.service`)
```ini
[Unit]
Description=EmberLine FastAPI Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/emberline
Environment="PATH=/var/www/emberline/.venv/bin"
ExecStart=/var/www/emberline/.venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8300 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktifkan layanan:
```bash
sudo systemctl daemon-reload
sudo systemctl enable emberline-api
sudo systemctl start emberline-api
```

#### 2. Build Aset Frontend
```bash
cd /var/www/emberline/web
npm run build
# Hasil statis berada di /var/www/emberline/web/dist
```

#### 3. Konfigurasi Reverse Proxy Nginx (`/etc/nginx/sites-available/emberline`)
```nginx
server {
    listen 80;
    server_name emberline.yourdomain.com;

    # Frontend Statis
    location / {
        root /var/www/emberline/web/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache header untuk aset statis biner
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }

    # Proxy ke Backend API FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8300/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

Uji dan aktifkan Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/emberline /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

### Opsi B: Deployment Kontainer Docker

#### 1. `Dockerfile.api` (Backend)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r api/requirements.txt
COPY api/ ./api/
COPY artifacts/ ./artifacts/
EXPOSE 8300
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8300"]
```

#### 2. `docker-compose.yml`
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8300:8300"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    restart: unless-stopped

  web:
    image: nginx:alpine
    volumes:
      - ./web/dist:/usr/share/nginx/html
      - ./deploy/nginx.conf:/etc/nginx/conf.d/default.conf
    ports:
      - "80:80"
    depends_on:
      - api
    restart: unless-stopped
```

---

## 7. Monitoring, Cadangan, dan Troubleshooting

### Health Check Endpoint
Gunakan endpoint presets untuk mengecek status kesehatan server:
```bash
curl -f http://127.0.0.1:8300/api/aoi/presets || exit 1
```

### Penanganan Masalah Umum (*Troubleshooting*)
1. **Port 8300 Conflict (`Errno 10048` / `Address already in use`)**:
   - Periksa proses lama yang masih mengikat port:
     ```bash
     # Linux:
     sudo lsof -i :8300
     # Windows PowerShell:
     Get-NetTCPConnection -LocalPort 8300
     ```
   - Hentikan PID terkait sebelum memulai ulang Uvicorn.
2. **CORS Error pada Browser**:
   - Backend mengizinkan semua origin browser melalui `CORSMiddleware`; redeploy setelah perubahan konfigurasi.
3. **Data Tile Kalender Kosong**:
   - Pastikan file `baseline_series.csv` atau `harmonized_daily.csv` pada folder `artifacts/<aoi>/` memuat kolom observasi harian instrumen. Jalankan `python scripts/test_all_endpoints.py` untuk mengisolasi wilayah yang terdampak.
