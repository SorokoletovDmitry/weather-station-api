from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from peewee import fn, JOIN, DoesNotExist
from typing import List, Optional
from datetime import datetime, timedelta
import statistics
import json

from models import (
    Location, WeatherStation, SensorType, Sensor, WeatherData, WeatherAlert,
    create_tables, DBContext
)
from schemas import (
    LocationCreate, LocationResponse, LocationWithStations,
    WeatherStationCreate, WeatherStationResponse, WeatherStationWithSensors,
    SensorTypeCreate, SensorTypeResponse,
    SensorCreate, SensorResponse, SensorWithData,
    WeatherDataCreate, WeatherDataResponse, WeatherDataWithSensor,
    WeatherAlertCreate, WeatherAlertResponse, WeatherAlertWithLocation
)

app = FastAPI(
    title="Weather Stations API",
    version="1.0.0",
    description="API для сбора и хранения данных с метеостанций",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

@app.on_event("startup")
def startup():
    create_tables()
    print("🚀 Weather Stations API запущен")

# ========== CRUD для Location ==========
@app.post("/locations/", response_model=LocationResponse, status_code=201)
def create_location(location: LocationCreate):
    with DBContext():
        existing = Location.select().where(
            (Location.latitude == location.latitude) &
            (Location.longitude == location.longitude)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Местоположение с такими координатами уже существует")
        location_db = Location.create(**location.model_dump())
        return LocationResponse.model_validate(location_db.__data__)

@app.get("/locations/", response_model=List[LocationResponse])
def read_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = True,
    city: Optional[str] = None,
    country: Optional[str] = None
):
    with DBContext():
        query = Location.select()
        if active_only:
            query = query.where(Location.is_active == True)
        if city:
            query = query.where(Location.city.contains(city))
        if country:
            query = query.where(Location.country.contains(country))
        locations = query.offset(skip).limit(limit)
        return [LocationResponse.model_validate(loc.__data__) for loc in locations]

@app.get("/locations/{location_id}", response_model=LocationWithStations)
def read_location(location_id: int):
    with DBContext():
        try:
            location = Location.get(Location.id == location_id)
            stations = []
            for station in location.stations.where(WeatherStation.is_active == True):
                stations.append(WeatherStationResponse.model_validate(station.__data__))
            active_alerts = []
            now = datetime.now()
            for alert in location.alerts.where(
                (WeatherAlert.is_active == True) &
                (WeatherAlert.start_time <= now) &
                (WeatherAlert.end_time >= now)
            ):
                active_alerts.append(WeatherAlertResponse.model_validate(alert.__data__))
            location_data = LocationWithStations.model_validate(location.__data__)
            location_data.stations = stations
            location_data.active_alerts = active_alerts
            return location_data
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Местоположение не найдено")

@app.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, location: LocationCreate):
    with DBContext():
        try:
            location_db = Location.get(Location.id == location_id)
            if (location_db.latitude != location.latitude or 
                location_db.longitude != location.longitude):
                existing = Location.select().where(
                    (Location.latitude == location.latitude) &
                    (Location.longitude == location.longitude) &
                    (Location.id != location_id)
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Местоположение с такими координатами уже существует")
            for key, value in location.model_dump().items():
                setattr(location_db, key, value)
            location_db.save()
            return LocationResponse.model_validate(location_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Местоположение не найдено")

@app.delete("/locations/{location_id}")
def delete_location(location_id: int):
    with DBContext():
        try:
            location = Location.get(Location.id == location_id)
            location.delete_instance()
            return {"message": "Местоположение успешно удалено"}
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Местоположение не найдено")

# ========== CRUD для WeatherStation ==========
@app.post("/stations/", response_model=WeatherStationResponse, status_code=201)
def create_station(station: WeatherStationCreate):
    with DBContext():
        try:
            Location.get(Location.id == station.location_id)
            existing = WeatherStation.select().where(
                WeatherStation.station_code == station.station_code
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Станция с таким кодом уже существует")
            station_db = WeatherStation.create(**station.model_dump())
            return WeatherStationResponse.model_validate(station_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Местоположение не найдено")

@app.get("/stations/", response_model=List[WeatherStationResponse])
def read_stations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = True,
    location_id: Optional[int] = None
):
    with DBContext():
        query = WeatherStation.select()
        if active_only:
            query = query.where(WeatherStation.is_active == True)
        if location_id:
            query = query.where(WeatherStation.location == location_id)
        stations = query.offset(skip).limit(limit)
        return [WeatherStationResponse.model_validate(station.__data__) for station in stations]

@app.get("/stations/{station_id}", response_model=WeatherStationWithSensors)
def read_station(station_id: int):
    with DBContext():
        try:
            station = WeatherStation.get(WeatherStation.id == station_id)
            sensors_with_types = []
            for sensor in station.sensors:
                sensor_data = SensorWithData.model_validate(sensor.__data__)
                sensor_data.sensor_type = SensorTypeResponse.model_validate(sensor.sensor_type.__data__)
                data_query = sensor.weather_data
                data_count = data_query.count()
                sensor_data.data_count = data_count
                if data_count > 0:
                    latest = data_query.order_by(WeatherData.timestamp.desc()).first()
                    sensor_data.latest_data = WeatherDataResponse.model_validate(latest.__data__)
                    values = [d.value for d in data_query]
                    sensor_data.avg_value = statistics.mean(values) if values else None
                    sensor_data.min_value = min(values) if values else None
                    sensor_data.max_value = max(values) if values else None
                sensors_with_types.append(sensor_data)
            station_data = WeatherStationWithSensors.model_validate(station.__data__)
            station_data.location = LocationResponse.model_validate(station.location.__data__)
            station_data.sensors = sensors_with_types
            return station_data
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Метеостанция не найдена")

@app.put("/stations/{station_id}", response_model=WeatherStationResponse)
def update_station(station_id: int, station: WeatherStationCreate):
    with DBContext():
        try:
            station_db = WeatherStation.get(WeatherStation.id == station_id)
            Location.get(Location.id == station.location_id)
            if station_db.station_code != station.station_code:
                existing = WeatherStation.select().where(
                    (WeatherStation.station_code == station.station_code) &
                    (WeatherStation.id != station_id)
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Станция с таким кодом уже существует")
            for key, value in station.model_dump().items():
                setattr(station_db, key, value)
            station_db.save()
            return WeatherStationResponse.model_validate(station_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Метеостанция не найдена")

@app.delete("/stations/{station_id}")
def delete_station(station_id: int):
    with DBContext():
        try:
            station = WeatherStation.get(WeatherStation.id == station_id)
            station.delete_instance()
            return {"message": "Метеостанция успешно удалена"}
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Метеостанция не найдена")

# ========== CRUD для SensorType ==========
@app.post("/sensor-types/", response_model=SensorTypeResponse, status_code=201)
def create_sensor_type(sensor_type: SensorTypeCreate):
    with DBContext():
        existing = SensorType.select().where(
            (SensorType.name == sensor_type.name) & (SensorType.unit == sensor_type.unit)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Тип датчика с таким названием и единицами уже существует")
        sensor_type_db = SensorType.create(**sensor_type.model_dump())
        return SensorTypeResponse.model_validate(sensor_type_db.__data__)

@app.get("/sensor-types/", response_model=List[SensorTypeResponse])
def read_sensor_types():
    with DBContext():
        sensor_types = SensorType.select()
        return [SensorTypeResponse.model_validate(st.__data__) for st in sensor_types]

@app.put("/sensor-types/{sensor_type_id}", response_model=SensorTypeResponse)
def update_sensor_type(sensor_type_id: int, sensor_type: SensorTypeCreate):
    with DBContext():
        try:
            sensor_type_db = SensorType.get(SensorType.id == sensor_type_id)
            for key, value in sensor_type.model_dump().items():
                setattr(sensor_type_db, key, value)
            sensor_type_db.save()
            return SensorTypeResponse.model_validate(sensor_type_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Тип датчика не найден")

@app.delete("/sensor-types/{sensor_type_id}")
def delete_sensor_type(sensor_type_id: int):
    with DBContext():
        try:
            sensor_type = SensorType.get(SensorType.id == sensor_type_id)
            sensor_type.delete_instance()
            return {"message": "Тип датчика успешно удален"}
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Тип датчика не найден")

# ========== CRUD для Sensor ==========
@app.post("/sensors/", response_model=SensorResponse, status_code=201)
def create_sensor(sensor: SensorCreate):
    with DBContext():
        try:
            WeatherStation.get(WeatherStation.id == sensor.station_id)
            SensorType.get(SensorType.id == sensor.sensor_type_id)
            existing = Sensor.select().where(
                (Sensor.station == sensor.station_id) &
                (Sensor.sensor_code == sensor.sensor_code)
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Датчик с таким кодом уже существует на этой станции")
            sensor_db = Sensor.create(**sensor.model_dump())
            return SensorResponse.model_validate(sensor_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Метеостанция или тип датчика не найдены")

@app.get("/sensors/", response_model=List[SensorResponse])
def read_sensors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    station_id: Optional[int] = None,
    sensor_type_id: Optional[int] = None,
    active_only: bool = True
):
    with DBContext():
        query = Sensor.select()
        if active_only:
            query = query.where(Sensor.is_active == True)
        if station_id:
            query = query.where(Sensor.station == station_id)
        if sensor_type_id:
            query = query.where(Sensor.sensor_type == sensor_type_id)
        sensors = query.offset(skip).limit(limit)
        return [SensorResponse.model_validate(sensor.__data__) for sensor in sensors]

@app.get("/sensors/{sensor_id}", response_model=SensorWithData)
def read_sensor(sensor_id: int):
    with DBContext():
        try:
            sensor = Sensor.get(Sensor.id == sensor_id)
            sensor_data = SensorWithData.model_validate(sensor.__data__)
            sensor_data.sensor_type = SensorTypeResponse.model_validate(sensor.sensor_type.__data__)
            data_query = sensor.weather_data
            data_count = data_query.count()
            sensor_data.data_count = data_count
            if data_count > 0:
                latest = data_query.order_by(WeatherData.timestamp.desc()).first()
                sensor_data.latest_data = WeatherDataResponse.model_validate(latest.__data__)
                values = [d.value for d in data_query]
                sensor_data.avg_value = statistics.mean(values) if values else None
                sensor_data.min_value = min(values) if values else None
                sensor_data.max_value = max(values) if values else None
            return sensor_data
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Датчик не найден")

@app.put("/sensors/{sensor_id}", response_model=SensorResponse)
def update_sensor(sensor_id: int, sensor: SensorCreate):
    with DBContext():
        try:
            sensor_db = Sensor.get(Sensor.id == sensor_id)
            WeatherStation.get(WeatherStation.id == sensor.station_id)
            SensorType.get(SensorType.id == sensor.sensor_type_id)
            if sensor_db.sensor_code != sensor.sensor_code:
                existing = Sensor.select().where(
                    (Sensor.station == sensor.station_id) &
                    (Sensor.sensor_code == sensor.sensor_code) &
                    (Sensor.id != sensor_id)
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Датчик с таким кодом уже существует на этой станции")
            for key, value in sensor.model_dump().items():
                setattr(sensor_db, key, value)
            sensor_db.save()
            return SensorResponse.model_validate(sensor_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Датчик не найден")

@app.delete("/sensors/{sensor_id}")
def delete_sensor(sensor_id: int):
    with DBContext():
        try:
            sensor = Sensor.get(Sensor.id == sensor_id)
            sensor.delete_instance()
            return {"message": "Датчик успешно удален"}
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Датчик не найден")

@app.get("/sensors/{sensor_id}/data", response_model=List[WeatherDataResponse])
def get_sensor_data(
    sensor_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(1000, ge=1, le=10000)
):
    with DBContext():
        try:
            sensor = Sensor.get(Sensor.id == sensor_id)
            query = sensor.weather_data
            if start_time:
                query = query.where(WeatherData.timestamp >= start_time)
            if end_time:
                query = query.where(WeatherData.timestamp <= end_time)
            data = query.order_by(WeatherData.timestamp.desc()).limit(limit)
            return [WeatherDataResponse.model_validate(d.__data__) for d in data]
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Датчик не найден")

# ========== CRUD для WeatherData ==========
@app.post("/weather-data/", response_model=WeatherDataResponse, status_code=201)
def create_weather_data(data: WeatherDataCreate, background_tasks: BackgroundTasks):
    with DBContext():
        try:
            sensor = Sensor.get(Sensor.id == data.sensor_id)
            sensor_type = sensor.sensor_type
            if sensor_type.min_value is not None and data.value < sensor_type.min_value:
                raise HTTPException(status_code=400, detail=f"Значение ниже минимального ({sensor_type.min_value})")
            if sensor_type.max_value is not None and data.value > sensor_type.max_value:
                raise HTTPException(status_code=400, detail=f"Значение выше максимального ({sensor_type.max_value})")
            data_dict = data.model_dump()
            if isinstance(data_dict.get('raw_data'), dict):
                data_dict['raw_data'] = json.dumps(data_dict['raw_data'])
            data_db = WeatherData.create(**data_dict)
            background_tasks.add_task(check_for_anomalies, data_db.id)
            return WeatherDataResponse.model_validate(data_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Датчик не найден")

async def check_for_anomalies(data_id: int):
    with DBContext():
        try:
            data = WeatherData.get(WeatherData.id == data_id)
            sensor = data.sensor
            sensor_type = sensor.sensor_type
            historical_data = sensor.weather_data.where(
                WeatherData.timestamp >= datetime.now() - timedelta(days=7)
            ).limit(100)
            if historical_data.count() > 10:
                values = [d.value for d in historical_data]
                mean = statistics.mean(values)
                stdev = statistics.stdev(values) if len(values) > 1 else 0
                if stdev > 0 and abs(data.value - mean) > 3 * stdev:
                    print(f"⚠️ Аномальное значение: {data.value} (среднее: {mean})")
                    WeatherAlert.create(
                        location_id=sensor.station.location.id,
                        alert_type="DATA_ANOMALY",
                        severity="СРЕДНЯЯ",
                        title=f"Аномальное значение датчика {sensor.sensor_code}",
                        description=f"Значение {data.value}{sensor_type.unit} значительно отличается от ожидаемого",
                        start_time=data.timestamp,
                        end_time=data.timestamp + timedelta(hours=1),
                        issued_at=datetime.now(),
                        issuer="Система мониторинга",
                        is_active=True
                    )
        except Exception as e:
            print(f"Ошибка при проверке аномалий: {e}")

@app.get("/weather-data/latest", response_model=List[WeatherDataWithSensor])
def get_latest_weather_data(
    station_id: Optional[int] = None,
    location_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    with DBContext():
        query = (WeatherData
                 .select(WeatherData, Sensor, SensorType)
                 .join(Sensor)
                 .join(SensorType))
        if station_id:
            query = query.where(Sensor.station == station_id)
        elif location_id:
            query = (query
                     .join(WeatherStation)
                     .where(WeatherStation.location == location_id))
        data = query.order_by(WeatherData.timestamp.desc()).limit(limit)
        result = []
        for item in data:
            data_with_sensor = WeatherDataWithSensor.model_validate(item.__data__)
            sensor_data = SensorWithData.model_validate(item.sensor.__data__)
            sensor_data.sensor_type = SensorTypeResponse.model_validate(item.sensor.sensor_type.__data__)
            data_with_sensor.sensor = sensor_data
            result.append(data_with_sensor)
        return result

@app.put("/weather-data/{weather_data_id}", response_model=WeatherDataResponse)
def update_weather_data(weather_data_id: int, data: WeatherDataCreate):
    with DBContext():
        try:
            data_db = WeatherData.get(WeatherData.id == weather_data_id)
            sensor = Sensor.get(Sensor.id == data.sensor_id)
            sensor_type = sensor.sensor_type
            if sensor_type.min_value is not None and data.value < sensor_type.min_value:
                raise HTTPException(status_code=400, detail=f"Значение ниже минимального ({sensor_type.min_value})")
            if sensor_type.max_value is not None and data.value > sensor_type.max_value:
                raise HTTPException(status_code=400, detail=f"Значение выше максимального ({sensor_type.max_value})")
            for key, value in data.model_dump().items():
                setattr(data_db, key, value)
            data_db.save()
            return WeatherDataResponse.model_validate(data_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Данные не найдены")

@app.delete("/weather-data/{weather_data_id}")
def delete_weather_data(weather_data_id: int):
    with DBContext():
        try:
            data = WeatherData.get(WeatherData.id == weather_data_id)
            data.delete_instance()
            return {"message": "Данные успешно удалены"}
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Данные не найдены")

# ========== CRUD для WeatherAlert ==========
@app.post("/alerts/", response_model=WeatherAlertResponse, status_code=201)
def create_weather_alert(alert: WeatherAlertCreate):
    with DBContext():
        try:
            Location.get(Location.id == alert.location_id)
            alert_db = WeatherAlert.create(**alert.model_dump())
            return WeatherAlertResponse.model_validate(alert_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Местоположение не найдено")

@app.get("/alerts/", response_model=List[WeatherAlertWithLocation])
def read_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = True,
    location_id: Optional[int] = None,
    severity: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    with DBContext():
        query = WeatherAlert.select(WeatherAlert, Location).join(Location)
        if active_only:
            query = query.where(WeatherAlert.is_active == True)
        if location_id:
            query = query.where(WeatherAlert.location == location_id)
        if severity:
            query = query.where(WeatherAlert.severity == severity)
        if start_time:
            query = query.where(WeatherAlert.start_time >= start_time)
        if end_time:
            query = query.where(WeatherAlert.end_time <= end_time)
        alerts = query.order_by(WeatherAlert.issued_at.desc()).offset(skip).limit(limit)
        result = []
        for alert in alerts:
            alert_with_loc = WeatherAlertWithLocation.model_validate(alert.__data__)
            alert_with_loc.location = LocationResponse.model_validate(alert.location.__data__)
            result.append(alert_with_loc)
        return result

@app.get("/alerts/active", response_model=List[WeatherAlertWithLocation])
def get_active_alerts():
    with DBContext():
        now = datetime.now()
        alerts = (WeatherAlert
                  .select(WeatherAlert, Location)
                  .join(Location)
                  .where(
                      (WeatherAlert.is_active == True) &
                      (WeatherAlert.start_time <= now) &
                      (WeatherAlert.end_time >= now)
                  )
                  .order_by(WeatherAlert.severity.desc(), WeatherAlert.issued_at.desc()))
        result = []
        for alert in alerts:
            alert_with_loc = WeatherAlertWithLocation.model_validate(alert.__data__)
            alert_with_loc.location = LocationResponse.model_validate(alert.location.__data__)
            result.append(alert_with_loc)
        return result

@app.get("/alerts/{alert_id}", response_model=WeatherAlertWithLocation)
def read_alert(alert_id: int):
    with DBContext():
        try:
            alert = WeatherAlert.get(WeatherAlert.id == alert_id)
            alert_with_loc = WeatherAlertWithLocation.model_validate(alert.__data__)
            alert_with_loc.location = LocationResponse.model_validate(alert.location.__data__)
            return alert_with_loc
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Предупреждение не найдено")

@app.put("/alerts/{alert_id}", response_model=WeatherAlertResponse)
def update_weather_alert(alert_id: int, alert: WeatherAlertCreate):
    with DBContext():
        try:
            alert_db = WeatherAlert.get(WeatherAlert.id == alert_id)
            Location.get(Location.id == alert.location_id)
            for key, value in alert.model_dump().items():
                setattr(alert_db, key, value)
            alert_db.save()
            return WeatherAlertResponse.model_validate(alert_db.__data__)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Предупреждение не найдено")

@app.delete("/alerts/{alert_id}")
def delete_weather_alert(alert_id: int):
    with DBContext():
        try:
            alert = WeatherAlert.get(WeatherAlert.id == alert_id)
            alert.delete_instance()
            return {"message": "Предупреждение успешно удалено"}
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Предупреждение не найдено")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)