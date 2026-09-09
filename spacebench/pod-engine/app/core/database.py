from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .settings import settings
import asyncpg

engine = create_async_engine(settings.DATABASE_URL, connect_args={"prepared_statement_cache_size": 0}, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

print("[init] database.py loaded from POD Engine")

async def get_session():
    async with SessionLocal() as session:
        yield session

# ═════════ Create all tables from SQLAlchemy models. ═════════
class Base(DeclarativeBase):
    pass
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
