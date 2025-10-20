import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, engine, SessionLocal

client = TestClient(app)

def setup_module(module):
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

def teardown_module(module):
    # Очищаем БД после тестов
    Base.metadata.drop_all(bind=engine)

class TestAPI:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data

    def test_create_and_get_location(self):
        # Создаем location
        location_data = {
            "name": "Test API Location",
            "latitude": 55.7558,
            "longitude": 37.6173,
            "altitude": 156.0
        }
        response = client.post("/api/locations/", json=location_data)
        assert response.status_code == 201
        location = response.json()
        assert location["name"] == "Test API Location"
        
        # Получаем location
        response = client.get(f"/api/locations/{location['id']}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test API Location"

    def test_create_station(self):
        # Сначала создаем location
        location_data = {
            "name": "Location for Station Test",
            "latitude": 55.7558,
            "longitude": 37.6173
        }
        location_response = client.post("/api/locations/", json=location_data)
        location_id = location_response.json()["id"]
        
        # Создаем station
        station_data = {
            "name": "Test API Station",
            "model": "WS-2000",
            "location_id": location_id
        }
        response = client.post("/api/stations/", json=station_data)
        assert response.status_code == 201
        station = response.json()
        assert station["name"] == "Test API Station"

if __name__ == "__main__":
    pytest.main([__file__])