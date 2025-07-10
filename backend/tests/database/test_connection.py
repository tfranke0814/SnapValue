"""
Tests for Database Connection & Configuration - Step 1 Database Models & Configuration
"""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.database.connection import engine, SessionLocal, get_db, Base


class TestDatabaseConnection:
    """Test cases for database connection and configuration."""
    
    def test_database_engine_creation(self):
        """Test that database engine is created properly."""
        assert engine is not None
        assert engine.url.drivername in ["postgresql", "sqlite"]
    
    def test_session_local_creation(self):
        """Test that SessionLocal is configured properly."""
        session = SessionLocal()
        assert session is not None
        session.close()
    
    def test_get_db_dependency(self):
        """Test the get_db dependency function."""
        db_generator = get_db()
        db_session = next(db_generator)
        
        assert db_session is not None
        assert isinstance(db_session, Session)
        
        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass  # Expected behavior
    
    def test_database_connection_alive(self, db_session: Session):
        """Test that database connection is alive and working."""
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    def test_database_tables_exist(self, db_session: Session):
        """Test that all required tables exist."""
        # Get all table names
        if engine.url.drivername == "sqlite":
            result = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        else:
            result = db_session.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ))
        
        table_names = [row[0] for row in result]
        
        # Check that our models' tables exist
        expected_tables = ["users", "appraisals", "market_data"]
        for table in expected_tables:
            assert table in table_names
    
    def test_database_metadata_creation(self):
        """Test that database metadata is properly created."""
        assert Base.metadata is not None
        
        # Check that our models are registered in metadata
        table_names = list(Base.metadata.tables.keys())
        expected_tables = ["users", "appraisals", "market_data"]
        
        for table in expected_tables:
            assert table in table_names
    
    def test_database_session_rollback(self, db_session: Session, sample_user_data):
        """Test database session rollback functionality."""
        from app.models.user import User
        
        # Create a user
        user = User(**sample_user_data)
        db_session.add(user)
        
        # Rollback before commit
        db_session.rollback()
        
        # Verify user was not saved
        users = db_session.query(User).filter_by(email=sample_user_data["email"]).all()
        assert len(users) == 0
    
    def test_database_session_commit(self, db_session: Session, sample_user_data):
        """Test database session commit functionality."""
        from app.models.user import User
        
        # Create a user
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        # Verify user was saved
        saved_user = db_session.query(User).filter_by(email=sample_user_data["email"]).first()
        assert saved_user is not None
        assert saved_user.email == sample_user_data["email"]
    
    def test_database_session_autoflush(self, db_session: Session, sample_user_data):
        """Test database session autoflush behavior."""
        from app.models.user import User
        
        # Create a user
        user = User(**sample_user_data)
        db_session.add(user)
        
        # Query should trigger autoflush
        users = db_session.query(User).filter_by(email=sample_user_data["email"]).all()
        
        # User should be found even without explicit commit
        assert len(users) == 1
        assert users[0].email == sample_user_data["email"]
    
    def test_database_transaction_isolation(self):
        """Test database transaction isolation."""
        from app.models.user import User
        
        # Create two separate sessions
        session1 = SessionLocal()
        session2 = SessionLocal()
        
        try:
            # Create user in session1
            user_data = {
                "email": "isolation_test@example.com",
                "api_key": "isolation_test_key",
                "is_active": True
            }
            user = User(**user_data)
            session1.add(user)
            session1.commit()
            
            # Verify user is visible in session2
            user_in_session2 = session2.query(User).filter_by(
                email="isolation_test@example.com"
            ).first()
            assert user_in_session2 is not None
            
        finally:
            session1.close()
            session2.close()


class TestDatabaseMigrations:
    """Test cases for database migrations."""
    
    def test_migration_schema_integrity(self, db_session: Session):
        """Test that migration schema maintains integrity."""
        # This would be more comprehensive with actual Alembic migrations
        # For now, check that all tables have required columns
        
        # Check users table structure
        if engine.url.drivername == "sqlite":
            result = db_session.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]  # Column names are in index 1
        else:
            result = db_session.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='users'"
            ))
            columns = [row[0] for row in result]
        
        expected_user_columns = ["id", "email", "api_key", "is_active", "created_at", "updated_at"]
        for col in expected_user_columns:
            assert col in columns
    
    def test_foreign_key_constraints(self, db_session: Session):
        """Test that foreign key constraints are properly set up."""
        from app.models.user import User
        from app.models.appraisal import Appraisal
        
        # Create user
        user_data = {
            "email": "fk_test@example.com",
            "api_key": "fk_test_key",
            "is_active": True
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Create appraisal
        appraisal = Appraisal(
            user_id=user.id,
            image_url="https://example.com/test.jpg",
            status="pending"
        )
        db_session.add(appraisal)
        db_session.commit()
        
        # Verify relationship works
        assert appraisal.user.id == user.id
        assert len(user.appraisals) == 1
        assert user.appraisals[0].id == appraisal.id
    
    def test_cascade_delete_behavior(self, db_session: Session):
        """Test cascade delete behavior."""
        from app.models.user import User
        from app.models.appraisal import Appraisal
        
        # Create user and appraisal
        user_data = {
            "email": "cascade_test@example.com",
            "api_key": "cascade_test_key",
            "is_active": True
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        appraisal = Appraisal(
            user_id=user.id,
            image_url="https://example.com/test.jpg",
            status="pending"
        )
        db_session.add(appraisal)
        db_session.commit()
        
        user_id = user.id
        appraisal_id = appraisal.id
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Verify appraisal was also deleted (cascade)
        remaining_appraisal = db_session.query(Appraisal).filter_by(id=appraisal_id).first()
        assert remaining_appraisal is None
