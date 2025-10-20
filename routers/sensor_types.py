from fastapi import APIRouter
from schemas import SensorTypeCreate

router = APIRouter()

@router.get("/")
def get_sensor_types():
    return {"message": "Get sensor types"}

@router.post("/")
def create_sensor_type(sensor_type: SensorTypeCreate):
    return {
        "message": "Create sensor type",
        "data": {
            "name": sensor_type.name,
            "unit": sensor_type.unit,
            "description": sensor_type.description,
            "station_id": sensor_type.station_id
        }
    }