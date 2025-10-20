from fastapi import FastAPI
from database import SessionLocal, engine
import models
from routers import locations, stations, weather_data, sensor_types, alerts

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Weather Station API",
    description="API для сбора и хранения данных с метеостанций",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])
app.include_router(stations.router, prefix="/api/stations", tags=["stations"])
app.include_router(weather_data.router, prefix="/api/weather-data", tags=["weather-data"])
app.include_router(sensor_types.router, prefix="/api/sensor-types", tags=["sensor-types"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])

@app.get("/")
async def root():
    return {
        "message": "Weather Station API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "locations": "/api/locations",
            "stations": "/api/stations", 
            "weather_data": "/api/weather-data",
            "sensor_types": "/api/sensor-types",
            "alerts": "/api/alerts"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)