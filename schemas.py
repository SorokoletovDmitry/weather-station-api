from pydantic import BaseModel
from typing import Optional

# Схемы для Locations
class LocationBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int
    
    class Config:
        from_attributes = True

# Схемы для Weather Stations
class WeatherStationBase(BaseModel):
    name: str
    model: Optional[str] = None
    status: Optional[str] = "active"
    location_id: int

class WeatherStationCreate(WeatherStationBase):
    pass

class WeatherStation(WeatherStationBase):
    id: int
    
    class Config:
        from_attributes = True

# Схемы для Sensor Types
class SensorTypeBase(BaseModel):
    name: str
    unit: str
    description: Optional[str] = None
    station_id: int

class SensorTypeCreate(SensorTypeBase):
    pass

class SensorType(SensorTypeBase):
    id: int
    
    class Config:
        from_attributes = True

# Схемы для Weather Data
class WeatherDataBase(BaseModel):
    value: float
    location_id: int
    station_id: int
    sensor_type_id: int

class WeatherDataCreate(WeatherDataBase):
    pass

class WeatherData(WeatherDataBase):
    id: int
    
    class Config:
        from_attributes = True

# Схемы для Alerts
class AlertBase(BaseModel):
    name: str
    condition: str
    severity: str
    is_active: bool = True
    sensor_type_id: int

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    
    class Config:
        from_attributes = True