# GeoSync Sprint Backlog

**Team:** Runtime Terror (5 developers)
**Duration:** 8 weeks
**SDSC RDS Summer 2026**

---

## WEEK 1: Setup & Data Pipeline

### Feature 1.1: Project Infrastructure
- [ ] Create GitLab repo (geosync)
- [ ] Set up branch protection rules
- [ ] Create development branches for each dev
- [ ] Write initial README with setup instructions

### Feature 1.2: Database Setup
- [ ] Create PostgreSQL on Render
- [ ] Enable PostGIS extension
- [ ] Design database schema (sprays, schools, alerts, chemicals)
- [ ] Create tables and indexes
- [ ] Test connection from local

### Feature 1.3: Data Pipeline
- [ ] Unzip all PUR data (2014-2023)
- [ ] Write Python script to parse PUR CSV files
- [ ] Load 2023 data into PostgreSQL (test)
- [ ] Load all years (2014-2023)
- [ ] Verify data integrity (row counts, sample queries)

### Feature 1.4: Backend Skeleton
- [ ] Initialize FastAPI project structure
- [ ] Set up virtual environment
- [ ] Create requirements.txt
- [ ] Set up database connection (SQLAlchemy)
- [ ] Create health check endpoint (/api/health)
- [ ] Deploy skeleton to Render

---

## WEEK 2: Core Backend APIs

### Feature 2.1: Sprays API
- [ ] Create Spray model (SQLAlchemy)
- [ ] GET /api/sprays - list sprays with filters
- [ ] Filter by date range
- [ ] Filter by county
- [ ] Filter by chemical name
- [ ] Filter by location (lat/lon + radius)
- [ ] Pagination support
- [ ] Write unit tests

### Feature 2.2: Weather Integration
- [ ] Get OpenWeatherMap API key
- [ ] Create weather service
- [ ] GET /api/weather?lat=&lon=
- [ ] Return wind speed, direction, temp, humidity
- [ ] Cache weather data (15 min TTL)

### Feature 2.3: Schools Data
- [ ] Download California School Directory
- [ ] Parse school locations (name, lat, lon)
- [ ] Load into schools table
- [ ] GET /api/schools - list schools
- [ ] Filter by county/region

---

## WEEK 3: Drift Prediction Model

### Feature 3.1: Gaussian Plume Implementation
- [ ] Research AgDRIFT equations
- [ ] Implement basic Gaussian plume formula
- [ ] Input: spray location, wind, droplet size
- [ ] Output: drift distance, direction, spread angle
- [ ] Create drift calculation service

### Feature 3.2: Drift API
- [ ] POST /api/drift - predict drift
- [ ] Input: lat, lon, spray_type (aerial/ground)
- [ ] Fetch current weather automatically
- [ ] Return drift polygon (GeoJSON)
- [ ] Return affected area in sq miles
- [ ] Return estimated concentration levels

### Feature 3.3: Risk Zone Calculation
- [ ] Define risk thresholds (high/medium/low)
- [ ] Calculate concentration at distance
- [ ] Generate concentric risk zones
- [ ] Return as GeoJSON for map overlay

---

## WEEK 4: Frontend Foundation

### Feature 4.1: React Project Setup
- [ ] Initialize with Vite
- [ ] Install dependencies (react-router, axios, tailwind)
- [ ] Set up project structure (components, pages, hooks)
- [ ] Create base layout (header, sidebar, main)
- [ ] Configure environment variables

### Feature 4.2: Map Integration
- [ ] Install MapLibre GL JS
- [ ] Create MapContainer component
- [ ] Center on California
- [ ] Add zoom controls
- [ ] Add attribution

### Feature 4.3: Spray Markers
- [ ] Fetch sprays from API
- [ ] Create SprayMarker component
- [ ] Color by risk level (red/orange/green)
- [ ] Add click handler for details
- [ ] Add marker clustering for performance

### Feature 4.4: Basic UI Components
- [ ] Header with logo and nav
- [ ] Sidebar skeleton
- [ ] Loading spinner
- [ ] Error message component

---

## WEEK 5: Frontend Features

### Feature 5.1: Drift Overlay
- [ ] Create DriftOverlay component
- [ ] Render drift polygon on map
- [ ] Color gradient by concentration
- [ ] Add animation (pulse effect)
- [ ] Toggle visibility

### Feature 5.2: Filters & Sidebar
- [ ] Time range filter (24h, 7d, 30d)
- [ ] Chemical type dropdown
- [ ] Risk level filter
- [ ] County filter
- [ ] Apply filters to API call
- [ ] Clear filters button

### Feature 5.3: Spray Details Panel
- [ ] Show on marker click
- [ ] Display: chemical, date, amount, location
- [ ] Show risk level badge
- [ ] "Predict Drift" button
- [ ] Close button

### Feature 5.4: School Markers
- [ ] Fetch schools from API
- [ ] Create SchoolMarker component (blue)
- [ ] Show school name on hover
- [ ] Toggle visibility layer

---

## WEEK 6: Exposure & Alerts

### Feature 6.1: Exposure Score API
- [ ] GET /api/exposure?address=
- [ ] Geocode address to lat/lon
- [ ] Query sprays within radius (past 30 days)
- [ ] Calculate weighted exposure score (0-100)
- [ ] Return chemical breakdown
- [ ] Return historical trend

### Feature 6.2: Exposure Score UI
- [ ] Create Exposure page
- [ ] Address input form
- [ ] Display score with gauge/meter
- [ ] Show chemical breakdown chart
- [ ] Show nearby spray events

### Feature 6.3: Alerts Backend
- [ ] Create alerts table (email, phone, address, lat, lon)
- [ ] POST /api/alerts/register
- [ ] Validate email/phone
- [ ] Geocode and store location
- [ ] GET /api/alerts (list user's alerts)
- [ ] DELETE /api/alerts/:id

### Feature 6.4: Alerts UI
- [ ] Create Alerts page
- [ ] Registration form
- [ ] List active alerts
- [ ] Delete alert button

---

## WEEK 7: Notifications & Polish

### Feature 7.1: SMS Notifications
- [ ] Set up Twilio account
- [ ] Create notification service
- [ ] Send SMS when drift detected near registered location
- [ ] Include chemical name, distance, ETA
- [ ] Rate limit to prevent spam

### Feature 7.2: Email Notifications
- [ ] Set up SendGrid account
- [ ] Create email templates
- [ ] Send email alerts
- [ ] Include map preview image

### Feature 7.3: Dosage Optimizer (Stretch)
- [ ] Train XGBoost model on PUR data
- [ ] Input: crop, pest, field_size
- [ ] Output: recommended dosage
- [ ] POST /api/dosage
- [ ] Create dosage form UI

### Feature 7.4: UI Polish
- [ ] Responsive design (mobile)
- [ ] Dark/light theme toggle
- [ ] Loading states
- [ ] Error handling
- [ ] Empty states

---

## WEEK 8: Demo & Deploy

### Feature 8.1: Production Deploy
- [ ] Deploy backend to Render (production)
- [ ] Deploy frontend to Render (static site)
- [ ] Set environment variables
- [ ] Enable HTTPS
- [ ] Test all endpoints

### Feature 8.2: Testing
- [ ] End-to-end testing
- [ ] Load testing (concurrent users)
- [ ] Fix critical bugs
- [ ] Performance optimization

### Feature 8.3: Documentation
- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guide
- [ ] Architecture diagram
- [ ] Data sources list

### Feature 8.4: Demo Preparation
- [ ] Create demo script
- [ ] Prepare sample queries
- [ ] Record backup video
- [ ] Practice presentation
- [ ] Prepare Q&A answers

---

## BACKLOG (Future / Stretch)

### NLP Query Engine
- [ ] Set up OpenAI/Claude API
- [ ] Create RAG pipeline
- [ ] POST /api/query
- [ ] "What was sprayed near X last week?"
- [ ] Natural language responses

### Predict Next Spray
- [ ] Train model on historical patterns
- [ ] Seasonal detection
- [ ] Farm-level predictions
- [ ] Alert before spray happens

### Mobile App
- [ ] React Native version
- [ ] Push notifications
- [ ] Location-based alerts

### Hardware Integration
- [ ] ESP32 sensor design
- [ ] Air quality sensors
- [ ] Real-time data ingestion
- [ ] Sensor dashboard

---

## Task Assignment Template

| Task ID | Task | Assignee | Status | Sprint |
|---------|------|----------|--------|--------|
| 1.1.1 | Create GitLab repo | Ioanna | Todo | Week 1 |
| 1.2.1 | Create PostgreSQL on Render | Ioanna | Todo | Week 1 |
| ... | ... | ... | ... | ... |

---

## Definition of Done

- [ ] Code reviewed by 1+ team member
- [ ] Unit tests pass
- [ ] No console errors
- [ ] Works on mobile viewport
- [ ] Deployed to staging
- [ ] Documented in README

---

Last updated: June 24, 2026
