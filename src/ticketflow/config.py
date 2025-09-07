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
    TIDB_CA: str = os.getenv("TIDB_CA", "")  # Path to CA cert if needed

    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    # OpenAI settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: Optional[str] = os.getenv("OPENROUTER_BASE_URL", None)
    # Jina AI settings
    JINA_API_KEY: str = os.getenv("JINA_API_KEY", "")
    # App settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    def validate(self) -> bool:
        """Check if all required config is present"""
        if not self.TIDB_HOST:
            print("❌ TIDB_HOST not set in .env")
            return False
        if not self.TIDB_USER:
            print("❌ TIDB_USER not set in .env")
            return False
        if not self.TIDB_PASSWORD:
            print("❌ TIDB_PASSWORD not set in .env")
            return False
        if not self.OPENROUTER_API_KEY:
            print("⚠️  OPENROUTER_API_KEY not set in .env (needed for chats)")
        if not self.JINA_API_KEY:
            print("⚠️  JINA_API_KEY not set in .env (needed for embeddings)")
        if not self.RESEND_API_KEY:
            print("⚠️  RESEND_API_KEY not set in .env (needed for email sending)")
            
        return True
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"mysql+pymysql://{self.TIDB_USER}:{self.TIDB_PASSWORD}@{self.TIDB_HOST}:{self.TIDB_PORT}/{self.TIDB_DATABASE}?ssl_ca={self.TIDB_CA}"

# Create global config instance
config = Config()