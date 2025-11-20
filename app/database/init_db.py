# app/database/init_db.py
import asyncio
from app.database.setup import Base, engine

async def init_db():
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized!")


asyncio.run(init_db())
