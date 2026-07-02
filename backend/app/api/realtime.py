"""
Real-time spray event notifications via WebSocket
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import asyncio
import random
import math

router = APIRouter()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.spray_events: List[Dict] = []  # Recent spray events

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    def add_spray_event(self, event: dict):
        """Add a spray event and keep last 100"""
        self.spray_events.insert(0, event)
        self.spray_events = self.spray_events[:100]

manager = ConnectionManager()

# California agricultural regions with realistic spray site coordinates
SPRAY_SITES = [
    # Fresno County - Central Valley agricultural areas
    {"name": "West Fresno Vineyards", "lat": 36.7378, "lon": -119.9200, "county": "FRESNO", "crop": "grapes"},
    {"name": "Selma Orchards", "lat": 36.5708, "lon": -119.6120, "county": "FRESNO", "crop": "stone_fruit"},
    {"name": "Reedley Farms", "lat": 36.5969, "lon": -119.4503, "county": "FRESNO", "crop": "citrus"},
    {"name": "Kingsburg Vineyards", "lat": 36.5144, "lon": -119.5539, "county": "FRESNO", "crop": "grapes"},
    {"name": "Sanger Orchards", "lat": 36.7080, "lon": -119.5560, "county": "FRESNO", "crop": "almonds"},
    {"name": "Firebaugh Cotton Fields", "lat": 36.8586, "lon": -120.4561, "county": "FRESNO", "crop": "cotton"},
    {"name": "Kerman Tomato Fields", "lat": 36.7266, "lon": -120.0597, "county": "FRESNO", "crop": "tomatoes"},

    # Kern County
    {"name": "Bakersfield Citrus Grove", "lat": 35.4200, "lon": -119.1500, "county": "KERN", "crop": "citrus"},
    {"name": "Arvin Vineyards", "lat": 35.2092, "lon": -118.8283, "county": "KERN", "crop": "grapes"},
    {"name": "McFarland Almond Orchards", "lat": 35.6800, "lon": -119.2300, "county": "KERN", "crop": "almonds"},
    {"name": "Wasco Almond Farm", "lat": 35.5942, "lon": -119.4100, "county": "KERN", "crop": "almonds"},
    {"name": "Shafter Cotton Fields", "lat": 35.5006, "lon": -119.2800, "county": "KERN", "crop": "cotton"},
    {"name": "Delano Table Grapes", "lat": 35.7686, "lon": -119.2500, "county": "KERN", "crop": "grapes"},

    # Tulare County
    {"name": "Visalia Dairy Farms", "lat": 36.3302, "lon": -119.3500, "county": "TULARE", "crop": "alfalfa"},
    {"name": "Tulare Citrus Grove", "lat": 36.2078, "lon": -119.4000, "county": "TULARE", "crop": "citrus"},
    {"name": "Porterville Orchards", "lat": 36.0652, "lon": -119.0168, "county": "TULARE", "crop": "oranges"},
    {"name": "Earlimart Vineyards", "lat": 35.8833, "lon": -119.2700, "county": "TULARE", "crop": "grapes"},

    # Monterey County
    {"name": "Salinas Lettuce Fields", "lat": 36.6777, "lon": -121.6555, "county": "MONTEREY", "crop": "lettuce"},
    {"name": "Gonzales Vegetable Farm", "lat": 36.5064, "lon": -121.4500, "county": "MONTEREY", "crop": "vegetables"},
    {"name": "King City Vineyards", "lat": 36.2128, "lon": -121.1300, "county": "MONTEREY", "crop": "grapes"},
    {"name": "Greenfield Lettuce", "lat": 36.3208, "lon": -121.2500, "county": "MONTEREY", "crop": "lettuce"},

    # Imperial County
    {"name": "El Centro Alfalfa", "lat": 32.7920, "lon": -115.5630, "county": "IMPERIAL", "crop": "alfalfa"},
    {"name": "Brawley Sugar Beets", "lat": 32.9786, "lon": -115.5300, "county": "IMPERIAL", "crop": "sugar_beets"},
    {"name": "Calexico Vegetables", "lat": 32.6789, "lon": -115.5000, "county": "IMPERIAL", "crop": "vegetables"},

    # San Joaquin County
    {"name": "Stockton Asparagus", "lat": 37.9577, "lon": -121.2900, "county": "SAN JOAQUIN", "crop": "asparagus"},
    {"name": "Lodi Vineyards", "lat": 38.1341, "lon": -121.2700, "county": "SAN JOAQUIN", "crop": "grapes"},
    {"name": "Tracy Tomatoes", "lat": 37.7397, "lon": -121.4300, "county": "SAN JOAQUIN", "crop": "tomatoes"},

    # Ventura County
    {"name": "Oxnard Strawberry Fields", "lat": 34.2011, "lon": -119.1800, "county": "VENTURA", "crop": "strawberries"},
    {"name": "Santa Paula Citrus", "lat": 34.3542, "lon": -119.0600, "county": "VENTURA", "crop": "citrus"},
    {"name": "Fillmore Orchards", "lat": 34.3992, "lon": -118.9200, "county": "VENTURA", "crop": "avocados"},
]

# Common pesticides with toxicity levels
PESTICIDES = [
    {"name": "Chlorpyrifos", "toxicity": "high", "epa_category": "II", "type": "insecticide"},
    {"name": "Glyphosate", "toxicity": "medium", "epa_category": "III", "type": "herbicide"},
    {"name": "Malathion", "toxicity": "medium", "epa_category": "III", "type": "insecticide"},
    {"name": "Sulfur", "toxicity": "low", "epa_category": "IV", "type": "fungicide"},
    {"name": "Paraquat", "toxicity": "high", "epa_category": "I", "type": "herbicide"},
    {"name": "Methyl Bromide", "toxicity": "high", "epa_category": "I", "type": "fumigant"},
    {"name": "Imidacloprid", "toxicity": "medium", "epa_category": "II", "type": "insecticide"},
    {"name": "Copper Hydroxide", "toxicity": "low", "epa_category": "III", "type": "fungicide"},
    {"name": "Abamectin", "toxicity": "high", "epa_category": "II", "type": "insecticide"},
    {"name": "Pyrethrin", "toxicity": "low", "epa_category": "III", "type": "insecticide"},
]

def calculate_drift_zone(wind_speed: float, wind_direction: float, lbs_applied: float) -> dict:
    """Calculate drift plume based on wind conditions"""
    # Drift distance increases with wind speed and application amount
    base_distance = 0.5  # km base drift
    drift_distance = base_distance + (wind_speed * 0.1) + (lbs_applied / 1000 * 0.05)
    drift_distance = min(drift_distance, 5.0)  # Max 5km drift

    # Plume width spreads with distance
    plume_width = drift_distance * 0.4

    return {
        "distance_km": round(drift_distance, 2),
        "width_km": round(plume_width, 2),
        "direction": wind_direction,
        "concentration_decay": "gaussian"
    }

def check_nearby_sensitive_locations(lat: float, lon: float, radius_km: float = 2.0) -> List[Dict]:
    """Check for schools/hospitals within drift zone"""
    from app.data.sensitive_locations import get_all_sensitive_locations

    locations = get_all_sensitive_locations()
    nearby = []

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
            nearby.append({
                **loc,
                "distance_km": round(dist, 2)
            })

    return sorted(nearby, key=lambda x: x["distance_km"])

def generate_spray_event() -> dict:
    """Generate a realistic spray event"""
    site = random.choice(SPRAY_SITES)
    pesticide = random.choice(PESTICIDES)

    # Add some randomness to location
    lat = site["lat"] + random.uniform(-0.02, 0.02)
    lon = site["lon"] + random.uniform(-0.02, 0.02)

    # Weather conditions
    wind_speed = random.uniform(2, 15)  # mph
    wind_direction = random.uniform(0, 360)  # degrees
    temperature = random.uniform(65, 95)  # F
    humidity = random.uniform(30, 70)  # %

    # Application details
    lbs_applied = random.uniform(50, 2000)
    acres_treated = random.uniform(10, 500)

    # Calculate drift zone
    drift = calculate_drift_zone(wind_speed, wind_direction, lbs_applied)

    # Check for nearby sensitive locations
    nearby_sensitive = check_nearby_sensitive_locations(lat, lon, drift["distance_km"])

    # Determine alert level
    alert_level = "low"
    if pesticide["toxicity"] == "high" and len(nearby_sensitive) > 0:
        alert_level = "critical"
    elif pesticide["toxicity"] == "high" or len(nearby_sensitive) > 2:
        alert_level = "high"
    elif pesticide["toxicity"] == "medium" and len(nearby_sensitive) > 0:
        alert_level = "medium"

    event = {
        "id": f"spray_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
        "timestamp": datetime.now().isoformat(),
        "type": "spray_event",

        # Location
        "site_name": site["name"],
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "county": site["county"],
        "crop": site["crop"],

        # Chemical
        "chemical": pesticide["name"],
        "chemical_type": pesticide["type"],
        "toxicity": pesticide["toxicity"],
        "epa_category": pesticide["epa_category"],

        # Application
        "lbs_applied": round(lbs_applied, 1),
        "acres_treated": round(acres_treated, 1),
        "application_rate": round(lbs_applied / acres_treated, 2),

        # Weather
        "weather": {
            "wind_speed_mph": round(wind_speed, 1),
            "wind_direction": round(wind_direction, 0),
            "temperature_f": round(temperature, 0),
            "humidity_pct": round(humidity, 0)
        },

        # Drift prediction
        "drift_zone": drift,

        # Risk assessment
        "nearby_sensitive_locations": nearby_sensitive[:5],  # Top 5 nearest
        "alert_level": alert_level,
        "schools_in_drift_zone": len([l for l in nearby_sensitive if l["category"] == "school"]),
        "healthcare_in_drift_zone": len([l for l in nearby_sensitive if l["category"] == "healthcare"])
    }

    return event

@router.websocket("/ws/sprays")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time spray updates"""
    await manager.connect(websocket)

    try:
        # Send recent events on connect
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to GeoSync real-time feed",
            "recent_events": manager.spray_events[:10]
        })

        while True:
            # Wait for messages from client (like filter updates)
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                # Handle client messages (filters, etc.)
                if data.get("type") == "subscribe":
                    await websocket.send_json({"type": "subscribed", "filters": data.get("filters", {})})
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/spray-events/recent")
def get_recent_events(limit: int = Query(20, le=100)):
    """Get recent spray events"""
    return {
        "count": len(manager.spray_events[:limit]),
        "events": manager.spray_events[:limit]
    }

@router.get("/spray-events/sites")
def get_spray_sites():
    """Get all known spray sites for map display"""
    return {
        "count": len(SPRAY_SITES),
        "sites": SPRAY_SITES
    }

@router.post("/spray-events/simulate")
async def simulate_spray_event():
    """Simulate a new spray event (for demo/testing)"""
    event = generate_spray_event()
    manager.add_spray_event(event)

    # Broadcast to all connected clients
    await manager.broadcast({
        "type": "new_spray_event",
        "event": event
    })

    return event

@router.post("/spray-events/report")
async def report_spray_event(
    lat: float = Query(...),
    lon: float = Query(...),
    chemical: str = Query(...),
    lbs_applied: float = Query(...),
    county: str = Query(None),
    notes: str = Query(None)
):
    """Report a spray event (from field reporters, sensors, etc.)"""
    # Find matching pesticide info
    pesticide_info = next((p for p in PESTICIDES if p["name"].lower() == chemical.lower()),
                          {"name": chemical, "toxicity": "unknown", "epa_category": "Unknown", "type": "unknown"})

    # Generate wind data (would come from weather API in production)
    wind_speed = random.uniform(2, 15)
    wind_direction = random.uniform(0, 360)

    drift = calculate_drift_zone(wind_speed, wind_direction, lbs_applied)
    nearby_sensitive = check_nearby_sensitive_locations(lat, lon, drift["distance_km"])

    event = {
        "id": f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
        "timestamp": datetime.now().isoformat(),
        "type": "reported_spray",
        "source": "field_report",

        "lat": lat,
        "lon": lon,
        "county": county or "UNKNOWN",

        "chemical": pesticide_info["name"],
        "chemical_type": pesticide_info["type"],
        "toxicity": pesticide_info["toxicity"],
        "epa_category": pesticide_info["epa_category"],

        "lbs_applied": lbs_applied,
        "notes": notes,

        "weather": {
            "wind_speed_mph": round(wind_speed, 1),
            "wind_direction": round(wind_direction, 0)
        },

        "drift_zone": drift,
        "nearby_sensitive_locations": nearby_sensitive[:5],
        "alert_level": "high" if len(nearby_sensitive) > 0 and pesticide_info["toxicity"] == "high" else "medium",
        "schools_in_drift_zone": len([l for l in nearby_sensitive if l["category"] == "school"]),
        "healthcare_in_drift_zone": len([l for l in nearby_sensitive if l["category"] == "healthcare"])
    }

    manager.add_spray_event(event)
    await manager.broadcast({
        "type": "new_spray_event",
        "event": event
    })

    return event

# Background task to simulate periodic spray events (for demo)
async def spray_simulator():
    """Simulates spray events for demo purposes"""
    while True:
        # Generate 1-3 events every 30-60 seconds during "active hours"
        await asyncio.sleep(random.uniform(30, 60))

        num_events = random.randint(1, 3)
        for _ in range(num_events):
            event = generate_spray_event()
            manager.add_spray_event(event)
            await manager.broadcast({
                "type": "new_spray_event",
                "event": event
            })
            await asyncio.sleep(random.uniform(1, 5))
