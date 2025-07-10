#!/usr/bin/env python3
"""
Initialize the database for development
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.database.base import Base
from app.core.config import settings
from app.models.appraisal import Appraisal
from app.models.user import User

def init_database():
    """Initialize the database with all tables"""
    print("Initializing database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    
    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Created tables: {', '.join(tables)}")

if __name__ == "__main__":
    init_database()