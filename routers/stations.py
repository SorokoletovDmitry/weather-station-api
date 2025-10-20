from fastapi import APIRouter
from schemas import WeatherStationCreate

router = APIRouter()

@router.get("/")
def get_stations():
    return {"message": "Get stations"}

@router.post("/")
def create_station(station: WeatherStationCreate):
    return {
        "message": "Create station",
        "data": {
            "name": station.name,
            "model": station.model,
            "location_id": station.location_id,
            "status": station.status
        }
    }