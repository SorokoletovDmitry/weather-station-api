import requests
import json
from datetime import datetime, timedelta
import time

# Базовый URL API
BASE_URL = "http://localhost:8000"

def print_response(response, test_name):
    """Вспомогательная функция для вывода результатов теста"""
    print(f"\n{'='*60}")
    print(f"Тест: {test_name}")
    print(f"Статус: {response.status_code}")
    print(f"URL: {response.url}")
    if response.status_code >= 400:
        print(f"❌ Ошибка: {response.text}")
    else:
        print(f"✅ Успех!")
        if response.text:
            try:
                data = response.json()
                print(f"Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"Ответ: {response.text}")
    print(f"{'='*60}")

def test_health_check():
    """Позитивный тест: Проверка здоровья API"""
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check (Позитивный)")

def test_root():
    """Позитивный тест: Корневой эндпоинт"""
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Root Endpoint (Позитивный)")

def test_create_location_positive():
    """Позитивный тест: Создание местоположения"""
    location_data = {
        "name": "Тестовое местоположение",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "altitude": 156.0,
        "address": "Тестовый адрес 123",
        "city": "Москва",
        "country": "Россия",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/locations/", json=location_data)
    print_response(response, "CREATE Location (Позитивный)")
    
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_create_location_negative():
    """Негативный тест: Создание местоположения с некорректными координатами"""
    location_data = {
        "name": "Некорректное местоположение",
        "latitude": 200.0,  # Некорректная широта
        "longitude": 37.6173,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/locations/", json=location_data)
    print_response(response, "CREATE Location (Негативный - некорректные координаты)")

def test_create_duplicate_location():
    """Негативный тест: Создание дублирующегося местоположения"""
    location_data = {
        "name": "Дубликат местоположения",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/locations/", json=location_data)
    print_response(response, "CREATE Location (Негативный - дубликат координат)")

def test_create_station_positive(location_id):
    """Позитивный тест: Создание метеостанции"""
    if not location_id:
        print("⚠️ Пропуск теста: location_id не предоставлен")
        return None
    
    station_data = {
        "location_id": location_id,
        "name": "Тестовая метеостанция",
        "station_code": "TEST-001",
        "manufacturer": "Test Manufacturer",
        "model": "Test Model",
        "installation_date": datetime.now().date().isoformat(),
        "last_maintenance": datetime.now().date().isoformat(),
        "is_active": True,
        "description": "Тестовая станция для API тестирования"
    }
    
    response = requests.post(f"{BASE_URL}/stations/", json=station_data)
    print_response(response, "CREATE Station (Позитивный)")
    
    if response.status_code == 201:
        return response.json()["id"]
    return None

def test_create_station_negative():
    """Негативный тест: Создание метеостанции с несуществующим местоположением"""
    station_data = {
        "location_id": 9999,  # Несуществующее местоположение
        "name": "Несуществующая станция",
        "station_code": "NONEXISTENT-001",
        "installation_date": datetime.now().date().isoformat(),
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/stations/", json=station_data)
    print_response(response, "CREATE Station (Негативный - несуществующее местоположение)")

def test_create_weather_data_positive(station_id):
    """Позитивный тест: Добавление погодных данных"""
    if not station_id:
        print("⚠️ Пропуск теста: station_id не предоставлен")
        return None
    
    # Сначала получим датчики станции
    response = requests.get(f"{BASE_URL}/stations/{station_id}")
    if response.status_code != 200:
        print("⚠️ Не удалось получить данные станции")
        return None
    
    station_data = response.json()
    if not station_data.get("sensors"):
        print("⚠️ На станции нет датчиков")
        return None
    
    # Используем первый датчик
    sensor = station_data["sensors"][0]
    
    weather_data = {
        "sensor_id": sensor["id"],
        "timestamp": datetime.now().isoformat(),
        "value": 25.5,
        "quality": 95,
        "raw_data": {
            "raw_value": 25.5,
            "battery": 98,
            "signal_strength": 85
        }
    }
    
    response = requests.post(f"{BASE_URL}/weather-data/", json=weather_data)
    print_response(response, "CREATE Weather Data (Позитивный)")
    
    return response.json()["id"] if response.status_code == 201 else None

def test_create_weather_data_negative():
    """Негативный тест: Добавление погодных данных с некорректным значением"""
    weather_data = {
        "sensor_id": 1,  # Предполагаем существующий датчик
        "timestamp": datetime.now().isoformat(),
        "value": -999,  # Некорректное значение
        "quality": 95
    }
    
    response = requests.post(f"{BASE_URL}/weather-data/", json=weather_data)
    print_response(response, "CREATE Weather Data (Негативный - некорректное значение)")

def test_create_alert_positive(location_id):
    """Позитивный тест: Создание погодного предупреждения"""
    if not location_id:
        print("⚠️ Пропуск теста: location_id не предоставлен")
        return None
    
    alert_data = {
        "location_id": location_id,
        "alert_type": "TEST_ALERT",
        "severity": "СРЕДНЯЯ",
        "title": "Тестовое предупреждение",
        "description": "Это тестовое предупреждение создано через API",
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(hours=24)).isoformat(),
        "issued_at": datetime.now().isoformat(),
        "issuer": "API Test Suite",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
    print_response(response, "CREATE Alert (Позитивный)")
    
    return response.json()["id"] if response.status_code == 201 else None

def test_create_alert_negative(location_id):
    """Негативный тест: Создание предупреждения с некорректными датами"""
    if not location_id:
        print("⚠️ Пропуск теста: location_id не предоставлен")
        return None
    
    alert_data = {
        "location_id": location_id,
        "alert_type": "TEST_ALERT",
        "severity": "СРЕДНЯЯ",
        "title": "Предупреждение с ошибкой",
        "description": "Дата окончания раньше даты начала",
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() - timedelta(hours=1)).isoformat(),  # Ошибка!
        "issued_at": datetime.now().isoformat(),
        "issuer": "API Test Suite",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/alerts/", json=alert_data)
    print_response(response, "CREATE Alert (Негативный - некорректные даты)")

def test_get_locations():
    """Позитивный тест: Получение списка местоположений"""
    response = requests.get(f"{BASE_URL}/locations/")
    print_response(response, "GET Locations (Позитивный)")

def test_get_nonexistent_location():
    """Негативный тест: Получение несуществующего местоположения"""
    response = requests.get(f"{BASE_URL}/locations/9999")
    print_response(response, "GET Location (Негативный - несуществующее)")

def test_get_station_stats(station_id):
    """Позитивный тест: Получение статистики станции"""
    if not station_id:
        print("⚠️ Пропуск теста: station_id не предоставлен")
        return
    
    response = requests.get(f"{BASE_URL}/stations/{station_id}/stats?days=7")
    print_response(response, "GET Station Stats (Позитивный)")

def test_get_active_alerts():
    """Позитивный тест: Получение активных предупреждений"""
    response = requests.get(f"{BASE_URL}/alerts/active")
    print_response(response, "GET Active Alerts (Позитивный)")

def test_get_weather_summary(location_id):
    """Позитивный тест: Получение сводки погоды"""
    if not location_id:
        print("⚠️ Пропуск теста: location_id не предоставлен")
        return
    
    response = requests.get(f"{BASE_URL}/analytics/weather-summary?location_id={location_id}&hours=24")
    print_response(response, "GET Weather Summary (Позитивный)")

def test_get_station_health_report():
    """Позитивный тест: Получение отчета о работоспособности"""
    response = requests.get(f"{BASE_URL}/analytics/station-health?days=7")
    print_response(response, "GET Station Health Report (Позитивный)")

def test_concurrent_data_submission(station_id):
    """Тест конкурентной отправки данных"""
    if not station_id:
        print("⚠️ Пропуск теста: station_id не предоставлен")
        return
    
    # Получаем датчики станции
    response = requests.get(f"{BASE_URL}/stations/{station_id}")
    if response.status_code != 200:
        return
    
    station_data = response.json()
    sensors = station_data.get("sensors", [])
    
    if not sensors:
        print("⚠️ Нет датчиков для теста конкурентности")
        return
    
    print("\n🚀 Тест конкурентной отправки данных...")
    
    import threading
    
    def send_data(sensor_id, thread_num):
        for i in range(3):
            data = {
                "sensor_id": sensor_id,
                "timestamp": (datetime.now() + timedelta(minutes=i)).isoformat(),
                "value": 20.0 + i + thread_num,
                "quality": 95
            }
            try:
                response = requests.post(f"{BASE_URL}/weather-data/", json=data, timeout=5)
                print(f"  Поток {thread_num}, итерация {i+1}: {response.status_code}")
            except Exception as e:
                print(f"  Поток {thread_num}, итерация {i+1}: Ошибка - {e}")
            time.sleep(0.1)
    
    threads = []
    for i, sensor in enumerate(sensors[:3]):  # Используем первые 3 датчика
        thread = threading.Thread(target=send_data, args=(sensor["id"], i+1))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    print("✅ Тест конкурентности завершен")

def test_update_location(location_id):
    """Позитивный тест: Обновление местоположения"""
    if not location_id:
        print("⚠️ Пропуск теста: location_id не предоставлен")
        return
    
    update_data = {
        "name": "Обновленное тестовое местоположение",
        "latitude": 55.7559,  # Немного изменяем координаты
        "longitude": 37.6174,
        "altitude": 160.0,
        "city": "Москва",
        "country": "Россия",
        "is_active": True
    }
    
    response = requests.put(f"{BASE_URL}/locations/{location_id}", json=update_data)
    print_response(response, "UPDATE Location (Позитивный)")

def test_delete_location_negative():
    """Негативный тест: Удаление несуществующего местоположения"""
    response = requests.delete(f"{BASE_URL}/locations/9999")
    print_response(response, "DELETE Location (Негативный - несуществующее)")

def test_bulk_operations():
    """Тест массовых операций"""
    print("\n📊 Тест массовых операций...")
    
    # Создание нескольких местоположений
    locations_created = 0
    for i in range(3):
        location_data = {
            "name": f"Массовое местоположение {i+1}",
            "latitude": 55.7 + i * 0.01,
            "longitude": 37.6 + i * 0.01,
            "city": "Москва",
            "country": "Россия",
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/locations/", json=location_data)
        if response.status_code == 201:
            locations_created += 1
    
    print(f"  Создано местоположений: {locations_created}/3")
    
    # Получение всех местоположений
    response = requests.get(f"{BASE_URL}/locations/?limit=50")
    if response.status_code == 200:
        locations = response.json()
        print(f"  Всего местоположений в системе: {len(locations)}")
    
    print("✅ Тест массовых операций завершен")

def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ WEATHER STATIONS API")
    print(f"Базовая ссылка: {BASE_URL}")
    print("=" * 80)
    
    try:
        # Проверка доступности сервера
        test_health_check()
        test_root()
        
        print("\n📌 ПОЗИТИВНЫЕ ТЕСТЫ:")
        print("-" * 40)
        
        # Основной поток позитивных тестов
        location_id = test_create_location_positive()
        station_id = test_create_station_positive(location_id)
        
        if location_id:
            test_get_locations()
            test_get_station_stats(station_id)
            test_get_active_alerts()
            test_get_weather_summary(location_id)
            test_get_station_health_report()
            
            # Создание данных
            weather_data_id = test_create_weather_data_positive(station_id)
            alert_id = test_create_alert_positive(location_id)
            
            # Обновление
            test_update_location(location_id)
            
            # Конкурентность
            test_concurrent_data_submission(station_id)
            
            # Массовые операции
            test_bulk_operations()
        
        print("\n📌 НЕГАТИВНЫЕ ТЕСТЫ:")
        print("-" * 40)
        
        # Негативные тесты
        test_create_location_negative()
        test_create_duplicate_location()
        test_create_station_negative()
        test_create_weather_data_negative()
        
        if location_id:
            test_create_alert_negative(location_id)
        
        test_get_nonexistent_location()
        test_delete_location_negative()
        
        print("\n" + "=" * 80)
        print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        
        # Краткая статистика
        print("\n📊 СТАТИСТИКА ТЕСТИРОВАНИЯ:")
        print("  1. Проверена доступность API")
        print("  2. Протестированы CRUD операции для основных сущностей")
        print("  3. Проверена обработка ошибок и валидация данных")
        print("  4. Протестированы аналитические эндпоинты")
        print("  5. Проверена конкурентная работа")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ОШИБКА: Не удается подключиться к серверу")
        print("Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()