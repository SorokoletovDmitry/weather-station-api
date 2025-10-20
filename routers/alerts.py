from fastapi import APIRouter
from schemas import AlertCreate

router = APIRouter()

@router.get("/")
def get_alerts():
    return {"message": "Get alerts"}

@router.post("/")
def create_alert(alert: AlertCreate):
    return {
        "message": "Create alert",
        "data": {
            "name": alert.name,
            "condition": alert.condition,
            "severity": alert.severity,
            "is_active": alert.is_active,
            "sensor_type_id": alert.sensor_type_id
        }
    }