"""Initialize database with Master admin account."""
import asyncio
import secrets
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User

# Import all models
import app.models  # noqa: F401


async def init_db():
    settings = get_settings()

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("数据库表创建成功")

    # Create Master admin
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == "master")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Master管理员已存在: {existing.username} ({existing.phone})")
            return

        password = secrets.token_urlsafe(12)
        admin = User(
            username=settings.MASTER_USERNAME,
            phone=settings.MASTER_PHONE,
            password_hash=hash_password(password),
            full_name="系统管理员",
            role="master",
            is_active=True,
        )
        session.add(admin)
        await session.commit()

        print("=" * 50)
        print("Master管理员账户创建成功!")
        print(f"  用户名: {settings.MASTER_USERNAME}")
        print(f"  手机号: {settings.MASTER_PHONE}")
        print(f"  密码:   {password}")
        print("=" * 50)
        print("请妥善保存以上信息，密码不会再次显示!")


if __name__ == "__main__":
    asyncio.run(init_db())
