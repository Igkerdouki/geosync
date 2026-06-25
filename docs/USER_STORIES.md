# GeoSync User Stories

## Format
**As a** [user type], **I want** [action], **so that** [benefit].

**Acceptance Criteria:**
- Specific, testable conditions that must be met

---

## Epic 1: Live Map Dashboard

### Story 1.1: View Spray Events
**As a** community member, **I want** to see recent pesticide spray events on a map, **so that** I know what's being applied near my home.

**Acceptance Criteria:**
- Map displays spray events from the past 30 days
- Each spray marker shows: chemical name, date, location
- Markers are color-coded by risk level (red = high, yellow = medium, green = low)
- User can click a marker to see full details
- Map loads in under 3 seconds

### Story 1.2: Filter Spray Events
**As a** researcher, **I want** to filter spray events by date, chemical, and county, **so that** I can analyze specific patterns.

**Acceptance Criteria:**
- Dropdown filter for time range (24h, 7 days, 30 days, custom)
- Dropdown filter for chemical type
- Dropdown filter for county
- Filters apply immediately without page reload
- "Clear filters" button resets all filters

### Story 1.3: View School Locations
**As a** parent, **I want** to see schools displayed on the map, **so that** I can check if spraying occurs near my child's school.

**Acceptance Criteria:**
- Schools displayed as blue markers
- School name shown on hover
- User can toggle school layer on/off
- Schools within active drift zones are highlighted

---

## Epic 2: Drift Prediction

### Story 2.1: Predict Drift from Spray Event
**As a** public health official, **I want** to see where pesticide drift will travel based on current weather, **so that** I can warn affected areas.

**Acceptance Criteria:**
- Select any spray event on map
- System fetches current wind speed and direction
- Drift cone displayed showing predicted spread
- Cone shows distance (in miles) and direction
- Risk zones displayed: high (red), medium (orange), low (yellow)

### Story 2.2: View Drift Animation
**As a** community member, **I want** to see an animated drift overlay, **so that** I can understand how pesticides spread over time.

**Acceptance Criteria:**
- Drift overlay pulses to indicate active drift
- Color gradient shows concentration (darker = higher)
- Animation can be toggled on/off
- Drift updates when weather changes

---

## Epic 3: Exposure Scoring

### Story 3.1: Check Exposure Score for Address
**As a** parent, **I want** to enter my home address and see an exposure score, **so that** I can understand my family's pesticide risk and discuss it with our doctor.

**Acceptance Criteria:**
- User enters any California address
- System returns exposure score (0-100)
- Score breakdown shows: contributing chemicals, number of nearby sprays, highest risk periods
- Historical trend shown (past 12 months)
- User can download report as PDF

### Story 3.2: Compare Exposure Across Locations
**As a** family considering relocation, **I want** to compare exposure scores between two addresses, **so that** I can make an informed decision about where to live.

**Acceptance Criteria:**
- User can enter two addresses
- Side-by-side comparison displayed
- Difference highlighted (e.g., "Address A has 40% lower exposure")

---

## Epic 4: Alerts

### Story 4.1: Register for Drift Alerts
**As a** parent, **I want** to register my home address for alerts, **so that** I receive a warning when pesticide drift is heading toward my location.

**Acceptance Criteria:**
- User enters email, phone (optional), and address
- Address is geocoded and validated
- Confirmation email/SMS sent
- User can manage (view/delete) their alerts

### Story 4.2: Receive Drift Alert
**As a** registered user, **I want** to receive an SMS/email when drift is approaching my location, **so that** I can take protective action.

**Acceptance Criteria:**
- Alert sent within 5 minutes of drift detection
- Alert includes: chemical name, estimated arrival time, distance, recommended actions
- Alert links to live map showing drift
- No more than 1 alert per hour (prevent spam)

### Story 4.3: School Alert System
**As a** school administrator, **I want** automatic alerts when drift approaches my campus, **so that** I can keep students indoors.

**Acceptance Criteria:**
- Schools can register as alert recipients
- Alert sent to designated school contact
- Alert includes: recommended action (keep students inside, close windows)
- Alert logged for documentation

---

## Epic 5: Dosage Recommendations

### Story 5.1: Get Optimal Dosage Recommendation
**As a** farmer, **I want** to input my crop, pest, and field size and receive an AI-recommended pesticide dosage, **so that** I use only what's needed and save money.

**Acceptance Criteria:**
- Form with dropdowns: crop type, pest type, field size (acres)
- System returns: recommended dosage (lbs), typical dosage, potential savings (%)
- Bee toxicity rating displayed (low/medium/high)
- Alternative lower-toxicity options suggested

### Story 5.2: View Historical Dosage Patterns
**As a** farm inspector, **I want** to see which farms consistently exceed recommended dosages, **so that** I can target compliance checks.

**Acceptance Criteria:**
- Dashboard showing farms by dosage vs. recommendation
- Filter by county, crop, time period
- Flag farms exceeding 150% of recommended dosage
- Export list as CSV

---

## Epic 6: NLP Query

### Story 6.1: Ask Questions in Plain English
**As a** community member, **I want** to ask questions like "What was sprayed near my house last week?", **so that** I can get answers without navigating complex data.

**Acceptance Criteria:**
- Chat interface for natural language input
- System parses intent and queries database
- Response in plain English with relevant data
- Follow-up questions supported
- Example queries shown for guidance

### Story 6.2: Ask Safety Questions
**As a** parent, **I want** to ask "Is it safe to take my kids outside today?", **so that** I can make informed decisions about outdoor activities.

**Acceptance Criteria:**
- System checks current drift conditions near user's location
- Response includes: safety assessment, nearby active sprays, recommended wait time
- Links to relevant exposure data

---

## Definition of Done (All Stories)
- [ ] Code reviewed and approved
- [ ] Unit tests passing
- [ ] Tested on mobile viewport
- [ ] No console errors
- [ ] Deployed to staging
- [ ] Accepted by product owner
