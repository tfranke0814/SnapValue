#!/usr/bin/env python3
"""
Check the database contents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.appraisal import Appraisal
from app.models.user import User

def check_database():
    """Check what's in the database"""
    print("Checking database contents...")
    
    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check appraisals
        appraisals = db.query(Appraisal).all()
        print(f"Found {len(appraisals)} appraisals:")
        
        for appraisal in appraisals:
            print(f"  ID: {appraisal.id}")
            print(f"  User ID: {appraisal.user_id}")
            print(f"  Status: {appraisal.status}")
            print(f"  Created: {appraisal.created_at}")
            print(f"  Updated: {appraisal.updated_at}")
            print(f"  Completed: {appraisal.completed_at}")
            print(f"  Market Price: {appraisal.market_price}")
            print(f"  Error: {appraisal.error_message}")
            print("  ---")
        
        # Check users
        users = db.query(User).all()
        print(f"Found {len(users)} users:")
        
        for user in users:
            print(f"  ID: {user.id}")
            print("  ---")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_database()