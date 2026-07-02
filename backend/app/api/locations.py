"""
Sensitive locations API - schools, hospitals, parks
"""

from fastapi import APIRouter, Query
from typing import Optional
import math

from app.data.sensitive_locations import (
    get_all_sensitive_locations,
    get_locations_by_county,
    get_locations_as_geojson
)
from app.database import get_connection

router = APIRouter()

@router.get("/locations")
def get_locations(
    county: Optional[str] = Query(None),
    category: Optional[str] = Query(None, description="school, healthcare, recreation")
):
    """Get sensitive locations as GeoJSON for map display"""
    return get_locations_as_geojson(county, category)

@router.get("/locations/schools")
def get_schools(county: Optional[str] = Query(None)):
    """Get schools as GeoJSON"""
    return get_locations_as_geojson(county, "school")

@router.get("/locations/proximity")
def check_proximity(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(5.0, description="Search radius in kilometers")
):
    """
    Find sensitive locations within radius of a point.
    Useful for checking what's near a spray site.
    """
    locations = get_all_sensitive_locations()
    nearby = []

    for loc in locations:
        dist = haversine_distance(lat, lon, loc["lat"], loc["lon"])
        if dist <= radius_km:
            nearby.append({
                **loc,
                "distance_km": round(dist, 2)
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return {
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "count": len(nearby),
        "locations": nearby
    }

@router.get("/locations/spray-exposure")
def get_spray_exposure(
    county: Optional[str] = Query(None),
    year: int = Query(2023),
    radius_km: float = Query(1.0, description="Radius around each location")
):
    """
    Analyze pesticide exposure risk for sensitive locations.
    Shows total lbs applied near schools, hospitals, etc.
    """
    locations = get_all_sensitive_locations()
    if county:
        locations = [loc for loc in locations if loc["county"].upper() == county.upper()]

    conn = get_connection()
    cursor = conn.cursor()

    results = []
    for loc in locations:
        # Get spray data near this location
        # Using county as proxy since we don't have exact spray coordinates
        cursor.execute("""
            SELECT
                SUM(lbs_chm_used) as total_lbs,
                COUNT(*) as spray_count,
                COUNT(DISTINCT chem_code) as chemical_count
            FROM sprays
            WHERE county = %s AND year = %s
        """, (loc["county"], year))

        row = cursor.fetchone()

        # Estimate exposure based on county total and area
        # This is simplified - real analysis would use exact coordinates
        county_total_lbs = float(row["total_lbs"] or 0)

        results.append({
            "name": loc["name"],
            "type": loc["type"],
            "category": loc["category"],
            "county": loc["county"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "county_total_lbs": county_total_lbs,
            "spray_events_in_county": row["spray_count"],
            "chemicals_used": row["chemical_count"],
            "risk_level": categorize_risk(county_total_lbs)
        })

    cursor.close()
    conn.close()

    # Sort by risk
    results.sort(key=lambda x: x["county_total_lbs"], reverse=True)
    return results

@router.get("/locations/at-risk")
def get_at_risk_locations(
    year: int = Query(2023),
    min_lbs: float = Query(1000000, description="Minimum county lbs to be considered at-risk")
):
    """
    Get sensitive locations in high-pesticide-use counties.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get high-use counties
    cursor.execute("""
        SELECT county, SUM(lbs_chm_used) as total_lbs
        FROM sprays
        WHERE year = %s AND county IS NOT NULL
        GROUP BY county
        HAVING SUM(lbs_chm_used) >= %s
        ORDER BY total_lbs DESC
    """, (year, min_lbs))

    high_use_counties = {row["county"]: float(row["total_lbs"]) for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    # Find locations in these counties
    locations = get_all_sensitive_locations()
    at_risk = []

    for loc in locations:
        if loc["county"] in high_use_counties:
            at_risk.append({
                **loc,
                "county_pesticide_lbs": high_use_counties[loc["county"]],
                "risk_level": categorize_risk(high_use_counties[loc["county"]])
            })

    # Sort by exposure
    at_risk.sort(key=lambda x: x["county_pesticide_lbs"], reverse=True)

    return {
        "year": year,
        "threshold_lbs": min_lbs,
        "high_use_counties": len(high_use_counties),
        "at_risk_locations": len(at_risk),
        "locations": at_risk
    }

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km"""
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def categorize_risk(lbs: float) -> str:
    """Categorize risk level based on pesticide lbs"""
    if lbs >= 10000000:
        return "very_high"
    elif lbs >= 5000000:
        return "high"
    elif lbs >= 1000000:
        return "medium"
    elif lbs >= 100000:
        return "low"
    else:
        return "minimal"
