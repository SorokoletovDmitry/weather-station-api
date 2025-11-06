# 🌤️ Weather Station API

RESTful API для сбора и анализа данных с метеорологических станций. Курсовой проект по программированию на Python.

## 🚀 Быстрый старт

### Установка и запуск

1. **Клонируйте репозиторий**
```bash
git clone weather-station-api
cd weather_station
```
2. **Установите зависимости**
```bash
pip install -r requirements.txt
```
3. **Запустите сервер**

```bash
python main.py
```
4. **Откройте документацию**

http://localhost:8000/docs

📚 Документация API
После запуска сервера доступна автоматическая документация:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

Основные endpoints:
Метод	Endpoint	Описание
GET	/api/locations/	Получить все местоположения
POST	/api/locations/	Создать новое местоположение
GET	/api/stations/	Получить все станции
POST	/api/stations/	Создать новую станцию
GET	/api/sensor-types/	Получить типы датчиков
POST	/api/sensor-types/	Создать тип датчика
GET	/api/weather-data/	Получить погодные данные
POST	/api/weather-data/	Добавить данные измерений
GET	/api/alerts/	Получить предупреждения
POST	/api/alerts/	Создать предупреждение
🏗️ Архитектура системы
Технологический стек:
FastAPI - современный веб-фреймворк

SQLAlchemy - ORM для работы с БД

SQLite - база данных

Pydantic - валидация данных

Uvicorn - ASGI сервер

Модели данных:
📍 Locations - географические местоположения

🏭 Weather Stations - метеорологические станции

📊 Sensor Types - типы датчиков

📈 Weather Data - данные измерений

🔔 Alerts - система предупреждений

💡 Примеры использования
Создание местоположения:
```json
POST /api/locations/
{
  "name": "Москва, Красная площадь",
  "latitude": 55.7539,
  "longitude": 37.6208,
  "altitude": 130
}
```
Создание метеостанции:
```json
POST /api/stations/
{
  "name": "Главная городская станция", 
  "model": "WS-5000",
  "location_id": 1,
  "status": "active"
}
```
🎯 Особенности проекта
✅ Автоматическая документация - Swagger/OpenAPI
✅ Валидация данных - строгая типизация через Pydantic
✅ RESTful архитектура - стандартные endpoints
✅ Модульная структура - легко расширять
✅ Простота развертывания - минимальные зависимости

👨‍🎓 Автор
Сороколетов Дмитрий 4-1П9 - Курсовой проект по программированию
