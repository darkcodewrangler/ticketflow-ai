"""
Database connection management for TicketFlow AI
"""

from typing import Generator
import logging
from typing import Optional
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# This will be the base for all our models
Base = declarative_base()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._connected = False
    
    def connect(self, database_url: str) -> bool:
        """
        Connect to TiDB database
        
        Args:
            database_url: Connection string like 'mysql+pymysql://user:pass@host:port/db'
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Validates connections before use
                echo=False  # Set to True for SQL debugging
            )
            
            # Test the connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection successful!")
                
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self._connected = False
            return False
    
    def get_session(self) -> Session:
        """Get a database session"""
        if not self._connected or not self.SessionLocal:
            raise Exception("Database not connected. Call connect() first.")
        
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self._connected = False
            logger.info("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions
    This will be used in the API routes
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()