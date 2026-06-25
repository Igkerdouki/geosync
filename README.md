# GeoSync

**Real-time pesticide drift monitoring and prediction platform for California**

## Problem

Every year, millions of pounds of pesticides drift off farms into communities — exposing children, farmworkers, and families without any warning. The data exists. The protection does not.

## Solution

GeoSync combines California's Pesticide Use Reports (PUR) with weather data and drift modeling to:

- **Live Map Dashboard** - See spray events with color-coded risk zones
- **Drift Prediction** - Predict where pesticides will travel using Gaussian plume modeling
- **Exposure Scoring** - Know your risk at any California address
- **Alerts** - Get SMS/email warnings before drift reaches your location
- **Dosage Optimization** - Help farmers use less pesticide

## Tech Stack

**Backend**
- Python / FastAPI
- PostgreSQL + PostGIS
- XGBoost (dosage optimization)

**Frontend**
- React + Vite
- MapLibre GL JS
- Tailwind CSS

**Data Sources**
- California PUR (2014-2023) - 10 years of pesticide spray records
- EPA AgDRIFT equations
- OpenWeatherMap API
- California School Directory

## Project Structure

```
geosync/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Business logic
│   └── scripts/          # Data loading scripts
├── frontend/             # React app
├── docs/                 # Documentation
└── data/                 # Local data (gitignored)
```

## Setup

```bash
# Clone
git clone https://github.com/yourusername/geosync.git
cd geosync

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev
```

## Data

PUR data can be downloaded from:
https://files.cdpr.ca.gov/pub/outgoing/pur_archives/

## Author

Ioanna Gkerdouki - Math-CS, UC San Diego

## License

MIT
