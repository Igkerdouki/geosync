"""
Chemical toxicity and safety information API
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from app.data.chemicals import (
    CHEMICAL_INFO, EPA_TOXICITY_CATEGORIES, CHEMICAL_CLASSES,
    get_chemical_info, get_toxicity_category_info, get_chemical_class_info
)
from app.database import get_connection

router = APIRouter()

@router.get("/toxicity/chemical/{chem_code}")
def get_chemical_toxicity(chem_code: int):
    """
    Get toxicity and safety information for a specific chemical.
    Includes EPA category, carcinogenicity, and usage warnings.
    """
    info = get_chemical_info(chem_code)

    if not info:
        # Try to get basic info from database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT chemname FROM sprays WHERE chem_code = %s LIMIT 1",
            (chem_code,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return {
                "chem_code": chem_code,
                "chemname": row["chemname"],
                "toxicity_data_available": False,
                "message": "Detailed toxicity data not yet in database. Check EPA or CA DPR."
            }
        else:
            raise HTTPException(status_code=404, detail="Chemical not found")

    return {
        "chem_code": chem_code,
        "toxicity_data_available": True,
        **info
    }

@router.get("/toxicity/categories")
def get_epa_categories():
    """
    Get EPA toxicity category definitions.
    """
    return EPA_TOXICITY_CATEGORIES

@router.get("/toxicity/category/{category}")
def get_category_info(category: str):
    """
    Get details for a specific EPA toxicity category (I, II, III, or IV).
    """
    info = get_toxicity_category_info(category.upper())
    if not info:
        raise HTTPException(status_code=404, detail="Category not found. Use I, II, III, or IV.")
    return {"category": category.upper(), **info}

@router.get("/toxicity/classes")
def get_chemical_classes():
    """
    Get information about chemical classes and their characteristics.
    """
    return CHEMICAL_CLASSES

@router.get("/toxicity/class/{class_name}")
def get_class_info(class_name: str):
    """
    Get details for a specific chemical class.
    """
    info = get_chemical_class_info(class_name)
    if not info:
        return {
            "class": class_name,
            "found": False,
            "available_classes": list(CHEMICAL_CLASSES.keys())
        }
    return {"class": class_name, **info}

@router.get("/toxicity/search")
def search_by_toxicity(
    category: Optional[str] = Query(None, description="EPA category I, II, III, or IV"),
    carcinogen: Optional[bool] = Query(None),
    restricted: Optional[bool] = Query(None),
    bee_toxic: Optional[bool] = Query(None),
    organic_approved: Optional[bool] = Query(None)
):
    """
    Search chemicals by toxicity characteristics.
    """
    results = []

    for code, info in CHEMICAL_INFO.items():
        match = True

        if category and info.get("epa_toxicity_category") != category.upper():
            match = False
        if carcinogen is not None:
            is_carcinogen = "carcinogen" in info.get("carcinogen", "").lower() or \
                           "likely" in info.get("carcinogen", "").lower()
            if carcinogen != is_carcinogen:
                match = False
        if restricted is not None and info.get("restricted_use", False) != restricted:
            match = False
        if bee_toxic is not None and info.get("bee_toxic", False) != bee_toxic:
            match = False
        if organic_approved is not None and info.get("organic_approved", False) != organic_approved:
            match = False

        if match:
            results.append({
                "chem_code": code,
                "name": info["name"],
                "epa_category": info.get("epa_toxicity_category"),
                "signal_word": info.get("signal_word"),
                "type": info.get("type"),
                "restricted_use": info.get("restricted_use", False)
            })

    return results

@router.get("/toxicity/high-concern")
def get_high_concern_chemicals():
    """
    Get list of chemicals with high toxicity concerns.
    Useful for researchers focusing on most hazardous pesticides.
    """
    high_concern = []

    for code, info in CHEMICAL_INFO.items():
        concerns = []

        if info.get("epa_toxicity_category") == "I":
            concerns.append("EPA Category I (Highly Toxic)")
        if "carcinogen" in info.get("carcinogen", "").lower() or \
           "likely" in info.get("carcinogen", "").lower():
            concerns.append("Potential carcinogen")
        if info.get("endocrine_disruptor") == "Yes":
            concerns.append("Endocrine disruptor")
        if info.get("neurotoxic"):
            concerns.append("Neurotoxic")
        if info.get("groundwater_contaminant"):
            concerns.append("Groundwater contaminant")
        if info.get("bee_toxic"):
            concerns.append("Bee toxic")
        if info.get("ozone_depleting"):
            concerns.append("Ozone depleting")

        if concerns:
            high_concern.append({
                "chem_code": code,
                "name": info["name"],
                "type": info.get("type"),
                "concerns": concerns,
                "restricted_use": info.get("restricted_use", False),
                "notes": info.get("notes")
            })

    # Sort by number of concerns
    high_concern.sort(key=lambda x: len(x["concerns"]), reverse=True)
    return high_concern

@router.get("/toxicity/usage-in-california")
def get_toxicity_usage_stats(
    year: Optional[int] = Query(None),
    category: Optional[str] = Query(None, description="EPA category I, II, III, or IV")
):
    """
    Get usage statistics for chemicals by toxicity category in California.
    Links toxicity data to actual PUR usage.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get usage for chemicals we have toxicity data for
    results = []
    for chem_code, info in CHEMICAL_INFO.items():
        if category and info.get("epa_toxicity_category") != category.upper():
            continue

        query = """
            SELECT
                SUM(lbs_chm_used) as total_lbs,
                COUNT(*) as applications,
                COUNT(DISTINCT county_cd) as counties
            FROM sprays
            WHERE chem_code = %s
        """
        params = [chem_code]

        if year:
            query += " AND year = %s"
            params.append(year)

        cursor.execute(query, params)
        row = cursor.fetchone()

        if row and row["total_lbs"]:
            results.append({
                "chem_code": chem_code,
                "name": info["name"],
                "epa_category": info.get("epa_toxicity_category"),
                "signal_word": info.get("signal_word"),
                "type": info.get("type"),
                "total_lbs": float(row["total_lbs"]),
                "applications": row["applications"],
                "counties": row["counties"],
                "restricted_use": info.get("restricted_use", False),
                "concerns": []
            })

            # Add concerns
            if info.get("carcinogen") and "no" not in info["carcinogen"].lower():
                results[-1]["concerns"].append("carcinogen")
            if info.get("bee_toxic"):
                results[-1]["concerns"].append("bee_toxic")
            if info.get("neurotoxic"):
                results[-1]["concerns"].append("neurotoxic")

    cursor.close()
    conn.close()

    # Sort by total lbs
    results.sort(key=lambda x: x["total_lbs"], reverse=True)
    return results
