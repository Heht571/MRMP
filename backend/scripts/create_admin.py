import asyncio
import logging
from sqlalchemy import select
from app.db.database import async_session_maker
from app.models.auth import User, Role
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_initial_data():
    async with async_session_maker() as db:
        logger.info("Creating initial data...")
        
        # 1. Create Admin Role
        result = await db.execute(select(Role).where(Role.name == "admin"))
        admin_role = result.scalar_one_or_none()
        
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="System Administrator",
                permissions=["*"]  # Superuser permission
            )
            db.add(admin_role)
            await db.flush()
            logger.info("✅ Created 'admin' role")
        else:
            logger.info("ℹ️ 'admin' role already exists")
            
        # 2. Create User Role
        result = await db.execute(select(Role).where(Role.name == "user"))
        user_role = result.scalar_one_or_none()
        
        if not user_role:
            user_role = Role(
                name="user",
                description="Regular User",
                permissions=["instance:read", "model:read"]
            )
            db.add(user_role)
            await db.flush()
            logger.info("✅ Created 'user' role")
        else:
            logger.info("ℹ️ 'user' role already exists")

        # 3. Create Admin User
        result = await db.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="System Admin",
                hashed_password=get_password_hash("admin"),  # Default password: admin
                is_active=True,
                is_superuser=True
            )
            # Assign admin role
            admin_user.roles.append(admin_role)
            
            db.add(admin_user)
            await db.commit()
            logger.info("✅ Created 'admin' user (password: admin)")
        else:
            logger.info("ℹ️ 'admin' user already exists")
            
        # 4. Create Regular User
        result = await db.execute(select(User).where(User.username == "user"))
        regular_user = result.scalar_one_or_none()
        
        if not regular_user:
            regular_user = User(
                username="user",
                email="user@example.com",
                full_name="Demo User",
                hashed_password=get_password_hash("user"),  # Default password: user
                is_active=True,
                is_superuser=False
            )
            # Assign user role
            regular_user.roles.append(user_role)
            
            db.add(regular_user)
            await db.commit()
            logger.info("✅ Created 'user' user (password: user)")
        else:
            logger.info("ℹ️ 'user' user already exists")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_initial_data())
