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
    
    # App settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"mysql+pymysql://{self.TIDB_USER}:{self.TIDB_PASSWORD}@{self.TIDB_HOST}:{self.TIDB_PORT}/{self.TIDB_DATABASE}"

# Create global config instance
config = Config()