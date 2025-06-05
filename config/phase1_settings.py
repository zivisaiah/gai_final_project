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
    
    # Model configuration with fallback support
    # Core Agent Model
    CORE_AGENT_MODEL: str = os.getenv("CORE_AGENT_MODEL", "gpt-3.5-turbo")
    
    # Exit Advisor Model (fine-tuned if available, fallback to standard)
    EXIT_ADVISOR_FINE_TUNED_MODEL: str = os.getenv("EXIT_ADVISOR_FINE_TUNED_MODEL", "")
    EXIT_ADVISOR_FALLBACK_MODEL: str = os.getenv("EXIT_ADVISOR_FALLBACK_MODEL", "gpt-3.5-turbo")
    
    # Scheduling Advisor Model
    SCHEDULING_ADVISOR_MODEL: str = os.getenv("SCHEDULING_ADVISOR_MODEL", "gpt-3.5-turbo")
    
    # Info Advisor Model (for future Phase 3)
    INFO_ADVISOR_MODEL: str = os.getenv("INFO_ADVISOR_MODEL", "gpt-3.5-turbo")
    
    # Legacy support (deprecated - will be removed in future version)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Model parameters
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
    
    def get_exit_advisor_model(self) -> str:
        """Get Exit Advisor model with fallback logic."""
        if self.EXIT_ADVISOR_FINE_TUNED_MODEL:
            return self.EXIT_ADVISOR_FINE_TUNED_MODEL
        return self.EXIT_ADVISOR_FALLBACK_MODEL
    
    def get_core_agent_model(self) -> str:
        """Get Core Agent model."""
        return self.CORE_AGENT_MODEL
    
    def get_scheduling_advisor_model(self) -> str:
        """Get Scheduling Advisor model."""
        return self.SCHEDULING_ADVISOR_MODEL
    
    def get_info_advisor_model(self) -> str:
        """Get Info Advisor model."""
        return self.INFO_ADVISOR_MODEL
    
    def is_using_fine_tuned_exit_advisor(self) -> bool:
        """Check if using fine-tuned Exit Advisor model."""
        return bool(self.EXIT_ADVISOR_FINE_TUNED_MODEL)
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration as dictionary."""
        return {
            "api_key": self.OPENAI_API_KEY,
            "model": self.OPENAI_MODEL,  # Legacy support
            "temperature": self.OPENAI_TEMPERATURE,
            "max_tokens": self.OPENAI_MAX_TOKENS
        }
    
    def get_model_config(self, agent_type: str) -> dict:
        """Get model configuration for specific agent type."""
        model_map = {
            "core_agent": self.get_core_agent_model(),
            "exit_advisor": self.get_exit_advisor_model(),
            "scheduling_advisor": self.get_scheduling_advisor_model(),
            "info_advisor": self.get_info_advisor_model()
        }
        
        model_name = model_map.get(agent_type, self.OPENAI_MODEL)
        
        return {
            "api_key": self.OPENAI_API_KEY,
            "model_name": model_name,
            "temperature": self.OPENAI_TEMPERATURE,
            "max_tokens": self.OPENAI_MAX_TOKENS,
            "is_fine_tuned": model_name.startswith("ft:") if model_name else False
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
    
    print(f"\n📝 Model Configuration:")
    print(f"   Core Agent: {settings.get_core_agent_model()}")
    print(f"   Exit Advisor: {settings.get_exit_advisor_model()}")
    if settings.is_using_fine_tuned_exit_advisor():
        print(f"   ✅ Using fine-tuned Exit Advisor model")
    else:
        print(f"   ⚠️  Using fallback Exit Advisor model (set EXIT_ADVISOR_FINE_TUNED_MODEL for fine-tuned)")
    print(f"   Scheduling Advisor: {settings.get_scheduling_advisor_model()}")
    print(f"   Info Advisor: {settings.get_info_advisor_model()}")
    
    print(f"\n🗄️ Infrastructure:")
    print(f"   Database: {settings.DATABASE_URL}")
    print(f"   Streamlit Port: {settings.STREAMLIT_SERVER_PORT}")
    print(f"   Max Conversation History: {settings.MAX_CONVERSATION_HISTORY}")
    print(f"   Scheduling Days Ahead: {settings.SCHEDULING_DAYS_AHEAD}")
    
    if not settings.OPENAI_API_KEY:
        print("\n   ⚠️  WARNING: OPENAI_API_KEY not set!")
    else:
        print(f"\n   ✅ OpenAI API Key: ...{settings.OPENAI_API_KEY[-4:]}")


if __name__ == "__main__":
    print_settings_summary() 