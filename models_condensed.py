"""
Condensed Database models for the Voice Assistant API
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Single function database setup
def setup_database():
    """Setup database with PostgreSQL fallback to SQLite"""
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./voice_assistant.db")
    
    if db_url.startswith("postgresql://"):
        try:
            engine = create_engine(db_url)
            engine.connect().close()
            print("Connected to PostgreSQL database")
            return engine
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}\nFalling back to SQLite...")
    
    return create_engine("sqlite:///./voice_assistant.db")

engine = setup_database()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Base model class with common patterns
class BaseTable(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TimestampedTable(BaseTable):
    __abstract__ = True
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Condensed models using inheritance
class CommandLog(BaseTable):
    __tablename__ = "command_logs"
    command = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    source = Column(String(50), default="api")
    success = Column(Boolean, default=True)
    processing_time_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100), nullable=True)

class UserPreference(TimestampedTable):
    __tablename__ = "user_preferences"
    user_id = Column(String(100), nullable=False, index=True)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text, nullable=False)

class SystemMetric(BaseTable):
    __tablename__ = "system_metrics"
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ApiKey(TimestampedTable):
    __tablename__ = "api_keys"
    service_name = Column(String(100), nullable=False, unique=True)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

# Simplified database utilities
def create_tables(): Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()