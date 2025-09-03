"""Configuration management for TicketFlow AI"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Database settings
    TIDB_HOST: str = os.getenv("TIDB_HOST", "localhost")
    TIDB_PORT: int = int(os.getenv("TIDB_PORT", "4000"))
    TIDB_USER: str = os.getenv("TIDB_USER", "root")
    TIDB_PASSWORD: str = os.getenv("TIDB_PASSWORD", "")
    TIDB_DATABASE: str = os.getenv("TIDB_DATABASE", "ticketflow")

    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL", None)
    
    # App settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    if not TIDB_HOST or not TIDB_PORT or not TIDB_USER or not TIDB_PASSWORD or not TIDB_DATABASE:
        raise ValueError("One or more TiDB environment variables are not set")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"mysql+pymysql://{self.TIDB_USER}:{self.TIDB_PASSWORD}@{self.TIDB_HOST}:{self.TIDB_PORT}/{self.TIDB_DATABASE}"

# Create global config instance
config = Config()