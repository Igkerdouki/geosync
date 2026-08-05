"""
Farmer Portal API - Login, registration, and spray reporting

This is the core of the real-time reporting system:
1. Farmers register/login
2. Before spraying, they log: chemical, amount, location, time
3. Dashboard updates immediately via WebSocket
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
from enum import Enum

from app.database import get_connection
from app.api.realtime import manager  # For broadcasting updates

router = APIRouter()
security = HTTPBearer(auto_error=False)

# JWT Configuration
JWT_SECRET = "geosync-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ==================== MODELS ====================

class FarmSize(str, Enum):
    small = "small"      # < 100 acres
    medium = "medium"    # 100-500 acres
    large = "large"      # 500-2000 acres
    enterprise = "enterprise"  # > 2000 acres

class VerificationStatus(str, Enum):
    """
    Verification status for farmer-submitted reports.
    GeoSync does not replace official state reporting (CalAgPermits/DPR),
    but integrates farmer-reported updates with official records.
    """
    pending = "pending"          # Submitted, awaiting verification
    verified = "verified"        # Matched with official PUR record
    farmer_reported = "farmer_reported"  # Not yet in official records
    rejected = "rejected"        # Invalid or incorrect data

class FarmerRegister(BaseModel):
    email: EmailStr
    password: str
    farm_name: str
    owner_name: str
    county: str
    farm_size: FarmSize
    primary_crops: str  # comma-separated
    phone: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class FarmerLogin(BaseModel):
    email: EmailStr
    password: str

class SprayReport(BaseModel):
    chemical_name: str
    chemical_type: str  # herbicide, insecticide, fungicide, fumigant
    lbs_applied: float
    acres_treated: float
    application_method: str  # ground, aerial, irrigation
    target_crop: str
    field_name: Optional[str] = None
    lat: float
    lon: float
    scheduled_time: datetime  # When spraying will occur
    notes: Optional[str] = None
    wind_speed_mph: Optional[float] = None
    wind_direction: Optional[str] = None
    temperature_f: Optional[float] = None

class SprayReportResponse(BaseModel):
    report_id: str
    status: str
    message: str
    nearby_schools: int
    nearby_healthcare: int
    drift_risk: str

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = "geosync-salt"  # In production, use unique salt per user
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def create_token(farmer_id: int, email: str) -> str:
    """Create JWT token"""
    payload = {
        "farmer_id": farmer_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify JWT token and return payload"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_nearby_sensitive_locations(lat: float, lon: float, radius_km: float = 2.0) -> dict:
    """Check for schools/hospitals near spray location"""
    from app.data.sensitive_locations import get_all_sensitive_locations
    import math

    locations = get_all_sensitive_locations()
    schools = []
    healthcare = []

    for loc in locations:
        # Haversine distance
        R = 6371
        lat1, lat2 = math.radians(lat), math.radians(loc["lat"])
        dlat = math.radians(loc["lat"] - lat)
        dlon = math.radians(loc["lon"] - lon)
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist = R * c

        if dist <= radius_km:
            if loc["category"] == "school":
                schools.append({**loc, "distance_km": round(dist, 2)})
            elif loc["category"] == "healthcare":
                healthcare.append({**loc, "distance_km": round(dist, 2)})

    return {
        "schools": sorted(schools, key=lambda x: x["distance_km"]),
        "healthcare": sorted(healthcare, key=lambda x: x["distance_km"])
    }

# ==================== DATABASE SETUP ====================

def init_farmer_tables():
    """Create farmer-related tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()

    # Farmers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            farm_name VARCHAR(255) NOT NULL,
            owner_name VARCHAR(255) NOT NULL,
            county VARCHAR(100) NOT NULL,
            farm_size VARCHAR(50),
            primary_crops TEXT,
            phone VARCHAR(50),
            address TEXT,
            lat DECIMAL(10, 6),
            lon DECIMAL(10, 6),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT FALSE,
            active BOOLEAN DEFAULT TRUE
        )
    """)

    # Spray reports table
    # Note: Farmer-submitted reports are separate from official PUR data.
    # verification_status tracks whether this report has been matched with official records.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spray_reports (
            id SERIAL PRIMARY KEY,
            report_id VARCHAR(50) UNIQUE NOT NULL,
            farmer_id INTEGER REFERENCES farmers(id),
            chemical_name VARCHAR(255) NOT NULL,
            chemical_type VARCHAR(100),
            lbs_applied DECIMAL(12, 4),
            acres_treated DECIMAL(10, 2),
            application_method VARCHAR(50),
            target_crop VARCHAR(100),
            field_name VARCHAR(255),
            lat DECIMAL(10, 6) NOT NULL,
            lon DECIMAL(10, 6) NOT NULL,
            scheduled_time TIMESTAMP NOT NULL,
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'scheduled',
            verification_status VARCHAR(50) DEFAULT 'farmer_reported',
            notes TEXT,
            wind_speed_mph DECIMAL(5, 2),
            wind_direction VARCHAR(10),
            temperature_f DECIMAL(5, 2),
            nearby_schools INTEGER DEFAULT 0,
            nearby_healthcare INTEGER DEFAULT 0,
            drift_risk VARCHAR(50),
            data_source VARCHAR(50) DEFAULT 'farmer_portal'
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

# Initialize tables on module load
try:
    init_farmer_tables()
except:
    pass  # Tables might already exist or DB not available

# ==================== ENDPOINTS ====================

@router.post("/farmers/register")
async def register_farmer(farmer: FarmerRegister):
    """
    Register a new farmer account

    Required for reporting spray activities.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if email exists
    cursor.execute("SELECT id FROM farmers WHERE email = %s", (farmer.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create farmer
    password_hash = hash_password(farmer.password)

    cursor.execute("""
        INSERT INTO farmers (email, password_hash, farm_name, owner_name, county,
                            farm_size, primary_crops, phone, address, lat, lon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        farmer.email, password_hash, farmer.farm_name, farmer.owner_name,
        farmer.county.upper(), farmer.farm_size.value, farmer.primary_crops,
        farmer.phone, farmer.address, farmer.lat, farmer.lon
    ))

    farmer_id = cursor.fetchone()["id"]
    conn.commit()
    cursor.close()
    conn.close()

    # Generate token
    token = create_token(farmer_id, farmer.email)

    return {
        "success": True,
        "message": "Registration successful",
        "farmer_id": farmer_id,
        "token": token,
        "farm_name": farmer.farm_name
    }

@router.post("/farmers/login")
async def login_farmer(credentials: FarmerLogin):
    """
    Login to farmer portal

    Returns JWT token for authenticated requests.
    """
    conn = get_connection()
    cursor = conn.cursor()

    password_hash = hash_password(credentials.password)

    cursor.execute("""
        SELECT id, farm_name, owner_name, county, active
        FROM farmers
        WHERE email = %s AND password_hash = %s
    """, (credentials.email, password_hash))

    farmer = cursor.fetchone()
    cursor.close()
    conn.close()

    if not farmer:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not farmer["active"]:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_token(farmer["id"], credentials.email)

    return {
        "success": True,
        "token": token,
        "farmer": {
            "id": farmer["id"],
            "farm_name": farmer["farm_name"],
            "owner_name": farmer["owner_name"],
            "county": farmer["county"]
        }
    }

@router.get("/farmers/me")
async def get_farmer_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current farmer's profile"""
    payload = verify_token(credentials)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, email, farm_name, owner_name, county, farm_size,
               primary_crops, phone, address, lat, lon, created_at, verified
        FROM farmers WHERE id = %s
    """, (payload["farmer_id"],))

    farmer = cursor.fetchone()
    cursor.close()
    conn.close()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    return dict(farmer)

@router.post("/farmers/spray-report")
async def submit_spray_report(
    report: SprayReport,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Submit a spray report BEFORE application

    This is the core of real-time reporting:
    1. Farmer submits what they're about to spray
    2. System checks for nearby schools/hospitals
    3. Calculates drift risk
    4. Broadcasts to public dashboard immediately
    """
    payload = verify_token(credentials)

    # Generate unique report ID
    report_id = f"SR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"

    # Check nearby sensitive locations
    nearby = check_nearby_sensitive_locations(report.lat, report.lon, radius_km=2.0)
    schools_count = len(nearby["schools"])
    healthcare_count = len(nearby["healthcare"])

    # Calculate drift risk
    wind_speed = report.wind_speed_mph or 5
    if wind_speed > 10 or schools_count > 2:
        drift_risk = "high"
    elif wind_speed > 6 or schools_count > 0:
        drift_risk = "medium"
    else:
        drift_risk = "low"

    # Get farmer info
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT farm_name, county FROM farmers WHERE id = %s", (payload["farmer_id"],))
    farmer = cursor.fetchone()

    # Save report
    cursor.execute("""
        INSERT INTO spray_reports (
            report_id, farmer_id, chemical_name, chemical_type, lbs_applied,
            acres_treated, application_method, target_crop, field_name,
            lat, lon, scheduled_time, notes, wind_speed_mph, wind_direction,
            temperature_f, nearby_schools, nearby_healthcare, drift_risk
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        report_id, payload["farmer_id"], report.chemical_name, report.chemical_type,
        report.lbs_applied, report.acres_treated, report.application_method,
        report.target_crop, report.field_name, report.lat, report.lon,
        report.scheduled_time, report.notes, report.wind_speed_mph,
        report.wind_direction, report.temperature_f, schools_count,
        healthcare_count, drift_risk
    ))

    conn.commit()
    cursor.close()
    conn.close()

    # Broadcast to dashboard via WebSocket
    # Note: All farmer-submitted data is labeled as "farmer_reported" until verified
    # against official PUR records. This maintains data credibility.
    event = {
        "id": report_id,
        "timestamp": datetime.now().isoformat(),
        "type": "farmer_report",
        "source": "farmer_portal",
        "data_source": "farmer_reported",  # Clearly labeled - not official PUR data
        "verification_status": "farmer_reported",  # Pending verification against official records

        "site_name": farmer["farm_name"] if farmer else "Unknown Farm",
        "lat": report.lat,
        "lon": report.lon,
        "county": farmer["county"] if farmer else "UNKNOWN",
        "crop": report.target_crop,

        "chemical": report.chemical_name,
        "chemical_type": report.chemical_type,
        "lbs_applied": report.lbs_applied,
        "acres_treated": report.acres_treated,
        "application_rate": round(report.lbs_applied / report.acres_treated, 2) if report.acres_treated else 0,

        "scheduled_time": report.scheduled_time.isoformat(),
        "application_method": report.application_method,

        "weather": {
            "wind_speed_mph": report.wind_speed_mph or 0,
            "wind_direction": report.wind_direction or "Unknown",
            "temperature_f": report.temperature_f or 0
        },

        "nearby_sensitive_locations": nearby["schools"][:3] + nearby["healthcare"][:2],
        "schools_in_drift_zone": schools_count,
        "healthcare_in_drift_zone": healthcare_count,
        "alert_level": "critical" if drift_risk == "high" else drift_risk,
        "drift_risk": drift_risk
    }

    # Broadcast to all connected clients
    await manager.broadcast({
        "type": "new_spray_event",
        "event": event
    })

    return {
        "success": True,
        "report_id": report_id,
        "status": "scheduled",
        "message": f"Spray report submitted. {schools_count} school(s) and {healthcare_count} healthcare facility(ies) within 2km.",
        "nearby_schools": schools_count,
        "nearby_healthcare": healthcare_count,
        "drift_risk": drift_risk,
        "warnings": [
            f"⚠️ {s['name']} is {s['distance_km']}km away" for s in nearby["schools"][:3]
        ] if schools_count > 0 else []
    }

@router.get("/farmers/my-reports")
async def get_my_reports(
    limit: int = Query(50, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get farmer's spray report history"""
    payload = verify_token(credentials)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT report_id, chemical_name, chemical_type, lbs_applied, acres_treated,
               application_method, target_crop, field_name, lat, lon,
               scheduled_time, reported_at, status, drift_risk,
               nearby_schools, nearby_healthcare
        FROM spray_reports
        WHERE farmer_id = %s
        ORDER BY reported_at DESC
        LIMIT %s
    """, (payload["farmer_id"], limit))

    reports = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "count": len(reports),
        "reports": [dict(r) for r in reports]
    }

@router.get("/farmers/reports/recent")
async def get_recent_reports(
    county: Optional[str] = Query(None),
    hours: int = Query(24, le=168)
):
    """
    Get recent spray reports (public endpoint)

    This powers the real-time dashboard.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT sr.report_id, sr.chemical_name, sr.chemical_type, sr.lbs_applied,
               sr.acres_treated, sr.application_method, sr.target_crop,
               sr.lat, sr.lon, sr.scheduled_time, sr.reported_at, sr.drift_risk,
               sr.nearby_schools, sr.nearby_healthcare,
               f.farm_name, f.county
        FROM spray_reports sr
        JOIN farmers f ON sr.farmer_id = f.id
        WHERE sr.reported_at >= NOW() - INTERVAL '%s hours'
    """
    params = [hours]

    if county:
        query += " AND f.county = %s"
        params.append(county.upper())

    query += " ORDER BY sr.reported_at DESC LIMIT 100"

    cursor.execute(query, params)
    reports = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "count": len(reports),
        "time_range_hours": hours,
        "reports": [dict(r) for r in reports]
    }

@router.get("/farmers/stats")
async def get_farmer_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get farmer's statistics"""
    payload = verify_token(credentials)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_reports,
            SUM(lbs_applied) as total_lbs,
            SUM(acres_treated) as total_acres,
            COUNT(DISTINCT chemical_name) as unique_chemicals,
            MIN(scheduled_time) as first_report,
            MAX(scheduled_time) as last_report
        FROM spray_reports
        WHERE farmer_id = %s
    """, (payload["farmer_id"],))

    stats = cursor.fetchone()
    cursor.close()
    conn.close()

    return {
        "total_reports": stats["total_reports"],
        "total_lbs_applied": float(stats["total_lbs"]) if stats["total_lbs"] else 0,
        "total_acres_treated": float(stats["total_acres"]) if stats["total_acres"] else 0,
        "unique_chemicals": stats["unique_chemicals"],
        "reporting_since": stats["first_report"].isoformat() if stats["first_report"] else None,
        "last_report": stats["last_report"].isoformat() if stats["last_report"] else None
    }
