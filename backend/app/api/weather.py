"""
Weather API endpoints for real-time drift risk assessment
"""

from fastapi import APIRouter, Query
from typing import Optional, List

from app.services.weather import (
    fetch_current_weather,
    calculate_drift_risk,
    estimate_drift_distance,
    get_weather_for_counties
)

router = APIRouter()

@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get current weather conditions for a location

    Includes wind speed/direction, temperature, humidity,
    and atmospheric stability classification.
    """
    weather = await fetch_current_weather(lat, lon)
    if not weather:
        return {"error": "Unable to fetch weather data"}

    return weather

@router.get("/weather/drift-risk")
async def get_drift_risk(
    lat: float = Query(...),
    lon: float = Query(...),
    chemical_toxicity: str = Query("medium", description="low, medium, or high")
):
    """
    Calculate current drift risk based on weather conditions

    Returns:
    - Risk level (critical, high, moderate, low)
    - Risk factors contributing to the assessment
    - Spray recommendations
    """
    weather = await fetch_current_weather(lat, lon)
    if not weather:
        return {"error": "Unable to fetch weather data"}

    risk = calculate_drift_risk(weather, chemical_toxicity)
    drift = estimate_drift_distance(weather)

    return {
        "weather": weather,
        "risk_assessment": risk,
        "drift_estimate": drift
    }

@router.get("/weather/counties")
async def get_county_weather(
    counties: str = Query("FRESNO,KERN,TULARE", description="Comma-separated county names")
):
    """
    Get weather conditions for multiple counties

    Useful for showing regional conditions across agricultural areas.
    """
    county_list = [c.strip().upper() for c in counties.split(",")]
    results = await get_weather_for_counties(county_list)

    # Add drift risk for each county
    for county, weather in results.items():
        risk = calculate_drift_risk(weather)
        results[county] = {
            **weather,
            "drift_risk": risk
        }

    return {
        "timestamp": results.get(county_list[0], {}).get("timestamp"),
        "counties": results
    }

@router.get("/weather/spray-window")
async def get_spray_window(
    lat: float = Query(...),
    lon: float = Query(...)
):
    """
    Determine if current conditions are safe for spraying

    Returns a simple yes/no with reasoning.
    """
    weather = await fetch_current_weather(lat, lon)
    if not weather:
        return {"error": "Unable to fetch weather data"}

    risk = calculate_drift_risk(weather)

    is_safe = risk["risk_level"] in ["low", "moderate"]

    return {
        "safe_to_spray": is_safe,
        "risk_level": risk["risk_level"],
        "recommendation": risk["recommendation"],
        "current_conditions": {
            "wind": f"{weather['wind_speed_mph']} mph {weather['wind_direction_cardinal']}",
            "temperature": f"{weather['temperature_f']}°F",
            "humidity": f"{weather['humidity_pct']}%",
            "stability": weather["stability_class"]
        },
        "factors": risk["factors"]
    }
