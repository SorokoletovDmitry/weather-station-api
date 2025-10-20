from fastapi import APIRouter
from schemas import WeatherDataCreate

router = APIRouter()

@router.get("/")
def get_weather_data():
    return {"message": "Get weather data"}

@router.post("/")
def create_weather_data(weather_data: WeatherDataCreate):
    return {
        "message": "Create weather data",
        "data": {
            "value": weather_data.value,
            "location_id": weather_data.location_id,
            "station_id": weather_data.station_id,
            "sensor_type_id": weather_data.sensor_type_id
        }
    }