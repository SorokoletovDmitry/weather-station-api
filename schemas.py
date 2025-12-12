from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime, date
from typing import List, Optional, Dict, Any

# Базовые схемы
class LocationBase(BaseModel):
    name: str = Field(..., max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True

class WeatherStationBase(BaseModel):
    location_id: int
    name: str = Field(..., max_length=100)
    station_code: str = Field(..., max_length=50)
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    installation_date: date
    last_maintenance: Optional[date] = None
    is_active: bool = True
    description: Optional[str] = None

class SensorTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    unit: str = Field(..., max_length=20)
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

class SensorBase(BaseModel):
    station_id: int
    sensor_type_id: int
    sensor_code: str = Field(..., max_length=50)
    calibration_date: Optional[date] = None
    accuracy: Optional[float] = None
    is_active: bool = True

class WeatherDataBase(BaseModel):
    sensor_id: int
    timestamp: datetime
    value: float
    quality: int = Field(..., ge=0, le=100)
    raw_data: Optional[Dict[str, Any]] = None

class WeatherAlertBase(BaseModel):
    location_id: int
    alert_type: str = Field(..., max_length=50)
    severity: str = Field(..., max_length=20)
    title: str = Field(..., max_length=200)
    description: str
    start_time: datetime
    end_time: datetime
    issued_at: datetime
    issuer: str = Field(..., max_length=100)
    is_active: bool = True

# Схемы для создания
class LocationCreate(LocationBase):
    pass

class WeatherStationCreate(WeatherStationBase):
    pass

class SensorTypeCreate(SensorTypeBase):
    pass

class SensorCreate(SensorBase):
    pass

class WeatherDataCreate(WeatherDataBase):
    pass

class WeatherAlertCreate(WeatherAlertBase):
    pass

# Схемы для ответов
class LocationResponse(LocationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class WeatherStationResponse(WeatherStationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SensorTypeResponse(SensorTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SensorResponse(SensorBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class WeatherDataResponse(WeatherDataBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class WeatherAlertResponse(WeatherAlertBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Схемы с отношениями
class SensorWithType(SensorResponse):
    sensor_type: 'SensorTypeResponse'

class WeatherStationWithSensors(WeatherStationResponse):
    location: 'LocationResponse'
    sensors: List[SensorWithType] = []

class LocationWithStations(LocationResponse):
    stations: List['WeatherStationResponse'] = []
    active_alerts: List['WeatherAlertResponse'] = []

class WeatherDataWithSensor(WeatherDataResponse):
    sensor: 'SensorWithData'

class SensorWithData(SensorResponse):
    sensor_type: 'SensorTypeResponse'
    latest_data: Optional['WeatherDataResponse'] = None
    data_count: int = 0
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

class WeatherAlertWithLocation(WeatherAlertResponse):
    location: 'LocationResponse'

# Обновляем ссылки на типы
SensorWithType.model_rebuild()
WeatherStationWithSensors.model_rebuild()
LocationWithStations.model_rebuild()
WeatherDataWithSensor.model_rebuild()
SensorWithData.model_rebuild()
WeatherAlertWithLocation.model_rebuild()