import asyncio
import logging
from app.db.database import async_engine, Base
from app.models.auth import User, Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_models():
    async with async_engine.begin() as conn:
        logger.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_models())
