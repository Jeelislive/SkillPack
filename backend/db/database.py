from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from config import get_settings

settings = get_settings()


# Async engine — NullPool for Vercel serverless (session pooler, port 5432)
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine (for cron jobs / pipeline scripts)
sync_engine = create_engine(
    settings.sync_database_url,
    poolclass=NullPool,
)
SyncSessionLocal = sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
