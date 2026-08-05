"""
Research API endpoints for data analysis and export
"""

from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import date
import csv
import io

from app.database import get_connection

router = APIRouter()

@router.get("/research/export")
def export_data(
    year: Optional[int] = Query(None),
    county: Optional[str] = Query(None),
    chem_code: Optional[int] = Query(None),
    chemname: Optional[str] = Query(None),
    site_code: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10000, le=100000),
    format: str = Query("csv", regex="^(csv|json)$")
):
    """
    Export spray data as CSV or JSON for research analysis.
    Max 100,000 rows per request.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT year, applic_dt, county_cd, county, chemname, chem_code,
               product_name, prodno, lbs_chm_used, lbs_prd_used, acre_treated,
               site_code, site_name, aer_gnd_ind, township, range, section, comtrs
        FROM sprays WHERE 1=1
    """
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
    if chemname:
        query += " AND chemname ILIKE %s"
        params.append(f"%{chemname}%")
    if site_code:
        query += " AND site_code = %s"
        params.append(site_code)
    if start_date:
        query += " AND applic_dt >= %s"
        params.append(start_date)
    if end_date:
        query += " AND applic_dt <= %s"
        params.append(end_date)

    query += " ORDER BY applic_dt DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    cursor.close()
    conn.close()

    if format == "json":
        return [dict(row) for row in results]

    # CSV export
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in results:
        writer.writerow(dict(row))

    response = Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=geosync_export_{year or 'all'}.csv"}
    )
    return response

@router.get("/research/chemicals")
def get_chemicals(
    year: Optional[int] = Query(None),
    min_lbs: Optional[float] = Query(None, description="Minimum total lbs applied"),
    search: Optional[str] = Query(None, description="Search chemical name")
):
    """
    Get list of all chemicals with usage statistics.
    Useful for researchers to understand what's being applied.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            chem_code,
            chemname,
            COUNT(*) as application_count,
            SUM(lbs_chm_used) as total_lbs,
            SUM(acre_treated) as total_acres,
            COUNT(DISTINCT county_cd) as county_count,
            MIN(applic_dt) as first_application,
            MAX(applic_dt) as last_application
        FROM sprays
        WHERE chemname IS NOT NULL
    """
    params = []

    if year:
        query += " AND year = %s"
        params.append(year)
    if search:
        query += " AND chemname ILIKE %s"
        params.append(f"%{search}%")

    query += " GROUP BY chem_code, chemname"

    if min_lbs:
        query += " HAVING SUM(lbs_chm_used) >= %s"
        params.append(min_lbs)

    query += " ORDER BY total_lbs DESC NULLS LAST"

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{
        "chem_code": r["chem_code"],
        "chemname": r["chemname"],
        "application_count": r["application_count"],
        "total_lbs": float(r["total_lbs"] or 0),
        "total_acres": float(r["total_acres"] or 0),
        "county_count": r["county_count"],
        "first_application": str(r["first_application"]) if r["first_application"] else None,
        "last_application": str(r["last_application"]) if r["last_application"] else None
    } for r in results]

@router.get("/research/sites")
def get_sites(
    year: Optional[int] = Query(None),
    county: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Get list of application sites (crops/locations) with statistics.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            site_code,
            site_name,
            COUNT(*) as application_count,
            SUM(lbs_chm_used) as total_lbs,
            SUM(acre_treated) as total_acres,
            COUNT(DISTINCT chem_code) as chemical_count,
            COUNT(DISTINCT county_cd) as county_count
        FROM sprays
        WHERE site_name IS NOT NULL
    """
    params = []

    if year:
        query += " AND year = %s"
        params.append(year)
    if county:
        query += " AND (county ILIKE %s OR county_cd = %s)"
        params.extend([f"%{county}%", county])
    if search:
        query += " AND site_name ILIKE %s"
        params.append(f"%{search}%")

    query += " GROUP BY site_code, site_name ORDER BY total_lbs DESC NULLS LAST LIMIT 100"

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{
        "site_code": r["site_code"],
        "site_name": r["site_name"],
        "application_count": r["application_count"],
        "total_lbs": float(r["total_lbs"] or 0),
        "total_acres": float(r["total_acres"] or 0),
        "chemical_count": r["chemical_count"],
        "county_count": r["county_count"]
    } for r in results]

@router.get("/research/trends/monthly")
def get_monthly_trends(
    year: Optional[int] = Query(None),
    county: Optional[str] = Query(None),
    chem_code: Optional[int] = Query(None)
):
    """
    Get monthly application trends for time series analysis.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            EXTRACT(YEAR FROM applic_dt) as year,
            EXTRACT(MONTH FROM applic_dt) as month,
            COUNT(*) as application_count,
            SUM(lbs_chm_used) as total_lbs,
            SUM(acre_treated) as total_acres,
            COUNT(DISTINCT chem_code) as unique_chemicals
        FROM sprays
        WHERE applic_dt IS NOT NULL
    """
    params = []

    if year:
        query += " AND EXTRACT(YEAR FROM applic_dt) = %s"
        params.append(year)
    if county:
        query += " AND (county ILIKE %s OR county_cd = %s)"
        params.extend([f"%{county}%", county])
    if chem_code:
        query += " AND chem_code = %s"
        params.append(chem_code)

    query += " GROUP BY year, month ORDER BY year, month"

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{
        "year": int(r["year"]),
        "month": int(r["month"]),
        "application_count": r["application_count"],
        "total_lbs": float(r["total_lbs"] or 0),
        "total_acres": float(r["total_acres"] or 0),
        "unique_chemicals": r["unique_chemicals"]
    } for r in results]

@router.get("/research/trends/yearly")
def get_yearly_trends(
    county: Optional[str] = Query(None),
    chem_code: Optional[int] = Query(None)
):
    """
    Get yearly trends for long-term analysis.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            year,
            COUNT(*) as application_count,
            SUM(lbs_chm_used) as total_lbs,
            SUM(acre_treated) as total_acres,
            COUNT(DISTINCT chem_code) as unique_chemicals,
            COUNT(DISTINCT county_cd) as unique_counties
        FROM sprays
        WHERE year IS NOT NULL
    """
    params = []

    if county:
        query += " AND (county ILIKE %s OR county_cd = %s)"
        params.extend([f"%{county}%", county])
    if chem_code:
        query += " AND chem_code = %s"
        params.append(chem_code)

    query += " GROUP BY year ORDER BY year"

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return [{
        "year": r["year"],
        "application_count": r["application_count"],
        "total_lbs": float(r["total_lbs"] or 0),
        "total_acres": float(r["total_acres"] or 0),
        "unique_chemicals": r["unique_chemicals"],
        "unique_counties": r["unique_counties"]
    } for r in results]

@router.get("/research/county/{county_cd}")
def get_county_details(
    county_cd: str,
    year: Optional[int] = Query(None)
):
    """
    Get detailed analysis for a specific county.
    """
    conn = get_connection()
    cursor = conn.cursor()

    where_clause = "WHERE county_cd = %s"
    params = [county_cd]

    if year:
        where_clause += " AND year = %s"
        params.append(year)

    # Basic stats
    cursor.execute(f"""
        SELECT
            county,
            COUNT(*) as total_applications,
            SUM(lbs_chm_used) as total_lbs,
            SUM(acre_treated) as total_acres,
            COUNT(DISTINCT chem_code) as unique_chemicals,
            COUNT(DISTINCT site_code) as unique_sites
        FROM sprays {where_clause}
        GROUP BY county
    """, params)
    basic = cursor.fetchone()

    if not basic:
        return {"error": "County not found"}

    # Top chemicals
    cursor.execute(f"""
        SELECT chemname, chem_code, SUM(lbs_chm_used) as total_lbs
        FROM sprays {where_clause} AND chemname IS NOT NULL
        GROUP BY chemname, chem_code
        ORDER BY total_lbs DESC NULLS LAST
        LIMIT 10
    """, params)
    top_chemicals = cursor.fetchall()

    # Top sites
    cursor.execute(f"""
        SELECT site_name, site_code, SUM(lbs_chm_used) as total_lbs
        FROM sprays {where_clause} AND site_name IS NOT NULL
        GROUP BY site_name, site_code
        ORDER BY total_lbs DESC NULLS LAST
        LIMIT 10
    """, params)
    top_sites = cursor.fetchall()

    # Monthly breakdown
    cursor.execute(f"""
        SELECT
            EXTRACT(MONTH FROM applic_dt) as month,
            SUM(lbs_chm_used) as total_lbs
        FROM sprays {where_clause} AND applic_dt IS NOT NULL
        GROUP BY month
        ORDER BY month
    """, params)
    monthly = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "county_cd": county_cd,
        "county_name": basic["county"],
        "summary": {
            "total_applications": basic["total_applications"],
            "total_lbs": float(basic["total_lbs"] or 0),
            "total_acres": float(basic["total_acres"] or 0),
            "unique_chemicals": basic["unique_chemicals"],
            "unique_sites": basic["unique_sites"]
        },
        "top_chemicals": [
            {"name": r["chemname"], "code": r["chem_code"], "lbs": float(r["total_lbs"] or 0)}
            for r in top_chemicals
        ],
        "top_sites": [
            {"name": r["site_name"], "code": r["site_code"], "lbs": float(r["total_lbs"] or 0)}
            for r in top_sites
        ],
        "monthly_distribution": [
            {"month": int(r["month"]), "lbs": float(r["total_lbs"] or 0)}
            for r in monthly
        ]
    }

@router.get("/research/chemical/{chem_code}")
def get_chemical_details(
    chem_code: int,
    year: Optional[int] = Query(None)
):
    """
    Get detailed analysis for a specific chemical.
    """
    conn = get_connection()
    cursor = conn.cursor()

    where_clause = "WHERE chem_code = %s"
    params = [chem_code]

    if year:
        where_clause += " AND year = %s"
        params.append(year)

    # Basic stats
    cursor.execute(f"""
        SELECT
            chemname,
            COUNT(*) as total_applications,
            SUM(lbs_chm_used) as total_lbs,
            SUM(acre_treated) as total_acres,
            COUNT(DISTINCT county_cd) as county_count,
            COUNT(DISTINCT site_code) as site_count,
            MIN(applic_dt) as first_use,
            MAX(applic_dt) as last_use
        FROM sprays {where_clause}
        GROUP BY chemname
    """, params)
    basic = cursor.fetchone()

    if not basic:
        return {"error": "Chemical not found"}

    # Top counties
    cursor.execute(f"""
        SELECT county, county_cd, SUM(lbs_chm_used) as total_lbs
        FROM sprays {where_clause} AND county IS NOT NULL
        GROUP BY county, county_cd
        ORDER BY total_lbs DESC NULLS LAST
        LIMIT 10
    """, params)
    top_counties = cursor.fetchall()

    # Top sites
    cursor.execute(f"""
        SELECT site_name, site_code, SUM(lbs_chm_used) as total_lbs
        FROM sprays {where_clause} AND site_name IS NOT NULL
        GROUP BY site_name, site_code
        ORDER BY total_lbs DESC NULLS LAST
        LIMIT 10
    """, params)
    top_sites = cursor.fetchall()

    # Yearly trend
    cursor.execute(f"""
        SELECT year, SUM(lbs_chm_used) as total_lbs, COUNT(*) as applications
        FROM sprays {where_clause}
        GROUP BY year
        ORDER BY year
    """, params)
    yearly = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "chem_code": chem_code,
        "chemname": basic["chemname"],
        "summary": {
            "total_applications": basic["total_applications"],
            "total_lbs": float(basic["total_lbs"] or 0),
            "total_acres": float(basic["total_acres"] or 0),
            "county_count": basic["county_count"],
            "site_count": basic["site_count"],
            "first_use": str(basic["first_use"]) if basic["first_use"] else None,
            "last_use": str(basic["last_use"]) if basic["last_use"] else None
        },
        "top_counties": [
            {"name": r["county"], "code": r["county_cd"], "lbs": float(r["total_lbs"] or 0)}
            for r in top_counties
        ],
        "top_sites": [
            {"name": r["site_name"], "code": r["site_code"], "lbs": float(r["total_lbs"] or 0)}
            for r in top_sites
        ],
        "yearly_trend": [
            {"year": r["year"], "lbs": float(r["total_lbs"] or 0), "applications": r["applications"]}
            for r in yearly
        ]
    }

@router.get("/research/compare/chemicals")
def compare_chemicals(
    codes: str = Query(..., description="Comma-separated chem_codes, e.g., '1855,2289,5447'"),
    year: Optional[int] = Query(None)
):
    """
    Compare multiple chemicals side by side.
    """
    chem_codes = [int(c.strip()) for c in codes.split(",")]

    conn = get_connection()
    cursor = conn.cursor()

    results = []
    for code in chem_codes:
        query = """
            SELECT
                chem_code,
                chemname,
                COUNT(*) as applications,
                SUM(lbs_chm_used) as total_lbs,
                SUM(acre_treated) as total_acres,
                COUNT(DISTINCT county_cd) as counties
            FROM sprays
            WHERE chem_code = %s
        """
        params = [code]

        if year:
            query += " AND year = %s"
            params.append(year)

        query += " GROUP BY chem_code, chemname"

        cursor.execute(query, params)
        row = cursor.fetchone()

        if row:
            results.append({
                "chem_code": row["chem_code"],
                "chemname": row["chemname"],
                "applications": row["applications"],
                "total_lbs": float(row["total_lbs"] or 0),
                "total_acres": float(row["total_acres"] or 0),
                "counties": row["counties"]
            })

    cursor.close()
    conn.close()

    return results

@router.get("/research/compare/counties")
def compare_counties(
    codes: str = Query(..., description="Comma-separated county_codes, e.g., '10,15,27'"),
    year: Optional[int] = Query(None)
):
    """
    Compare multiple counties side by side.
    """
    county_codes = [c.strip() for c in codes.split(",")]

    conn = get_connection()
    cursor = conn.cursor()

    results = []
    for code in county_codes:
        query = """
            SELECT
                county_cd,
                county,
                COUNT(*) as applications,
                SUM(lbs_chm_used) as total_lbs,
                SUM(acre_treated) as total_acres,
                COUNT(DISTINCT chem_code) as chemicals
            FROM sprays
            WHERE county_cd = %s
        """
        params = [code]

        if year:
            query += " AND year = %s"
            params.append(year)

        query += " GROUP BY county_cd, county"

        cursor.execute(query, params)
        row = cursor.fetchone()

        if row:
            results.append({
                "county_cd": row["county_cd"],
                "county": row["county"],
                "applications": row["applications"],
                "total_lbs": float(row["total_lbs"] or 0),
                "total_acres": float(row["total_acres"] or 0),
                "chemicals": row["chemicals"]
            })

    cursor.close()
    conn.close()

    return results
