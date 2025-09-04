"""
FastAPI dependencies
"""

from sqlalchemy.orm import Session
from ..database import db_manager
from ..config import config

def get_db_session() -> Session:
    """Get database session dependency"""
    db_manager.connect(config.database_url)
    session = db_manager.get_session()
    try:
        yield session
    finally:
        db_manager.close()
