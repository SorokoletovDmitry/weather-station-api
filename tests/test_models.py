import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base
from models import Location, WeatherStation, SensorType, WeatherData, Alert

# Тестовая БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestModels:
    @classmethod
    def setup_class(cls):
        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        cls.db = TestingSessionLocal()

    @classmethod
    def teardown_class(cls):
        cls.db.close()
        # Удаляем тестовую БД
        if os.path.exists("test.db"):
            os.remove("test.db")

    def test_location_creation(self):
        location = Location(
            name="Test Location",
            latitude=55.7558,
            longitude=37.6173,
            altitude=156.0
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        
        assert location.id is not None
        assert location.name == "Test Location"
        assert location.latitude == 55.7558

    def test_weather_station_creation(self):
        # Сначала создаем location
        location = Location(
            name="Test Location for Station",
            latitude=55.7558,
            longitude=37.6173
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        
        station = WeatherStation(
            name="Test Station",
            model="WS-1000",
            location_id=location.id
        )
        self.db.add(station)
        self.db.commit()
        self.db.refresh(station)
        
        assert station.id is not None
        assert station.name == "Test Station"
        assert station.location_id == location.id

if __name__ == "__main__":
    pytest.main([__file__])