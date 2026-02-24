
import asyncio
from sqlalchemy import create_engine, inspect
from app.core.config import settings

def inspect_db():
    engine = create_engine(settings.DATABASE_URL_SYNC)
    inspector = inspect(engine)
    columns = inspector.get_columns('models')
    print("Columns in 'models' table:")
    for col in columns:
        print(f"- {col['name']} ({col['type']})")

if __name__ == "__main__":
    inspect_db()
