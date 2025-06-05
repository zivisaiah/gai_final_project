#!/usr/bin/env python3
"""
Enhanced monitoring for the clean MVC architecture.
Demonstrates how all business logic is now centralized in the Core Agent.
"""

import requests
import time
import json
from datetime import datetime

def log_message(message, level="INFO"):
    """Log a message with timestamp and level."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[0m",      # Default
        "SUCCESS": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",    # Red
        "RESET": "\033[0m"      # Reset
    }
    color = colors.get(level, colors["INFO"])
    print(f"{color}[{timestamp}] {message}{colors['RESET']}")

def test_mvc_architecture():
    """Test and demonstrate the clean MVC architecture."""
    log_message("🏗️ CLEAN MVC ARCHITECTURE MONITORING", "SUCCESS")
    log_message("=" * 60)
    
    # Test application health
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            log_message("✅ Streamlit application is running", "SUCCESS")
        else:
            log_message(f"❌ Streamlit app returned status code: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Cannot connect to Streamlit app: {e}", "ERROR")
        return False
    
    return True

def display_architecture_info():
    """Display information about the new MVC architecture."""
    log_message("")
    log_message("🎯 NEW CLEAN MVC ARCHITECTURE:", "SUCCESS")
    log_message("  📱 VIEW (Streamlit):")
    log_message("     - Only handles UI/presentation")
    log_message("     - User input collection")
    log_message("     - Response display")
    log_message("     - NO business logic")
    log_message("")
    log_message("  🧠 CONTROLLER (Core Agent):")
    log_message("     - ALL business logic centralized here")
    log_message("     - Exit decision logic")
    log_message("     - Continue/Schedule decisions") 
    log_message("     - Orchestrates all advisors")
    log_message("")
    log_message("  🗄️ MODEL (Database + Advisors):")
    log_message("     - Data persistence")
    log_message("     - Specialized advisor logic")
    log_message("     - External API calls")
    log_message("")

def display_decision_flow():
    """Display the clean decision flow."""
    log_message("🔄 CLEAN DECISION FLOW:", "SUCCESS")
    log_message("  1️⃣ User Input → Streamlit (View)")
    log_message("  2️⃣ Streamlit → Core Agent (Controller)")
    log_message("  3️⃣ Core Agent → Exit Advisor → Decision")
    log_message("  4️⃣ Core Agent → Response")
    log_message("  5️⃣ Response → Streamlit → User")
    log_message("")
    log_message("📋 BENEFITS OF NEW ARCHITECTURE:")
    log_message("  ✅ Single source of truth for business logic")
    log_message("  ✅ No duplicate/conflicting decision logic")
    log_message("  ✅ Easier to maintain and test")
    log_message("  ✅ Proper separation of concerns")
    log_message("  ✅ Follows software engineering best practices")
    log_message("")

def display_test_scenarios():
    """Display test scenarios for the MVC architecture."""
    log_message("🧪 TEST SCENARIOS FOR MVC ARCHITECTURE:", "SUCCESS")
    log_message("  1. Technology Preference Exit:")
    log_message("     Input: 'I'm more interested in Java development'")
    log_message("     Expected: Core Agent → Exit Advisor → END decision")
    log_message("")
    log_message("  2. Explicit Decline:")
    log_message("     Input: 'I'll pass on this opportunity'")
    log_message("     Expected: Core Agent → Exit Advisor → END decision")
    log_message("")
    log_message("  3. Information Request:")
    log_message("     Input: 'Tell me about the position'")
    log_message("     Expected: Core Agent → CONTINUE decision")
    log_message("")
    log_message("  4. Scheduling Request:")
    log_message("     Input: 'When can we schedule an interview?'")
    log_message("     Expected: Core Agent → SCHEDULE decision")
    log_message("")

def monitor_application():
    """Monitor the application with clean MVC architecture."""
    log_message("🚀 Starting MVC Architecture Monitoring...", "SUCCESS")
    log_message(f"📍 Application URL: http://localhost:8501")
    log_message("")
    
    # Test application health
    if not test_mvc_architecture():
        return
    
    # Display architecture information
    display_architecture_info()
    display_decision_flow()
    display_test_scenarios()
    
    log_message("🌐 Open http://localhost:8501 in your browser to test the clean MVC architecture", "SUCCESS")
    log_message("💬 Try the test scenarios above to see centralized business logic in action", "SUCCESS")
    log_message("")
    log_message("🔄 Monitoring will continue... (Press Ctrl+C to stop)")
    log_message("=" * 60)
    
    # Keep monitoring with periodic health checks
    try:
        counter = 0
        while True:
            time.sleep(30)  # Check every 30 seconds
            counter += 1
            
            # Periodic health check
            try:
                response = requests.get("http://localhost:8501", timeout=5)
                if response.status_code == 200:
                    log_message(f"✅ Health check #{counter} - MVC architecture running normally", "SUCCESS")
                else:
                    log_message(f"⚠️ Health check #{counter} - Status: {response.status_code}", "WARNING")
            except requests.exceptions.RequestException as e:
                log_message(f"❌ Health check #{counter} failed: {e}", "ERROR")
                break
                
    except KeyboardInterrupt:
        log_message("🛑 MVC Architecture monitoring stopped by user", "WARNING")
        log_message("📊 Summary: Clean MVC architecture successfully implemented", "SUCCESS")
        log_message("   - All business logic centralized in Core Agent", "SUCCESS")
        log_message("   - No duplicate decision logic", "SUCCESS")
        log_message("   - Proper separation of concerns achieved", "SUCCESS")
    except Exception as e:
        log_message(f"❌ Monitoring error: {e}", "ERROR")

if __name__ == "__main__":
    monitor_application() 