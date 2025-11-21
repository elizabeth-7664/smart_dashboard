# app/database/setup.py
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


DATABASE_URL = "postgresql+asyncpg://smartuser:gideonmunyao%40254@localhost:5432/smart_dashboard"

engine = create_async_engine(DATABASE_URL, echo=True)

async_session =  sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
class Base(DeclarativeBase):
    pass
