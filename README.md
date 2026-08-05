# GeoSync

**Real-time pesticide drift monitoring and research platform for California**

## Problem

Every year, millions of pounds of pesticides drift off farms into communities — exposing children, farmworkers, and families without any warning. The data exists. The protection does not.

## Solution

GeoSync combines California's Pesticide Use Reports (PUR) with drift modeling and toxicity data to provide:

- **Live Map Dashboard** - See spray events with color-coded risk zones
- **Drift Prediction** - Predict where pesticides will travel using Gaussian plume modeling
- **Research Tools** - Export data, analyze trends, compare chemicals
- **Toxicity Database** - EPA classifications, carcinogenicity, health concerns
- **Time Series Analysis** - Monthly/yearly trends by county or chemical

## Quick Start

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Frontend
cd frontend
npm run dev -- --port 3000
```

Then open: http://localhost:3000

## API Endpoints

### Spray Data
| Endpoint | Description |
|----------|-------------|
| `GET /api/sprays` | Query spray records with filters |
| `GET /api/sprays/stats` | Aggregated statistics |
| `GET /api/sprays/years` | Available years with counts |
| `GET /api/sprays/heatmap` | County GeoJSON for maps |

### Drift Prediction
| Endpoint | Description |
|----------|-------------|
| `GET /api/drift/predict` | Gaussian plume prediction |
| `GET /api/drift/stability` | Atmospheric stability class |

### Research Tools
| Endpoint | Description |
|----------|-------------|
| `GET /api/research/export` | Export data as CSV/JSON (up to 100K rows) |
| `GET /api/research/chemicals` | All chemicals with usage stats |
| `GET /api/research/sites` | Application sites (crops) analysis |
| `GET /api/research/trends/monthly` | Monthly time series |
| `GET /api/research/trends/yearly` | Yearly trends |
| `GET /api/research/county/{code}` | Detailed county analysis |
| `GET /api/research/chemical/{code}` | Detailed chemical analysis |
| `GET /api/research/compare/chemicals` | Compare multiple chemicals |
| `GET /api/research/compare/counties` | Compare multiple counties |

### Toxicity Data
| Endpoint | Description |
|----------|-------------|
| `GET /api/toxicity/chemical/{code}` | Toxicity info for chemical |
| `GET /api/toxicity/categories` | EPA toxicity category definitions |
| `GET /api/toxicity/classes` | Chemical class information |
| `GET /api/toxicity/high-concern` | List of high-concern chemicals |
| `GET /api/toxicity/search` | Search by toxicity characteristics |
| `GET /api/toxicity/usage-in-california` | Link toxicity to actual usage |

## Example Research Queries

```bash
# Export all 2023 Fresno County data as CSV
curl "http://localhost:8001/api/research/export?year=2023&county=FRESNO&format=csv" > fresno_2023.csv

# Get chemicals with >1M lbs applied in 2023
curl "http://localhost:8001/api/research/chemicals?year=2023&min_lbs=1000000"

# Get yearly trends for Glyphosate (chem_code 1855)
curl "http://localhost:8001/api/research/chemical/1855"

# Find all bee-toxic chemicals
curl "http://localhost:8001/api/toxicity/search?bee_toxic=true"

# Get high-concern chemicals with usage data
curl "http://localhost:8001/api/toxicity/usage-in-california?year=2023"

# Compare Fresno vs Kern counties
curl "http://localhost:8001/api/research/compare/counties?codes=10,15&year=2023"
```

## Database

- **55+ million spray records** (2014-2023)
- **~780 unique chemicals** tracked per year
- **58 California counties** with coordinates
- **Time series data** for trend analysis

## Tech Stack

**Backend**
- Python / FastAPI
- PostgreSQL (55M+ records)
- Gaussian plume drift model
- EPA toxicity classifications

**Frontend**
- React 18 + Vite
- MapLibre GL JS (open-source maps)
- Interactive drift simulation

**Algorithms**
- Gaussian Plume Model (EPA AgDRIFT equations)
- Pasquill-Gifford stability classification

## Project Structure

```
geosync/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # PostgreSQL connection
│   │   ├── api/
│   │   │   ├── sprays.py        # Spray data endpoints
│   │   │   ├── drift.py         # Drift prediction
│   │   │   ├── research.py      # Research/export tools
│   │   │   └── toxicity.py      # Chemical toxicity data
│   │   ├── services/
│   │   │   └── drift.py         # Gaussian plume model
│   │   └── data/
│   │       └── chemicals.py     # Toxicity database
│   ├── scripts/
│   │   └── load_all_years.py    # Data loading
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx              # Map + controls
│       └── App.css              # Styles
└── docs/
```

## Gaussian Plume Model

```
C(x,y,z) = (Q / 2πu σy σz) × exp(-y²/2σy²) × [exp(-(z-H)²/2σz²) + exp(-(z+H)²/2σz²)]
```

| Stability | Conditions | Dispersion |
|-----------|------------|------------|
| A | Very unstable (sunny, light wind) | Rapid |
| B | Unstable | Good |
| C | Slightly unstable | Moderate |
| D | Neutral (cloudy/windy) | Typical |
| E | Slightly stable (night, light wind) | Reduced |
| F | Stable (clear night, calm) | Poor - drift travels far |

## Toxicity Categories (EPA)

| Category | Signal Word | Acute Oral LD50 |
|----------|-------------|-----------------|
| I | DANGER-POISON | Up to 50 mg/kg |
| II | WARNING | 50-500 mg/kg |
| III | CAUTION | 500-5000 mg/kg |
| IV | CAUTION (optional) | >5000 mg/kg |

## Running the App

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8001/docs |

## Next Steps

- [x] Database with 55M+ records
- [x] County heatmap visualization
- [x] Gaussian plume drift model
- [x] Research export tools (CSV/JSON)
- [x] Chemical toxicity database
- [x] Time series analysis
- [ ] Real-time weather integration
- [ ] SMS/email alerts
- [ ] Proximity to schools analysis
- [ ] XGBoost dosage optimization

## Author

Ioanna Gkerdouki - Math-CS, UC San Diego

## License

MIT
