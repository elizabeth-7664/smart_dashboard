# app/database/setup.py
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.models.sales import Base

DATABASE_URL = "postgresql+asyncpg://smartuser:gideonmunyao%40254@localhost:5432/smart_dashboard"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
