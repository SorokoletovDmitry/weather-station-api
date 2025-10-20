from fastapi import APIRouter
from schemas import LocationCreate

router = APIRouter()

@router.get("/")
def get_locations():
    return {"message": "Get locations"}

@router.post("/")
def create_location(location: LocationCreate):
    return {
        "message": "Create location",
        "data": {
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "altitude": location.altitude
        }
    }