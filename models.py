from peewee import *
from datetime import datetime
import json
from typing import Optional, Dict, Any

# Настройка подключения к базе данных SQLite
database = SqliteDatabase('weather_stations.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64,
    'foreign_keys': 1,
})

class BaseModel(Model):
    """Базовая модель с общими полями"""
    id: AutoField  # Явное указание типа для Pylance
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super(BaseModel, self).save(*args, **kwargs)
    
    class Meta:
        database = database

class Location(BaseModel):
    """Местоположение метеостанции"""
    name = CharField(max_length=100, verbose_name='Название местоположения')
    latitude = DecimalField(max_digits=9, decimal_places=6, verbose_name='Широта')
    longitude = DecimalField(max_digits=9, decimal_places=6, verbose_name='Долгота')
    altitude = DecimalField(max_digits=6, decimal_places=2, null=True, verbose_name='Высота над уровнем моря (м)')
    address = TextField(null=True, verbose_name='Адрес')
    city = CharField(max_length=100, null=True, verbose_name='Город')
    country = CharField(max_length=100, null=True, verbose_name='Страна')
    is_active = BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        table_name = 'locations'
        indexes = (
            (('latitude', 'longitude'), True),  # Уникальные координаты
        )
    
    def __str__(self) -> str:
        return f"Location {self.id}: {self.name}"

class WeatherStation(BaseModel):
    """Метеостанция"""
    location = ForeignKeyField(
        Location,
        backref='stations',
        on_delete='CASCADE',
        verbose_name='Местоположение'
    )
    name = CharField(max_length=100, verbose_name='Название станции')
    station_code = CharField(max_length=50, unique=True, verbose_name='Код станции')
    manufacturer = CharField(max_length=100, null=True, verbose_name='Производитель')
    model = CharField(max_length=100, null=True, verbose_name='Модель')
    installation_date = DateField(verbose_name='Дата установки')
    last_maintenance = DateField(null=True, verbose_name='Последнее обслуживание')
    is_active = BooleanField(default=True, verbose_name='Активна')
    description = TextField(null=True, verbose_name='Описание')
    
    class Meta:
        table_name = 'weather_stations'
        indexes = (
            (('station_code',), True),
            (('is_active', 'installation_date'), False),
        )
    
    def __str__(self) -> str:
        return f"WeatherStation {self.id}: {self.name}"

class SensorType(BaseModel):
    """Типы датчиков погоды"""
    name = CharField(max_length=100, verbose_name='Название типа датчика')
    unit = CharField(max_length=20, verbose_name='Единица измерения')
    description = TextField(null=True, verbose_name='Описание')
    min_value = FloatField(null=True, verbose_name='Минимальное значение')
    max_value = FloatField(null=True, verbose_name='Максимальное значение')
    
    class Meta:
        table_name = 'sensor_types'
    
    def __str__(self) -> str:
        return f"SensorType {self.id}: {self.name} ({self.unit})"

class Sensor(BaseModel):
    """Датчик погоды"""
    station = ForeignKeyField(
        WeatherStation,
        backref='sensors',
        on_delete='CASCADE',
        verbose_name='Метеостанция'
    )
    sensor_type = ForeignKeyField(
        SensorType,
        backref='sensors',
        on_delete='RESTRICT',
        verbose_name='Тип датчика'
    )
    sensor_code = CharField(max_length=50, verbose_name='Код датчика')
    calibration_date = DateField(null=True, verbose_name='Дата калибровки')
    accuracy = FloatField(null=True, verbose_name='Точность (±)')
    is_active = BooleanField(default=True, verbose_name='Активен')
    
    class Meta:
        table_name = 'sensors'
        indexes = (
            (('station', 'sensor_code'), True),  # Уникальный код датчика в рамках станции
        )
    
    def __str__(self) -> str:
        return f"Sensor {self.id}: {self.sensor_code}"

class WeatherData(BaseModel):
    """Погодные данные"""
    sensor = ForeignKeyField(
        Sensor,
        backref='weather_data',
        on_delete='CASCADE',
        verbose_name='Датчик'
    )
    timestamp = DateTimeField(verbose_name='Время измерения', index=True)
    value = FloatField(verbose_name='Значение')
    quality = IntegerField(default=100, verbose_name='Качество данных (0-100)')
    raw_data = TextField(null=True, verbose_name='Сырые данные')
    
    class Meta:
        table_name = 'weather_data'
        indexes = (
            (('sensor', 'timestamp'), False),
        )
    
    def __str__(self) -> str:
        return f"WeatherData {self.id}: {self.sensor.sensor_type.name} = {self.value}"

class WeatherAlert(BaseModel):
    """Погодные предупреждения"""
    location = ForeignKeyField(
        Location,
        backref='alerts',
        on_delete='CASCADE',
        verbose_name='Местоположение'
    )
    alert_type = CharField(max_length=50, verbose_name='Тип предупреждения')
    severity = CharField(max_length=20, verbose_name='Серьезность')
    title = CharField(max_length=200, verbose_name='Заголовок')
    description = TextField(verbose_name='Описание')
    start_time = DateTimeField(verbose_name='Время начала')
    end_time = DateTimeField(verbose_name='Время окончания')
    issued_at = DateTimeField(verbose_name='Время выдачи')
    issuer = CharField(max_length=100, verbose_name='Источник')
    is_active = BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        table_name = 'weather_alerts'
        indexes = (
            (('location', 'start_time', 'end_time'), False),
            (('is_active', 'severity'), False),
        )
    
    def __str__(self) -> str:
        return f"WeatherAlert {self.id}: {self.alert_type} - {self.title}"

def create_tables():
    """Создание таблиц в базе данных"""
    tables = [Location, WeatherStation, SensorType, Sensor, WeatherData, WeatherAlert]
    
    try:
        database.connect()
        database.create_tables(tables, safe=True)
        print("✅ Таблицы успешно созданы")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
    finally:
        if not database.is_closed():
            database.close()

def initialize_database():
    """Инициализация базы данных с тестовыми данными"""
    create_tables()
    
    # Добавляем тестовые данные, если таблицы пустые
    if not Location.select().exists():
        from datetime import datetime, timedelta
        
        # Создаем типы датчиков
        sensor_types = [
            {"name": "Температура", "unit": "°C", "min_value": -50, "max_value": 60},
            {"name": "Влажность", "unit": "%", "min_value": 0, "max_value": 100},
            {"name": "Давление", "unit": "hPa", "min_value": 800, "max_value": 1100},
            {"name": "Скорость ветра", "unit": "м/с", "min_value": 0, "max_value": 100},
            {"name": "Направление ветра", "unit": "°", "min_value": 0, "max_value": 360},
            {"name": "Осадки", "unit": "мм", "min_value": 0, "max_value": 1000},
            {"name": "УФ-индекс", "unit": "индекс", "min_value": 0, "max_value": 15},
        ]
        
        for sensor_type_data in sensor_types:
            SensorType.create(**sensor_type_data)
        
        # Создаем местоположение
        location = Location.create(
            name="Москва, центр",
            latitude=55.7558,
            longitude=37.6173,
            altitude=156,
            address="Красная площадь, 1",
            city="Москва",
            country="Россия",
            is_active=True
        )
        
        # Создаем метеостанцию
        station = WeatherStation.create(
            location=location,
            name="Главная метеостанция Москвы",
            station_code="MOSCOW-001",
            manufacturer="Vaisala",
            model="AWS310",
            installation_date=datetime.now().date(),
            last_maintenance=datetime.now().date(),
            is_active=True,
            description="Основная метеостанция мониторинга погоды в Москве"
        )
        
        # Создаем датчики
        sensors_to_create = [
            {"sensor_code": "TEMP-001", "sensor_type": 1},
            {"sensor_code": "HUM-001", "sensor_type": 2},
            {"sensor_code": "PRESS-001", "sensor_type": 3},
            {"sensor_code": "WIND-SPD-001", "sensor_type": 4},
        ]
        
        for sensor_data in sensors_to_create:
            Sensor.create(
                station=station,
                sensor_type=sensor_data["sensor_type"],
                sensor_code=sensor_data["sensor_code"],
                calibration_date=datetime.now().date(),
                accuracy=0.1,
                is_active=True
            )
        
        # Создаем тестовые погодные данные
        temp_sensor = Sensor.get(Sensor.sensor_code == "TEMP-001")
        for i in range(24):
            WeatherData.create(
                sensor=temp_sensor,
                timestamp=datetime.now() - timedelta(hours=i),
                value=15 + i * 0.5,
                quality=95,
                raw_data=json.dumps({"raw": 15 + i * 0.5, "battery": 98})
            )
        
        # Создаем тестовое предупреждение
        WeatherAlert.create(
            location=location,
            alert_type="ШТОРМ",
            severity="ВЫСОКАЯ",
            title="Штормовое предупреждение",
            description="Ожидается усиление ветра до 25 м/с",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=12),
            issued_at=datetime.now(),
            issuer="Гидрометцентр России",
            is_active=True
        )
        
        print("✅ Тестовые данные добавлены")
    
    print("✅ База данных инициализирована")

# Контекстный менеджер для работы с БД
class DBContext:
    """Контекстный менеджер для работы с базой данных"""
    def __enter__(self):
        database.connect()
        return database
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not database.is_closed():
            database.close()

if __name__ == "__main__":
    initialize_database()