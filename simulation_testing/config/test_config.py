"""
Test Configuration for User Simulation
Separate testing environment configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestConfig:
    """Configuration for simulation testing environment"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    SIMULATION_ROOT = Path(__file__).parent.parent
    
    # Test environment settings
    TEST_DATABASE_URL = "sqlite:///./simulation_testing/results/test_recruitment.db"
    
    # API Configuration (using actual API key as requested)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE = 1.0
    OPENAI_MAX_TOKENS = 1000
    
    # Simulation settings
    DEFAULT_DELAY_BETWEEN_MESSAGES = 2  # seconds
    MAX_CONVERSATION_LENGTH = 20  # messages
    SIMULATION_TIMEOUT = 300  # seconds (5 minutes)
    
    # Logging configuration
    LOG_LEVEL = "INFO"
    LOG_FILE = SIMULATION_ROOT / "results" / "simulation.log"
    
    # Metrics collection
    COLLECT_RESPONSE_TIMES = True
    COLLECT_DECISION_ACCURACY = True
    COLLECT_TOKEN_USAGE = True
    
    # Output configuration
    CONSOLE_OUTPUT = True
    DETAILED_LOGS = True
    SAVE_CONVERSATION_TRANSCRIPTS = True
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        issues = []
        
        if not cls.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY not set")
        
        if not cls.SIMULATION_ROOT.exists():
            issues.append(f"Simulation root directory not found: {cls.SIMULATION_ROOT}")
        
        # Create results directory if it doesn't exist
        results_dir = cls.SIMULATION_ROOT / "results"
        results_dir.mkdir(exist_ok=True)
        
        return issues
    
    @classmethod
    def print_config_summary(cls):
        """Print configuration summary"""
        print("\n>> Simulation Test Configuration:")
        print(f"   Project Root: {cls.PROJECT_ROOT}")
        print(f"   Simulation Root: {cls.SIMULATION_ROOT}")
        print(f"   Test Database: {cls.TEST_DATABASE_URL}")
        print(f"   OpenAI Model: {cls.OPENAI_MODEL}")
        print(f"   API Key: {'SET' if cls.OPENAI_API_KEY else 'MISSING'}")
        print(f"   Max Conversation Length: {cls.MAX_CONVERSATION_LENGTH}")
        print(f"   Log File: {cls.LOG_FILE}")
        print()

# Global configuration instance
config = TestConfig()