# Listening Telemetry & 3D Physical Media Shelf

A full-stack music analytics dashboard and interactive 3D PlayStation 2-inspired physical media shelf (Vinyl, CD, Cassette). Built with **FastAPI**, **SQLAlchemy**, **React**, **Three.js (`@react-three/fiber`)**, and **Tailwind CSS**.

## Features

* **Listening Telemetry Dashboard**: Tracks lifetime, monthly (last 30 days), and weekly (last 7 days) listening minutes, hours, play counts, top artists, top albums, top tracks, and recent stream history.
* **Multi-Platform Ingestion**: Supports **Apple Music** (`Library.xml` + `Apple Music Play Activity.csv`) and **Spotify** (`Streaming_History_Audio_*.json` exports + optional automated API sync).
* **Smart Disambiguation & Reconciliation**: Prevents same-title songs by different artists from colliding and reconciles play history regardless of whether `Library.xml` or `Play Activity.csv` is imported first.
* **Automated High-Res Artwork Enrichment**: Resolves 1000x1000 album covers and artist portraits via the Deezer and iTunes Catalog APIs with artist-matching guardrails.
* **Sub-15ms Cached Queries**: Pre-computes and caches aggregations across all timeframes in an `AppCache` layer with non-blocking background warming.
* **Interactive 3D PS2 Collection Shelf**: Browse your physical Vinyl, CD, and Cassette collection in a 3D environment with CRT scanlines, flashlight cursor lighting, format filtering (`ALL` / `VINYL` / `CD` / `CASSETTE`), and alphabetical sorting (`ARTIST` / `ALBUM` / `FMT`).
* **Live Catalog Autocomplete & Link Resolution**: Add physical media via live search or by pasting an Apple Music or Spotify album link to automatically pull cover art and tracklists.
* **Procedural Wrapped Share Cards & Theme Customizer**: Generate downloadable recap graphics and customize colors, layouts (`Bento`, `Classic`, `Compact`), fonts, and 3D space/photo backgrounds.

---

## Tech Stack

* **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pandas, HTTPX, Uvicorn, PostgreSQL (`psycopg`) / SQLite.
* **Frontend**: React 18, TypeScript, Vite, Three.js, `@react-three/fiber`, `@react-three/drei`, Zustand, Tailwind CSS, Lucide Icons.

---

## Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/music-stats.git](https://github.com/YOUR_USERNAME/music-stats.git)
cd music-stats

```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate virtual environment:
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Start FastAPI server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Seeding Your Music Data
You can import your data either through the Sync Data button in the web UI or via the command-line seeder (backend/seed_from_files.py).

Where to Get Your Export Files
- Apple Music (Library.xml): In the Apple Music / iTunes desktop app, click File → Library → Export Library... and save as Library.xml.
- Apple Music (Apple Music Play Activity.csv): Request your privacy data at privacy.apple.com → select Apple Media Services information. Inside the downloaded zip, locate Apple Music Play Activity.csv.
- Spotify (Streaming_History_Audio_*.json): Request your Extended Streaming History from your Spotify Account Privacy page.

## Running the CLI Seeder (Local SQLite)
Place your files in backend/data/ and run from inside backend/:

```bash
python seed_from_files.py \
  --xml "data/Library.xml" \
  --activity-csv "data/Apple Music Play Activity.csv" \
  --collection-csv "data/collection.example.csv"
```
- Idempotent Re-Uploads: You can re-run the seeder or re-upload updated CSV/XML files at any time. Existing (track_id, played_at) stream events are automatically deduplicated so your listening minutes are never double-counted.

- Exporting Your Physical Shelf to CSV: To back up your current physical shelf (physical_items table) to a portable CSV file with all artwork URLs and tracklists intact:
```bash
python seed_from_files.py --export-collection "data/collection.csv"
```

# Production Deployment Guide (Neon + Render + Vercel)
## Database (Neon PostgreSQL)
1. Create a free project on Neon.
2. Copy your Pooled Connection String and change the scheme prefix from postgresql:// to postgresql+psycopg://:
```bash
postgresql+psycopg://USER:PASSWORD@ep-example-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
```
3. Seed your production Neon database directly from your local machine:
```bash
python seed_from_files.py \
  --db-url "postgresql+psycopg://USER:PASSWORD@ep-example-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require" \
  --xml "data/Library.xml" \
  --activity-csv "data/Apple Music Play Activity.csv" \
  --collection-csv "data/collection.csv"
```

## Backend (Render Web Service)
1. Create a new Web Service on Render connected to your GitHub repo.
2. Configure the service:
- Root Directory: backend
- Build Command: pip install -r requirements.txt
- Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
3. Add Environment Variables on Render:
- DATABASE_URL: Your postgresql+psycopg://... Neon URL
- ADMIN_SECRET: A strong password used to unlock admin features in the UI
- CORS_ORIGINS: Your Vercel frontend URL (e.g., https://your-app.vercel.app,https://www.yourdomain.com)

## Frontend (Vercel)

1. Import your repo into Vercel with the Root Directory set to frontend.
2. Add the Environment Variable:
- VITE_API_URL: Your Render backend URL (e.g., https://your-backend.onrender.com)
3. Deploy!