#!/usr/bin/env python3
"""
Database initialization script
Creates all tables required for the SkillPack application
"""

import asyncio
from sqlalchemy import text
from db.database import async_engine, Base
from db.models import *

async def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    
    async with async_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created successfully!")
        
        # Verify tables exist
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

if __name__ == "__main__":
    asyncio.run(init_database())
