"""
Database models for the Voice Assistant API
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup with fallback to SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to SQLite for local development
    DATABASE_URL = "sqlite:///./voice_assistant.db"
    print("Warning: DATABASE_URL not set, using SQLite fallback")

# Test PostgreSQL connection and fallback to SQLite if needed
try:
    if DATABASE_URL.startswith("postgresql://"):
        test_engine = create_engine(DATABASE_URL)
        test_connection = test_engine.connect()
        test_connection.close()
        engine = test_engine
        print("Connected to PostgreSQL database")
    else:
        engine = create_engine(DATABASE_URL)
        print("Using SQLite database")
except Exception as e:
    print(f"PostgreSQL connection failed: {e}")
    print("Falling back to SQLite...")
    DATABASE_URL = "sqlite:///./voice_assistant.db"
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CommandLog(Base):
    """Store all voice commands and their responses"""
    __tablename__ = "command_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    command = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    source = Column(String(50), default="api")
    success = Column(Boolean, default=True)
    processing_time_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100), nullable=True)  # For future user tracking
    
    def __repr__(self):
        return f"<CommandLog(id={self.id}, command='{self.command[:50]}...', timestamp={self.timestamp})>"

class UserPreference(Base):
    """Store user preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreference(user_id='{self.user_id}', key='{self.preference_key}')>"

class SystemMetric(Base):
    """Store system performance and usage metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemMetric(name='{self.metric_name}', value={self.metric_value}, timestamp={self.timestamp})>"

class ApiKey(Base):
    """Store encrypted API keys for external services"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False, unique=True)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ApiKey(service='{self.service_name}', active={self.is_active})>"

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()