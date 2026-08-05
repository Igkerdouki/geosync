from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from app.services.drift import predict_drift, get_stability_class

router = APIRouter()

class DriftRequest(BaseModel):
    source_lat: float
    source_lon: float
    lbs_applied: float
    application_hours: float = 1.0
    wind_speed: float  # m/s
    wind_direction: float  # degrees
    is_daytime: bool = True
    cloud_cover: float = 0.5

@router.post("/drift/predict")
def predict_drift_endpoint(request: DriftRequest):
    """
    Predict pesticide drift using Gaussian plume model.

    Returns GeoJSON with drift plume visualization points.
    """
    return predict_drift(
        source_lat=request.source_lat,
        source_lon=request.source_lon,
        lbs_applied=request.lbs_applied,
        application_hours=request.application_hours,
        wind_speed=request.wind_speed,
        wind_direction=request.wind_direction,
        is_daytime=request.is_daytime,
        cloud_cover=request.cloud_cover
    )

@router.get("/drift/predict")
def predict_drift_get(
    lat: float = Query(..., description="Source latitude"),
    lon: float = Query(..., description="Source longitude"),
    lbs: float = Query(..., description="Pounds of pesticide applied"),
    hours: float = Query(1.0, description="Application duration in hours"),
    wind_speed: float = Query(..., description="Wind speed in m/s"),
    wind_dir: float = Query(..., description="Wind direction (degrees, where wind comes FROM)"),
    daytime: bool = Query(True, description="Is it daytime?"),
    clouds: float = Query(0.5, description="Cloud cover (0-1)")
):
    """
    Predict pesticide drift using Gaussian plume model (GET version).
    """
    return predict_drift(
        source_lat=lat,
        source_lon=lon,
        lbs_applied=lbs,
        application_hours=hours,
        wind_speed=wind_speed,
        wind_direction=wind_dir,
        is_daytime=daytime,
        cloud_cover=clouds
    )

@router.get("/drift/stability")
def get_stability(
    wind_speed: float = Query(..., description="Wind speed in m/s"),
    daytime: bool = Query(True),
    clouds: float = Query(0.5)
):
    """Get atmospheric stability class based on conditions"""
    stability = get_stability_class(wind_speed, daytime, clouds)

    descriptions = {
        'A': 'Very unstable - Strong mixing, rapid dispersion',
        'B': 'Unstable - Good dispersion',
        'C': 'Slightly unstable - Moderate dispersion',
        'D': 'Neutral - Typical conditions',
        'E': 'Slightly stable - Reduced dispersion',
        'F': 'Stable - Poor dispersion, drift travels far'
    }

    return {
        "stability_class": stability,
        "description": descriptions.get(stability, "Unknown"),
        "conditions": {
            "wind_speed_ms": wind_speed,
            "is_daytime": daytime,
            "cloud_cover": clouds
        }
    }
