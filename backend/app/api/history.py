"""
Spray History API - Actual historical spray events with dates

This provides REAL DATA from California's Pesticide Use Reports (PUR)
with actual application dates, chemicals, and quantities.
"""

from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, date

from app.database import get_connection

router = APIRouter()

@router.get("/history/county/{county}")
def get_county_spray_history(
    county: str,
    year: int = Query(2023),
    month: Optional[int] = Query(None, ge=1, le=12),
    limit: int = Query(100, le=1000),
    chemical: Optional[str] = Query(None)
):
    """
    Get actual spray history for a county with specific dates

    Returns individual spray events with:
    - Exact application date
    - Chemical name
    - Amount applied
    - Site information
    - Application method

    This is REAL DATA from California PUR records.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build query for actual spray events
    query = """
        SELECT
            applic_dt as application_date,
            chemname as chemical_name,
            lbs_chm_used as lbs_applied,
            acre_treated,
            site_name,
            aer_gnd_ind as application_method,
            prodchem_pct as concentration_pct,
            unit_treated
        FROM sprays
        WHERE UPPER(county) = %s AND year = %s
    """
    params = [county.upper(), year]

    if month:
        query += " AND EXTRACT(MONTH FROM applic_dt) = %s"
        params.append(month)

    if chemical:
        query += " AND UPPER(chemname) LIKE %s"
        params.append(f"%{chemical.upper()}%")

    query += " ORDER BY applic_dt DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    events = []
    for row in rows:
        app_date = row["application_date"]
        events.append({
            "date": app_date.strftime("%Y-%m-%d") if app_date else None,
            "date_formatted": app_date.strftime("%B %d, %Y") if app_date else "Unknown",
            "day_of_week": app_date.strftime("%A") if app_date else None,
            "chemical": row["chemical_name"],
            "lbs_applied": float(row["lbs_applied"]) if row["lbs_applied"] else 0,
            "acres_treated": float(row["acre_treated"]) if row["acre_treated"] else 0,
            "site": row["site_name"],
            "method": "Aerial" if row["application_method"] == "A" else "Ground",
            "concentration_pct": float(row["concentration_pct"]) if row["concentration_pct"] else 0
        })

    # Get summary stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_events,
            SUM(lbs_chm_used) as total_lbs,
            COUNT(DISTINCT chemname) as unique_chemicals,
            MIN(applic_dt) as earliest_date,
            MAX(applic_dt) as latest_date
        FROM sprays
        WHERE UPPER(county) = %s AND year = %s
    """, [county.upper(), year])

    summary = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "county": county.upper(),
        "year": year,
        "month": month,
        "summary": {
            "total_spray_events": summary["total_events"],
            "total_lbs_applied": float(summary["total_lbs"]) if summary["total_lbs"] else 0,
            "unique_chemicals": summary["unique_chemicals"],
            "date_range": {
                "earliest": summary["earliest_date"].strftime("%Y-%m-%d") if summary["earliest_date"] else None,
                "latest": summary["latest_date"].strftime("%Y-%m-%d") if summary["latest_date"] else None
            }
        },
        "events_returned": len(events),
        "events": events
    }

@router.get("/history/timeline/{county}")
def get_spray_timeline(
    county: str,
    year: int = Query(2023)
):
    """
    Get daily spray activity timeline for a county

    Shows spray intensity by day - useful for parents to see
    which days had heavy spray activity.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Daily aggregation
    cursor.execute("""
        SELECT
            applic_dt as spray_date,
            COUNT(*) as spray_events,
            SUM(lbs_chm_used) as total_lbs,
            COUNT(DISTINCT chemname) as chemicals_used,
            array_agg(DISTINCT chemname) as chemical_list
        FROM sprays
        WHERE UPPER(county) = %s AND year = %s AND applic_dt IS NOT NULL
        GROUP BY applic_dt
        ORDER BY applic_dt DESC
    """, [county.upper(), year])

    rows = cursor.fetchall()

    timeline = []
    for row in rows:
        spray_date = row["spray_date"]
        total_lbs = float(row["total_lbs"]) if row["total_lbs"] else 0

        # Categorize intensity
        if total_lbs > 100000:
            intensity = "very_high"
        elif total_lbs > 50000:
            intensity = "high"
        elif total_lbs > 10000:
            intensity = "medium"
        else:
            intensity = "low"

        timeline.append({
            "date": spray_date.strftime("%Y-%m-%d"),
            "date_formatted": spray_date.strftime("%B %d, %Y"),
            "day_of_week": spray_date.strftime("%A"),
            "spray_events": row["spray_events"],
            "total_lbs": total_lbs,
            "chemicals_used": row["chemicals_used"],
            "top_chemicals": row["chemical_list"][:5] if row["chemical_list"] else [],
            "intensity": intensity
        })

    # Monthly summary
    cursor.execute("""
        SELECT
            EXTRACT(MONTH FROM applic_dt) as month,
            COUNT(*) as events,
            SUM(lbs_chm_used) as total_lbs
        FROM sprays
        WHERE UPPER(county) = %s AND year = %s AND applic_dt IS NOT NULL
        GROUP BY EXTRACT(MONTH FROM applic_dt)
        ORDER BY month
    """, [county.upper(), year])

    months = cursor.fetchall()
    monthly = {}
    month_names = ["", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    for m in months:
        month_num = int(m["month"])
        monthly[month_names[month_num]] = {
            "events": m["events"],
            "total_lbs": float(m["total_lbs"]) if m["total_lbs"] else 0
        }

    cursor.close()
    conn.close()

    return {
        "county": county.upper(),
        "year": year,
        "days_with_spraying": len(timeline),
        "monthly_summary": monthly,
        "daily_timeline": timeline[:365]  # Limit to one year
    }

@router.get("/history/recent-near-schools")
def get_recent_sprays_near_schools(
    county: str = Query(...),
    year: int = Query(2023),
    days: int = Query(30, description="Look back this many days from latest data")
):
    """
    Get recent spray events in a county - critical for parent awareness

    Returns the most recent spray events, organized by date,
    showing what chemicals were applied near schools.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get the most recent spray date to calculate "recent"
    cursor.execute("""
        SELECT MAX(applic_dt) as latest
        FROM sprays
        WHERE UPPER(county) = %s AND year = %s
    """, [county.upper(), year])

    latest_row = cursor.fetchone()
    latest_date = latest_row["latest"]

    if not latest_date:
        cursor.close()
        conn.close()
        return {"error": "No spray data found for this county/year"}

    # Get recent events
    cursor.execute("""
        SELECT
            applic_dt as spray_date,
            chemname as chemical,
            SUM(lbs_chm_used) as total_lbs,
            COUNT(*) as applications,
            site_name
        FROM sprays
        WHERE UPPER(county) = %s
          AND year = %s
          AND applic_dt >= %s - INTERVAL '%s days'
        GROUP BY applic_dt, chemname, site_name
        ORDER BY applic_dt DESC, total_lbs DESC
    """, [county.upper(), year, latest_date, days])

    rows = cursor.fetchall()

    # Group by date
    by_date = {}
    for row in rows:
        d = row["spray_date"].strftime("%Y-%m-%d")
        if d not in by_date:
            by_date[d] = {
                "date": d,
                "date_formatted": row["spray_date"].strftime("%B %d, %Y"),
                "day_of_week": row["spray_date"].strftime("%A"),
                "chemicals": [],
                "total_lbs": 0
            }

        by_date[d]["chemicals"].append({
            "name": row["chemical"],
            "lbs": float(row["total_lbs"]),
            "applications": row["applications"],
            "site": row["site_name"]
        })
        by_date[d]["total_lbs"] += float(row["total_lbs"]) if row["total_lbs"] else 0

    cursor.close()
    conn.close()

    # Convert to sorted list
    timeline = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)

    return {
        "county": county.upper(),
        "year": year,
        "latest_data_date": latest_date.strftime("%Y-%m-%d"),
        "lookback_days": days,
        "spray_days_found": len(timeline),
        "timeline": timeline
    }

@router.get("/history/chemicals/{county}")
def get_chemical_history(
    county: str,
    year: int = Query(2023),
    limit: int = Query(20)
):
    """
    Get most-used chemicals in a county with application dates

    Useful for researching specific chemical exposure patterns.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            chemname as chemical,
            SUM(lbs_chm_used) as total_lbs,
            COUNT(*) as spray_events,
            MIN(applic_dt) as first_application,
            MAX(applic_dt) as last_application,
            COUNT(DISTINCT applic_dt) as days_applied
        FROM sprays
        WHERE UPPER(county) = %s AND year = %s
        GROUP BY chemname
        ORDER BY total_lbs DESC
        LIMIT %s
    """, [county.upper(), year, limit])

    rows = cursor.fetchall()

    chemicals = []
    for row in rows:
        chemicals.append({
            "chemical": row["chemical"],
            "total_lbs": float(row["total_lbs"]) if row["total_lbs"] else 0,
            "spray_events": row["spray_events"],
            "days_applied": row["days_applied"],
            "first_application": row["first_application"].strftime("%Y-%m-%d") if row["first_application"] else None,
            "last_application": row["last_application"].strftime("%Y-%m-%d") if row["last_application"] else None,
            "date_range": f"{row['first_application'].strftime('%b %d')} - {row['last_application'].strftime('%b %d, %Y')}" if row["first_application"] and row["last_application"] else "Unknown"
        })

    cursor.close()
    conn.close()

    return {
        "county": county.upper(),
        "year": year,
        "chemicals": chemicals
    }

@router.get("/history/peak-days/{county}")
def get_peak_spray_days(
    county: str,
    year: int = Query(2023),
    top_n: int = Query(10)
):
    """
    Get the highest spray volume days in a county

    These are the days parents should be most concerned about.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            applic_dt as spray_date,
            SUM(lbs_chm_used) as total_lbs,
            COUNT(*) as spray_events,
            COUNT(DISTINCT chemname) as unique_chemicals,
            array_agg(DISTINCT chemname ORDER BY chemname) as chemicals
        FROM sprays
        WHERE UPPER(county) = %s AND year = %s AND applic_dt IS NOT NULL
        GROUP BY applic_dt
        ORDER BY total_lbs DESC
        LIMIT %s
    """, [county.upper(), year, top_n])

    rows = cursor.fetchall()

    peak_days = []
    for i, row in enumerate(rows):
        peak_days.append({
            "rank": i + 1,
            "date": row["spray_date"].strftime("%Y-%m-%d"),
            "date_formatted": row["spray_date"].strftime("%A, %B %d, %Y"),
            "total_lbs": float(row["total_lbs"]) if row["total_lbs"] else 0,
            "spray_events": row["spray_events"],
            "unique_chemicals": row["unique_chemicals"],
            "chemicals": row["chemicals"][:10] if row["chemicals"] else []
        })

    cursor.close()
    conn.close()

    return {
        "county": county.upper(),
        "year": year,
        "peak_days": peak_days,
        "warning": "These were the highest pesticide application days. If you were outdoors on these dates, you may have had elevated exposure."
    }
