from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from app.database import get_connection

router = APIRouter()

# California county centroids (lat, lon)
COUNTY_COORDS = {
    "01": {"name": "ALAMEDA", "lat": 37.6017, "lon": -121.7195},
    "02": {"name": "ALPINE", "lat": 38.5941, "lon": -119.8815},
    "03": {"name": "AMADOR", "lat": 38.4466, "lon": -120.6538},
    "04": {"name": "BUTTE", "lat": 39.6670, "lon": -121.6008},
    "05": {"name": "CALAVERAS", "lat": 38.1963, "lon": -120.5544},
    "06": {"name": "COLUSA", "lat": 39.1776, "lon": -122.2375},
    "07": {"name": "CONTRA COSTA", "lat": 37.9193, "lon": -121.9277},
    "08": {"name": "DEL NORTE", "lat": 41.7432, "lon": -123.8978},
    "09": {"name": "EL DORADO", "lat": 38.7786, "lon": -120.5246},
    "10": {"name": "FRESNO", "lat": 36.7378, "lon": -119.7871},
    "11": {"name": "GLENN", "lat": 39.5983, "lon": -122.3911},
    "12": {"name": "HUMBOLDT", "lat": 40.7450, "lon": -123.8695},
    "13": {"name": "IMPERIAL", "lat": 33.0114, "lon": -115.4734},
    "14": {"name": "INYO", "lat": 36.5111, "lon": -117.4109},
    "15": {"name": "KERN", "lat": 35.3433, "lon": -118.7278},
    "16": {"name": "KINGS", "lat": 36.0988, "lon": -119.8815},
    "17": {"name": "LAKE", "lat": 39.0994, "lon": -122.7531},
    "18": {"name": "LASSEN", "lat": 40.6739, "lon": -120.5946},
    "19": {"name": "LOS ANGELES", "lat": 34.3083, "lon": -118.2280},
    "20": {"name": "MADERA", "lat": 37.2181, "lon": -119.7631},
    "21": {"name": "MARIN", "lat": 38.0834, "lon": -122.7633},
    "22": {"name": "MARIPOSA", "lat": 37.5848, "lon": -119.9665},
    "23": {"name": "MENDOCINO", "lat": 39.4380, "lon": -123.3918},
    "24": {"name": "MERCED", "lat": 37.1948, "lon": -120.7178},
    "25": {"name": "MODOC", "lat": 41.5885, "lon": -120.7254},
    "26": {"name": "MONO", "lat": 37.9391, "lon": -118.8864},
    "27": {"name": "MONTEREY", "lat": 36.2400, "lon": -121.3103},
    "28": {"name": "NAPA", "lat": 38.5025, "lon": -122.2654},
    "29": {"name": "NEVADA", "lat": 39.3013, "lon": -120.7688},
    "30": {"name": "ORANGE", "lat": 33.7175, "lon": -117.8311},
    "31": {"name": "PLACER", "lat": 39.0916, "lon": -120.8039},
    "32": {"name": "PLUMAS", "lat": 40.0037, "lon": -120.8388},
    "33": {"name": "RIVERSIDE", "lat": 33.7437, "lon": -115.9930},
    "34": {"name": "SACRAMENTO", "lat": 38.4500, "lon": -121.3400},
    "35": {"name": "SAN BENITO", "lat": 36.6058, "lon": -121.0750},
    "36": {"name": "SAN BERNARDINO", "lat": 34.8414, "lon": -116.1781},
    "37": {"name": "SAN DIEGO", "lat": 33.0214, "lon": -116.7680},
    "38": {"name": "SAN FRANCISCO", "lat": 37.7749, "lon": -122.4194},
    "39": {"name": "SAN JOAQUIN", "lat": 37.9349, "lon": -121.2713},
    "40": {"name": "SAN LUIS OBISPO", "lat": 35.3870, "lon": -120.4520},
    "41": {"name": "SAN MATEO", "lat": 37.4337, "lon": -122.4014},
    "42": {"name": "SANTA BARBARA", "lat": 34.5362, "lon": -120.0385},
    "43": {"name": "SANTA CLARA", "lat": 37.2939, "lon": -121.6951},
    "44": {"name": "SANTA CRUZ", "lat": 37.0454, "lon": -122.0580},
    "45": {"name": "SHASTA", "lat": 40.7637, "lon": -122.0405},
    "46": {"name": "SIERRA", "lat": 39.5769, "lon": -120.5161},
    "47": {"name": "SISKIYOU", "lat": 41.5926, "lon": -122.5405},
    "48": {"name": "SOLANO", "lat": 38.2670, "lon": -121.9400},
    "49": {"name": "SONOMA", "lat": 38.5254, "lon": -122.9277},
    "50": {"name": "STANISLAUS", "lat": 37.5591, "lon": -120.9979},
    "51": {"name": "SUTTER", "lat": 39.0346, "lon": -121.6947},
    "52": {"name": "TEHAMA", "lat": 40.1255, "lon": -122.2342},
    "53": {"name": "TRINITY", "lat": 40.6506, "lon": -123.1119},
    "54": {"name": "TULARE", "lat": 36.2281, "lon": -118.7815},
    "55": {"name": "TUOLUMNE", "lat": 38.0279, "lon": -119.9544},
    "56": {"name": "VENTURA", "lat": 34.3586, "lon": -119.1391},
    "57": {"name": "YOLO", "lat": 38.6869, "lon": -121.9012},
    "58": {"name": "YUBA", "lat": 39.2677, "lon": -121.3502},
}

class SprayRecord(BaseModel):
    id: int
    year: Optional[int]
    applic_dt: Optional[date]
    county_cd: Optional[str]
    county: Optional[str]
    chemname: Optional[str]
    chem_code: Optional[int]
    lbs_chm_used: Optional[float]
    acre_treated: Optional[float]
    site_name: Optional[str]
    comtrs: Optional[str]

class SprayStats(BaseModel):
    total_records: int
    total_lbs_applied: float
    total_acres_treated: float
    top_chemicals: List[dict]
    top_counties: List[dict]

@router.get("/sprays", response_model=List[SprayRecord])
def get_sprays(
    year: Optional[int] = Query(None, ge=2014, le=2023),
    county: Optional[str] = Query(None),
    chem_code: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Query spray records with filters"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT id, year, applic_dt, county_cd, county, chemname, chem_code, lbs_chm_used, acre_treated, site_name, comtrs FROM sprays WHERE 1=1"
    params = []

    if year:
        query += " AND year = %s"
        params.append(year)
    if county:
        query += " AND (county ILIKE %s OR county_cd = %s)"
        params.extend([f"%{county}%", county])
    if chem_code:
        query += " AND chem_code = %s"
        params.append(chem_code)
    if start_date:
        query += " AND applic_dt >= %s"
        params.append(start_date)
    if end_date:
        query += " AND applic_dt <= %s"
        params.append(end_date)

    query += " ORDER BY applic_dt DESC NULLS LAST LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [SprayRecord(**row) for row in results]

@router.get("/sprays/stats", response_model=SprayStats)
def get_spray_stats(
    year: Optional[int] = Query(None, ge=2014, le=2023),
    county: Optional[str] = Query(None)
):
    """Get aggregated statistics for spray data"""
    conn = get_connection()
    cursor = conn.cursor()

    where_clause = "WHERE 1=1"
    params = []

    if year:
        where_clause += " AND year = %s"
        params.append(year)
    if county:
        where_clause += " AND (county ILIKE %s OR county_cd = %s)"
        params.extend([f"%{county}%", county])

    # Total stats
    cursor.execute(f"""
        SELECT
            COUNT(*) as total_records,
            COALESCE(SUM(lbs_chm_used), 0) as total_lbs,
            COALESCE(SUM(acre_treated), 0) as total_acres
        FROM sprays {where_clause}
    """, params)
    totals = cursor.fetchone()

    # Top chemicals
    cursor.execute(f"""
        SELECT chemname, chem_code, SUM(lbs_chm_used) as total_lbs
        FROM sprays {where_clause} AND chemname IS NOT NULL
        GROUP BY chemname, chem_code
        ORDER BY total_lbs DESC NULLS LAST
        LIMIT 10
    """, params)
    top_chemicals = [{"name": r["chemname"], "code": r["chem_code"], "lbs": r["total_lbs"]} for r in cursor.fetchall()]

    # Top counties
    cursor.execute(f"""
        SELECT county, county_cd, SUM(lbs_chm_used) as total_lbs
        FROM sprays {where_clause} AND county IS NOT NULL
        GROUP BY county, county_cd
        ORDER BY total_lbs DESC NULLS LAST
        LIMIT 10
    """, params)
    top_counties = [{"name": r["county"], "code": r["county_cd"], "lbs": r["total_lbs"]} for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    return SprayStats(
        total_records=totals["total_records"],
        total_lbs_applied=totals["total_lbs"] or 0,
        total_acres_treated=totals["total_acres"] or 0,
        top_chemicals=top_chemicals,
        top_counties=top_counties
    )

@router.get("/sprays/years")
def get_available_years():
    """Get list of years with data"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT year, COUNT(*) as record_count FROM sprays GROUP BY year ORDER BY year")
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"year": r["year"], "records": r["record_count"]} for r in results]

@router.get("/sprays/counties")
def get_counties(year: Optional[int] = Query(None)):
    """Get list of counties with spray data"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT DISTINCT county, county_cd FROM sprays WHERE county IS NOT NULL"
    params = []

    if year:
        query += " AND year = %s"
        params.append(year)

    query += " ORDER BY county"

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{"name": r["county"], "code": r["county_cd"]} for r in results]

@router.get("/sprays/heatmap")
def get_county_heatmap(year: Optional[int] = Query(None)):
    """Get spray totals by county with coordinates for map visualization"""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT county_cd, SUM(lbs_chm_used) as total_lbs, COUNT(*) as spray_count
        FROM sprays WHERE county_cd IS NOT NULL
    """
    params = []

    if year:
        query += " AND year = %s"
        params.append(year)

    query += " GROUP BY county_cd ORDER BY total_lbs DESC"

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    features = []
    for r in results:
        county_cd = r["county_cd"]
        if county_cd in COUNTY_COORDS:
            coords = COUNTY_COORDS[county_cd]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [coords["lon"], coords["lat"]]
                },
                "properties": {
                    "county_cd": county_cd,
                    "county": coords["name"],
                    "total_lbs": float(r["total_lbs"] or 0),
                    "spray_count": r["spray_count"]
                }
            })

    return {"type": "FeatureCollection", "features": features}
