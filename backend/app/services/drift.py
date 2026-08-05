"""
Gaussian Plume Model for Pesticide Drift Prediction

Based on EPA AgDRIFT model equations for estimating downwind pesticide concentrations.
The Gaussian plume model calculates pollutant dispersion based on:
- Source emission rate
- Wind speed and direction
- Atmospheric stability
- Distance from source
"""

import math
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class DriftParams:
    """Parameters for drift calculation"""
    source_lat: float          # Source latitude
    source_lon: float          # Source longitude
    emission_rate: float       # kg/s (pesticide application rate)
    wind_speed: float          # m/s
    wind_direction: float      # degrees (direction wind is coming FROM)
    stability_class: str       # A-F (Pasquill-Gifford stability)
    release_height: float = 2.0  # meters (spray boom height)

# Pasquill-Gifford dispersion coefficients
# sigma_y = a * x^b, sigma_z = c * x^d + f
STABILITY_PARAMS = {
    'A': {'a': 0.22, 'b': 0.894, 'c': 0.20, 'd': 1.0, 'f': 0},      # Very unstable
    'B': {'a': 0.16, 'b': 0.894, 'c': 0.12, 'd': 0.894, 'f': 0},    # Unstable
    'C': {'a': 0.11, 'b': 0.894, 'c': 0.08, 'd': 0.894, 'f': 0},    # Slightly unstable
    'D': {'a': 0.08, 'b': 0.894, 'c': 0.06, 'd': 0.894, 'f': 0},    # Neutral
    'E': {'a': 0.06, 'b': 0.894, 'c': 0.03, 'd': 0.894, 'f': 0},    # Slightly stable
    'F': {'a': 0.04, 'b': 0.894, 'c': 0.016, 'd': 0.894, 'f': 0},   # Stable
}

def get_stability_class(wind_speed: float, is_daytime: bool, cloud_cover: float) -> str:
    """
    Determine Pasquill-Gifford stability class based on conditions.

    wind_speed: m/s
    is_daytime: True if day, False if night
    cloud_cover: 0-1 (fraction)
    """
    if is_daytime:
        if wind_speed < 2:
            return 'A' if cloud_cover < 0.5 else 'B'
        elif wind_speed < 3:
            return 'B' if cloud_cover < 0.5 else 'C'
        elif wind_speed < 5:
            return 'C' if cloud_cover < 0.5 else 'D'
        else:
            return 'D'
    else:
        if wind_speed < 2:
            return 'F'
        elif wind_speed < 3:
            return 'E' if cloud_cover < 0.5 else 'F'
        else:
            return 'D' if cloud_cover < 0.5 else 'E'

def calculate_dispersion_coefficients(x: float, stability: str) -> Tuple[float, float]:
    """
    Calculate sigma_y and sigma_z (dispersion coefficients) at distance x.

    x: downwind distance in meters
    stability: Pasquill-Gifford stability class (A-F)

    Returns: (sigma_y, sigma_z) in meters
    """
    params = STABILITY_PARAMS.get(stability, STABILITY_PARAMS['D'])

    sigma_y = params['a'] * (x ** params['b'])
    sigma_z = params['c'] * (x ** params['d']) + params['f']

    return sigma_y, sigma_z

def gaussian_plume_concentration(
    x: float,           # downwind distance (m)
    y: float,           # crosswind distance (m)
    z: float,           # height above ground (m)
    Q: float,           # emission rate (kg/s)
    u: float,           # wind speed (m/s)
    H: float,           # release height (m)
    stability: str      # stability class
) -> float:
    """
    Calculate concentration at point (x, y, z) using Gaussian plume model.

    Returns concentration in kg/m³
    """
    if x <= 0 or u <= 0:
        return 0.0

    sigma_y, sigma_z = calculate_dispersion_coefficients(x, stability)

    # Gaussian plume equation with ground reflection
    exp_y = math.exp(-0.5 * (y / sigma_y) ** 2)
    exp_z1 = math.exp(-0.5 * ((z - H) / sigma_z) ** 2)
    exp_z2 = math.exp(-0.5 * ((z + H) / sigma_z) ** 2)

    C = (Q / (2 * math.pi * u * sigma_y * sigma_z)) * exp_y * (exp_z1 + exp_z2)

    return C

def latlon_to_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    """
    Convert lat/lon difference to approximate meters (x=east, y=north).
    Uses simple equirectangular projection (accurate for short distances).
    """
    R = 6371000  # Earth radius in meters

    lat_mid = math.radians((lat1 + lat2) / 2)

    dx = R * math.radians(lon2 - lon1) * math.cos(lat_mid)
    dy = R * math.radians(lat2 - lat1)

    return dx, dy

def meters_to_latlon(lat_origin: float, lon_origin: float, dx: float, dy: float) -> Tuple[float, float]:
    """Convert meter offsets back to lat/lon"""
    R = 6371000

    lat_new = lat_origin + math.degrees(dy / R)
    lon_new = lon_origin + math.degrees(dx / (R * math.cos(math.radians(lat_origin))))

    return lat_new, lon_new

def calculate_drift_plume(params: DriftParams, max_distance: float = 5000, grid_resolution: int = 50) -> List[dict]:
    """
    Calculate drift plume and return as GeoJSON features.

    params: DriftParams with source location, wind, emission info
    max_distance: maximum downwind distance to calculate (meters)
    grid_resolution: number of points along each axis

    Returns list of GeoJSON features with concentration values
    """
    features = []

    # Wind direction is where wind comes FROM, plume goes opposite direction
    wind_rad = math.radians((params.wind_direction + 180) % 360)

    # Convert emission rate from lbs/hour to kg/s
    Q = params.emission_rate * 0.000126  # lbs/hr to kg/s

    # Create grid of points downwind
    for i in range(1, grid_resolution + 1):
        x = (i / grid_resolution) * max_distance  # downwind distance

        # Calculate max crosswind spread at this distance
        sigma_y, _ = calculate_dispersion_coefficients(x, params.stability_class)
        max_y = 3 * sigma_y  # 3 sigma covers 99.7% of plume

        for j in range(-grid_resolution // 4, grid_resolution // 4 + 1):
            y = (j / (grid_resolution // 4)) * max_y  # crosswind distance

            # Calculate concentration at ground level (z=0)
            conc = gaussian_plume_concentration(
                x, y, 0, Q, params.wind_speed, params.release_height, params.stability_class
            )

            if conc < 1e-12:  # Skip negligible concentrations
                continue

            # Convert x, y offsets to lat/lon
            # x is along wind direction, y is perpendicular
            dx = x * math.sin(wind_rad) + y * math.cos(wind_rad)
            dy = x * math.cos(wind_rad) - y * math.sin(wind_rad)

            lat, lon = meters_to_latlon(params.source_lat, params.source_lon, dx, dy)

            # Concentration to risk level (arbitrary thresholds for visualization)
            if conc > 1e-6:
                risk = "high"
            elif conc > 1e-8:
                risk = "medium"
            else:
                risk = "low"

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "concentration": conc,
                    "concentration_ug_m3": conc * 1e9,  # Convert to μg/m³
                    "risk_level": risk,
                    "distance_m": math.sqrt(x**2 + y**2)
                }
            })

    return features

def predict_drift(
    source_lat: float,
    source_lon: float,
    lbs_applied: float,
    application_hours: float,
    wind_speed: float,
    wind_direction: float,
    is_daytime: bool = True,
    cloud_cover: float = 0.5
) -> dict:
    """
    Main function to predict pesticide drift from a spray event.

    Returns GeoJSON FeatureCollection with drift plume visualization.
    """
    stability = get_stability_class(wind_speed, is_daytime, cloud_cover)

    # Calculate emission rate (lbs/hour)
    emission_rate = lbs_applied / max(application_hours, 0.5)

    params = DriftParams(
        source_lat=source_lat,
        source_lon=source_lon,
        emission_rate=emission_rate,
        wind_speed=max(wind_speed, 0.5),  # Minimum wind speed
        wind_direction=wind_direction,
        stability_class=stability
    )

    features = calculate_drift_plume(params)

    # Add source point
    features.insert(0, {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [source_lon, source_lat]
        },
        "properties": {
            "type": "source",
            "lbs_applied": lbs_applied,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "stability_class": stability
        }
    })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "stability_class": stability,
            "emission_rate_lbs_hr": emission_rate,
            "max_distance_m": 5000
        }
    }
