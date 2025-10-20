from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float)
    
    weather_stations = relationship("WeatherStation", back_populates="location")
    weather_data = relationship("WeatherData", back_populates="location")

class WeatherStation(Base):
    __tablename__ = "weather_stations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    model = Column(String(100))
    installation_date = Column(DateTime, server_default=func.now())
    status = Column(String(20), default="active")
    
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    location = relationship("Location", back_populates="weather_stations")
    sensors = relationship("SensorType", back_populates="weather_station")
    weather_data = relationship("WeatherData", back_populates="weather_station")

class SensorType(Base):
    __tablename__ = "sensor_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    unit = Column(String(20), nullable=False)
    description = Column(Text)
    
    station_id = Column(Integer, ForeignKey("weather_stations.id"), nullable=False)
    
    weather_station = relationship("WeatherStation", back_populates="sensors")
    weather_data = relationship("WeatherData", back_populates="sensor_type")
    alerts = relationship("Alert", back_populates="sensor_type")

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    value = Column(Float, nullable=False)
    
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    station_id = Column(Integer, ForeignKey("weather_stations.id"), nullable=False)
    sensor_type_id = Column(Integer, ForeignKey("sensor_types.id"), nullable=False)
    
    location = relationship("Location", back_populates="weather_data")
    weather_station = relationship("WeatherStation", back_populates="weather_data")
    sensor_type = relationship("SensorType", back_populates="weather_data")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    condition = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    sensor_type_id = Column(Integer, ForeignKey("sensor_types.id"), nullable=False)
    
    sensor_type = relationship("SensorType", back_populates="alerts")