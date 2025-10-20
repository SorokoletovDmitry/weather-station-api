from database import engine
import models

def check_database():
    print("🔍 Checking database setup...")
    
    try:
        # Создаем таблицы
        models.Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Проверяем существование таблиц
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['locations', 'weather_stations', 'sensor_types', 'weather_data', 'alerts']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print(f"✅ All tables created: {', '.join(tables)}")
            return True
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = check_database()
    exit(0 if success else 1)