"""
GAI Final Project - Main Application Entry Point
Phase 1: Core Agent + Scheduling Advisor + Basic Streamlit UI
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.agents.core_agent import CoreAgent
from app.modules.database.sql_manager import SQLManager
from config.phase1_settings import Settings


def initialize_app():
    """Initialize the Phase 1 application components."""
    print("🚀 Initializing GAI Final Project - Phase 1")
    
    # Load settings
    settings = Settings()
    print(f"✅ Settings loaded for environment: {settings.ENVIRONMENT}")
    
    # Initialize database
    sql_manager = SQLManager(settings.DATABASE_URL)
    print("✅ Database connection initialized")
    
    # Initialize core agent
    core_agent = CoreAgent(
        openai_api_key=settings.OPENAI_API_KEY,
        sql_manager=sql_manager
    )
    print("✅ Core Agent initialized")
    
    return {
        'settings': settings,
        'sql_manager': sql_manager,
        'core_agent': core_agent
    }


def main():
    """Main application function."""
    try:
        components = initialize_app()
        print("\n🎯 Phase 1 Application Ready!")
        print("📝 Available components:")
        print("   - Core Agent (Continue/Schedule decisions)")
        print("   - SQL Manager (Database operations)")
        print("   - Settings (Configuration management)")
        print("\n💡 Next: Run the Streamlit UI with: streamlit run streamlit_app/streamlit_main.py")
        
        return components
        
    except Exception as e:
        print(f"❌ Error initializing application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 