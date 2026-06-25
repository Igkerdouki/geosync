# GeoSync Project Progress

## Data Downloads

### PUR Data (Pesticide Use Reports)
- [x] pur2023.zip (248 MB) - Downloaded & unzipped
- [x] pur2022.zip (155 MB) - Downloaded
- [x] pur2021.zip (163 MB) - Downloaded
- [x] pur2020.zip (179 MB) - Downloaded
- [x] pur2019.zip (176 MB) - Downloaded
- [ ] pur2018.zip (175 MB) - Downloading...
- [ ] pur2017.zip (165 MB) - Downloading...
- [ ] pur2016.zip (170 MB) - Downloading...
- [ ] pur2015.zip (166 MB) - Downloading...
- [ ] pur2014.zip (148 MB) - Downloading...

Source: https://files.cdpr.ca.gov/pub/outgoing/pur_archives/

### Other Data Sources
- [ ] CalEnviroScreen 4.0 - Not downloaded
- [ ] California School Directory - Not downloaded
- [ ] OpenWeatherMap API key - Not set up

---

## Local Setup

### PostgreSQL
- [x] Installed via Homebrew (postgresql@15)
- [x] Service started
- [x] Database created: `geosync`
- [ ] PostGIS extension - Installing...
- [ ] Tables created - Not done
- [ ] PUR data loaded - Not done

### Render (Production)
- [ ] PostgreSQL created on Render
- [ ] Connection string saved
- [ ] PostGIS enabled
- [ ] Data loaded

---

## GitLab

- [x] SSH key created (~/.ssh/id_ed25519_gitlab)
- [x] SSH key added to GitLab
- [x] Cloned brainstorming repo
- [x] Pushed GeoSync_README.md to geosync-proposal branch
- [x] Added system architecture diagram
- [ ] Create geosync project repo (private)

---

## Code Progress

### Backend (FastAPI)
- [ ] Project structure created
- [ ] /api/drift endpoint
- [ ] /api/sprays endpoint
- [ ] /api/exposure endpoint
- [ ] /api/dosage endpoint
- [ ] /api/alerts endpoint
- [ ] /api/weather endpoint

### Frontend (React + Vite)
- [ ] Project initialized
- [ ] MapLibre setup
- [ ] Spray markers
- [ ] Drift overlay
- [ ] Sidebar/filters

### ML Models
- [ ] Drift predictor (Gaussian plume)
- [ ] Dosage optimizer (XGBoost)
- [ ] Risk scorer

---

## Files Created

- ~/Desktop/GeoSync_README.md
- ~/Desktop/GeoSync_Build_Plan.txt
- ~/Desktop/GeoSync_Data_Sources.txt
- ~/Desktop/GeoSync_User_Stories.txt
- ~/Desktop/ESPINA_email.txt
- ~/Desktop/brainstorming/GeoSync_README.md (pushed to GitLab)
- ~/Desktop/brainstorming/geosync_mockup.html
- ~/Desktop/brainstorming/geosync_architecture.html
- ~/Desktop/geosync_data/ (PUR data folder)

---

## Team

**Runtime Terror** - SDSC RDS Summer 2026

| Dev | Role |
|-----|------|
| Ioanna | Backend + Drift Model Lead |
| Dev 2 | Frontend Lead |
| Dev 3 | Frontend Support |
| Dev 4 | Backend + Data |
| Dev 5 | Integrations |

---

## Next Steps

1. [ ] Set up Render PostgreSQL
2. [ ] Load PUR data into database
3. [ ] Create FastAPI project structure
4. [ ] Build /api/sprays endpoint first
5. [ ] Set up React + Vite frontend

---

Last updated: June 24, 2026
