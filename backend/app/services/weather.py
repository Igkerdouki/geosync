"""
Weather Service - Real-time weather data for drift prediction

Uses OpenWeatherMap API (free tier: 1000 calls/day)
Sign up at: https://openweathermap.org/api

For production, set OPENWEATHER_API_KEY environment variable
"""

import os
import httpx
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
import math

# API Configuration
# Get your free API key at: https://openweathermap.org/api
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "demo")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Cache weather data to reduce API calls (cache for 10 minutes)
weather_cache: Dict[str, Tuple[dict, datetime]] = {}
CACHE_DURATION = timedelta(minutes=10)

# Pasquill-Gifford Atmospheric Stability Classes
# Based on wind speed and solar radiation/cloud cover
STABILITY_CLASSES = {
    "A": "Very Unstable - Strong daytime, light wind",
    "B": "Unstable - Moderate daytime, light-moderate wind",
    "C": "Slightly Unstable - Overcast day, moderate wind",
    "D": "Neutral - Overcast or windy conditions",
    "E": "Slightly Stable - Evening, light wind",
    "F": "Stable - Night, light wind, clear sky"
}

def get_cache_key(lat: float, lon: float) -> str:
    """Create cache key from coordinates (rounded to reduce API calls)"""
    return f"{round(lat, 2)}_{round(lon, 2)}"

async def fetch_current_weather(lat: float, lon: float) -> Optional[dict]:
    """
    Fetch current weather from OpenWeatherMap API

    Returns weather data including:
    - Temperature
    - Wind speed and direction
    - Humidity
    - Cloud cover
    - Visibility
    """
    cache_key = get_cache_key(lat, lon)

    # Check cache first
    if cache_key in weather_cache:
        cached_data, cached_time = weather_cache[cache_key]
        if datetime.now() - cached_time < CACHE_DURATION:
            return cached_data

    if OPENWEATHER_API_KEY == "demo":
        # Return simulated data if no API key
        return generate_simulated_weather(lat, lon)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENWEATHER_BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "imperial"  # Fahrenheit, mph
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                weather = parse_weather_response(data)
                weather_cache[cache_key] = (weather, datetime.now())
                return weather
            else:
                print(f"Weather API error: {response.status_code}")
                return generate_simulated_weather(lat, lon)

    except Exception as e:
        print(f"Weather fetch error: {e}")
        return generate_simulated_weather(lat, lon)

def parse_weather_response(data: dict) -> dict:
    """Parse OpenWeatherMap response into our format"""
    wind = data.get("wind", {})
    main = data.get("main", {})
    clouds = data.get("clouds", {})

    wind_speed = wind.get("speed", 0)  # mph
    wind_deg = wind.get("deg", 0)  # degrees

    # Calculate atmospheric stability
    cloud_cover = clouds.get("all", 50)  # percentage
    hour = datetime.now().hour
    is_daytime = 6 <= hour <= 18

    stability = calculate_stability_class(wind_speed, cloud_cover, is_daytime)

    return {
        "temperature_f": round(main.get("temp", 70), 1),
        "feels_like_f": round(main.get("feels_like", 70), 1),
        "humidity_pct": main.get("humidity", 50),
        "pressure_hpa": main.get("pressure", 1013),

        "wind_speed_mph": round(wind_speed, 1),
        "wind_direction_deg": wind_deg,
        "wind_direction_cardinal": degrees_to_cardinal(wind_deg),
        "wind_gust_mph": round(wind.get("gust", wind_speed), 1),

        "cloud_cover_pct": cloud_cover,
        "visibility_miles": round(data.get("visibility", 10000) / 1609, 1),

        "stability_class": stability,
        "stability_description": STABILITY_CLASSES.get(stability, "Unknown"),

        "conditions": data.get("weather", [{}])[0].get("description", "clear"),
        "icon": data.get("weather", [{}])[0].get("icon", "01d"),

        "timestamp": datetime.now().isoformat(),
        "source": "openweathermap"
    }

def generate_simulated_weather(lat: float, lon: float) -> dict:
    """Generate realistic simulated weather for California agricultural areas"""
    import random

    # Seasonal variations based on current month
    month = datetime.now().month
    hour = datetime.now().hour

    # California Central Valley typical conditions
    if month in [6, 7, 8]:  # Summer
        base_temp = random.uniform(85, 105)
        humidity = random.uniform(15, 35)
    elif month in [12, 1, 2]:  # Winter
        base_temp = random.uniform(45, 65)
        humidity = random.uniform(50, 80)
    else:  # Spring/Fall
        base_temp = random.uniform(65, 85)
        humidity = random.uniform(30, 55)

    # Wind patterns - typically from NW in afternoon, calmer morning/evening
    if 10 <= hour <= 16:
        wind_speed = random.uniform(5, 15)
        wind_dir = random.uniform(280, 340)  # NW winds
    else:
        wind_speed = random.uniform(2, 8)
        wind_dir = random.uniform(0, 360)

    cloud_cover = random.uniform(0, 40) if month in [6, 7, 8] else random.uniform(20, 70)
    is_daytime = 6 <= hour <= 18

    stability = calculate_stability_class(wind_speed, cloud_cover, is_daytime)

    return {
        "temperature_f": round(base_temp, 1),
        "feels_like_f": round(base_temp - 2 + random.uniform(-3, 3), 1),
        "humidity_pct": round(humidity),
        "pressure_hpa": round(1010 + random.uniform(-10, 10)),

        "wind_speed_mph": round(wind_speed, 1),
        "wind_direction_deg": round(wind_dir),
        "wind_direction_cardinal": degrees_to_cardinal(wind_dir),
        "wind_gust_mph": round(wind_speed * random.uniform(1.1, 1.5), 1),

        "cloud_cover_pct": round(cloud_cover),
        "visibility_miles": round(random.uniform(5, 10), 1),

        "stability_class": stability,
        "stability_description": STABILITY_CLASSES.get(stability, "Unknown"),

        "conditions": "clear sky" if cloud_cover < 20 else "partly cloudy" if cloud_cover < 60 else "cloudy",
        "icon": "01d" if is_daytime and cloud_cover < 20 else "02d" if is_daytime else "01n",

        "timestamp": datetime.now().isoformat(),
        "source": "simulated"
    }

def calculate_stability_class(wind_speed_mph: float, cloud_cover_pct: float, is_daytime: bool) -> str:
    """
    Calculate Pasquill-Gifford atmospheric stability class

    This determines how pesticide plumes disperse:
    - Unstable (A, B, C): More vertical mixing, faster dispersion
    - Neutral (D): Moderate dispersion
    - Stable (E, F): Less mixing, plumes travel farther horizontally
    """
    # Convert wind to m/s for standard classification
    wind_ms = wind_speed_mph * 0.447

    # Solar radiation proxy based on cloud cover and time
    if is_daytime:
        if cloud_cover_pct < 30:
            solar = "strong"
        elif cloud_cover_pct < 70:
            solar = "moderate"
        else:
            solar = "slight"
    else:
        if cloud_cover_pct < 40:
            solar = "clear_night"
        else:
            solar = "cloudy_night"

    # Pasquill-Gifford classification
    if wind_ms < 2:
        if solar == "strong":
            return "A"
        elif solar == "moderate":
            return "A"
        elif solar == "slight":
            return "B"
        elif solar == "clear_night":
            return "F"
        else:
            return "E"
    elif wind_ms < 3:
        if solar == "strong":
            return "A"
        elif solar == "moderate":
            return "B"
        elif solar == "slight":
            return "C"
        elif solar == "clear_night":
            return "F"
        else:
            return "E"
    elif wind_ms < 5:
        if solar == "strong":
            return "B"
        elif solar == "moderate":
            return "B"
        elif solar == "slight":
            return "C"
        elif solar == "clear_night":
            return "E"
        else:
            return "D"
    elif wind_ms < 6:
        if solar == "strong":
            return "C"
        elif solar == "moderate":
            return "C"
        elif solar == "slight":
            return "D"
        else:
            return "D"
    else:
        return "D"  # High wind = neutral stability

def degrees_to_cardinal(degrees: float) -> str:
    """Convert wind direction degrees to cardinal direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]

def calculate_drift_risk(weather: dict, chemical_toxicity: str = "medium") -> dict:
    """
    Calculate pesticide drift risk based on current weather conditions

    Returns risk assessment with recommendations
    """
    wind_speed = weather["wind_speed_mph"]
    stability = weather["stability_class"]
    humidity = weather["humidity_pct"]
    temp = weather["temperature_f"]

    # Risk factors
    risk_score = 0
    factors = []

    # Wind speed risk
    if wind_speed > 10:
        risk_score += 40
        factors.append(f"High wind ({wind_speed} mph) increases drift distance")
    elif wind_speed > 6:
        risk_score += 20
        factors.append(f"Moderate wind ({wind_speed} mph) may cause drift")
    elif wind_speed < 3:
        risk_score += 10
        factors.append("Low wind may cause temperature inversions")

    # Atmospheric stability risk
    if stability in ["E", "F"]:
        risk_score += 30
        factors.append(f"Stable atmosphere ({stability}) - plumes travel farther")
    elif stability in ["A", "B"]:
        risk_score -= 10
        factors.append(f"Unstable atmosphere ({stability}) - good vertical dispersion")

    # Temperature inversion risk (early morning, evening)
    hour = datetime.now().hour
    if (hour < 8 or hour > 18) and wind_speed < 5:
        risk_score += 25
        factors.append("Possible temperature inversion - avoid spraying")

    # High temperature + low humidity = faster evaporation but also drift
    if temp > 90 and humidity < 30:
        risk_score += 15
        factors.append("Hot/dry conditions increase small droplet drift")

    # Chemical toxicity multiplier
    if chemical_toxicity == "high":
        risk_score = int(risk_score * 1.5)
        factors.append("High-toxicity chemical requires extra caution")

    # Determine risk level
    if risk_score >= 60:
        level = "critical"
        recommendation = "DO NOT SPRAY - Conditions unsafe for application"
        color = "#ef4444"
    elif risk_score >= 40:
        level = "high"
        recommendation = "AVOID SPRAYING - High drift potential, wait for better conditions"
        color = "#f97316"
    elif risk_score >= 20:
        level = "moderate"
        recommendation = "USE CAUTION - Apply with drift-reducing practices"
        color = "#f59e0b"
    else:
        level = "low"
        recommendation = "CONDITIONS FAVORABLE - Normal precautions apply"
        color = "#10b981"

    return {
        "risk_level": level,
        "risk_score": min(risk_score, 100),
        "recommendation": recommendation,
        "color": color,
        "factors": factors,
        "weather_summary": {
            "wind": f"{wind_speed} mph {weather['wind_direction_cardinal']}",
            "stability": f"Class {stability}",
            "temp": f"{temp}°F",
            "humidity": f"{humidity}%"
        }
    }

def estimate_drift_distance(weather: dict, application_rate_lbs_acre: float = 2.0) -> dict:
    """
    Estimate maximum drift distance based on weather conditions

    Uses simplified Gaussian plume model assumptions
    """
    wind_speed = weather["wind_speed_mph"]
    stability = weather["stability_class"]

    # Base drift distance (meters) for typical ground application
    # Increases with wind speed
    base_distance = 100 + (wind_speed * 50)

    # Stability multiplier
    stability_multipliers = {
        "A": 0.5,  # Very unstable - rapid vertical mixing
        "B": 0.7,
        "C": 0.9,
        "D": 1.0,  # Neutral
        "E": 1.3,
        "F": 1.6   # Very stable - plume travels far
    }

    multiplier = stability_multipliers.get(stability, 1.0)

    # Higher application rates = more drift potential
    rate_factor = 1 + (application_rate_lbs_acre / 10)

    max_distance_m = base_distance * multiplier * rate_factor
    max_distance_miles = max_distance_m / 1609

    # Concentration zones
    high_conc_distance = max_distance_m * 0.2
    medium_conc_distance = max_distance_m * 0.5

    return {
        "max_drift_distance_m": round(max_distance_m),
        "max_drift_distance_miles": round(max_distance_miles, 2),
        "high_concentration_zone_m": round(high_conc_distance),
        "medium_concentration_zone_m": round(medium_conc_distance),
        "wind_direction": weather["wind_direction_cardinal"],
        "wind_direction_deg": weather["wind_direction_deg"],
        "drift_direction": (weather["wind_direction_deg"] + 180) % 360,  # Opposite of wind
        "drift_direction_cardinal": degrees_to_cardinal((weather["wind_direction_deg"] + 180) % 360)
    }

async def get_weather_for_counties(counties: List[str]) -> Dict[str, dict]:
    """Get weather data for multiple county centers"""
    from app.api.sprays import COUNTY_COORDS

    results = {}
    for county in counties:
        if county.upper() in COUNTY_COORDS:
            lat, lon = COUNTY_COORDS[county.upper()]
            weather = await fetch_current_weather(lat, lon)
            if weather:
                results[county.upper()] = weather

    return results
