from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .settings import settings
import asyncpg

async def ensure_database_exists():
    postgres_url = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/postgres"
    )

    try:
        conn = await asyncpg.connect(postgres_url)

        # Database exists ?
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            settings.POSTGRES_DB
        )

        if not db_exists:
            print(f"Database '{settings.POSTGRES_DB}' not found. Creating...")

            await conn.execute(f'CREATE DATABASE "{settings.POSTGRES_DB}"')

            print(f"Database '{settings.POSTGRES_DB}' created successfully")
        else:
            print(f"Database '{settings.POSTGRES_DB}' already exists")

        await conn.close()

        # Connect to the database
        target_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        conn = await asyncpg.connect(target_url)

        schemas = ['public', 'pod']
        for schema in schemas:
            await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
            print(f"Schema '{schema}' ensured")

        await conn.close()
        print("Database setup complete!")

    except Exception as e:
        print(f"Error ensuring database exists: {e}")
        raise


engine = create_async_engine(settings.DATABASE_URL, connect_args={"prepared_statement_cache_size": 0}, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

print("[init] database.py loaded")

async def get_session():
    async with SessionLocal() as session:
        yield session

# ═════════ Create all tables from SQLAlchemy models. ═════════
class Base(DeclarativeBase):
    pass
async def init_models():
    async with engine.begin() as conn:

        if settings.RESET_DB:
            print("[db] Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)

        print("[db] Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
