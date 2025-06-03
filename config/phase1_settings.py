"""
Phase 1 Settings and Configuration
Environment variable management for Core Agent + Scheduling system
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings for Phase 1."""
    
    # Environment settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # OpenAI API settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    
    # Database settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Streamlit settings
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")
    
    # Application settings
    APP_NAME: str = "GAI Final Project - Phase 1"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "SMS-based Recruitment Chatbot - Core Agent + Scheduling"
    
    # Conversation settings
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # Scheduling settings
    DEFAULT_INTERVIEW_DURATION_MINUTES: int = int(os.getenv("DEFAULT_INTERVIEW_DURATION_MINUTES", "60"))
    MAX_SLOTS_TO_SHOW: int = int(os.getenv("MAX_SLOTS_TO_SHOW", "5"))
    SCHEDULING_DAYS_AHEAD: int = int(os.getenv("SCHEDULING_DAYS_AHEAD", "14"))
    
    @validator('OPENAI_API_KEY')
    def openai_api_key_must_be_set(cls, v):
        """Validate that OpenAI API key is provided."""
        if not v and os.getenv("ENVIRONMENT", "development") == "production":
            raise ValueError('OPENAI_API_KEY must be set in production')
        return v
    
    @validator('DATABASE_URL', pre=True)
    def set_database_url(cls, v):
        """Set default database URL if not provided."""
        if not v:
            # Default to SQLite database in data directory
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            return f"sqlite:///{data_dir}/recruitment.db"
        return v
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration as dictionary."""
        return {
            "api_key": self.OPENAI_API_KEY,
            "model": self.OPENAI_MODEL,
            "temperature": self.OPENAI_TEMPERATURE,
            "max_tokens": self.OPENAI_MAX_TOKENS
        }
    
    def get_database_config(self) -> dict:
        """Get database configuration as dictionary."""
        return {
            "database_url": self.DATABASE_URL
        }
    
    def get_streamlit_config(self) -> dict:
        """Get Streamlit configuration as dictionary."""
        return {
            "server_port": self.STREAMLIT_SERVER_PORT,
            "server_address": self.STREAMLIT_SERVER_ADDRESS
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() == "production"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def print_settings_summary():
    """Print a summary of current settings."""
    print("\n🔧 Phase 1 Configuration Summary:")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug Mode: {settings.DEBUG}")
    print(f"   OpenAI Model: {settings.OPENAI_MODEL}")
    print(f"   Database: {settings.DATABASE_URL}")
    print(f"   Streamlit Port: {settings.STREAMLIT_SERVER_PORT}")
    print(f"   Max Conversation History: {settings.MAX_CONVERSATION_HISTORY}")
    print(f"   Scheduling Days Ahead: {settings.SCHEDULING_DAYS_AHEAD}")
    
    if not settings.OPENAI_API_KEY:
        print("   ⚠️  WARNING: OPENAI_API_KEY not set!")
    else:
        print(f"   ✅ OpenAI API Key: ...{settings.OPENAI_API_KEY[-4:]}")


if __name__ == "__main__":
    print_settings_summary() 