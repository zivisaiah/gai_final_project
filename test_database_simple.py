"""
Simple Database Test Script
Testing SQL Manager and Models functionality without pytest
"""

import sys
import os
from datetime import date, time, datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.modules.database.sql_manager import SQLManager
    from app.modules.database.models import (
        RecruiterCreate, AvailableSlotCreate, AppointmentCreate
    )
    from config.phase1_settings import Settings
    
    print("✅ All imports successful!")
    
    # Test settings
    print("\n🔧 Testing Settings...")
    settings = Settings()
    print(f"✅ App Name: {settings.APP_NAME}")
    print(f"✅ Environment: {settings.ENVIRONMENT}")
    print(f"✅ Database URL: {settings.DATABASE_URL}")
    
    # Test database connection
    print("\n🗄️ Testing Database Connection...")
    sql_manager = SQLManager("sqlite:///:memory:")
    print(f"✅ Database connection: {sql_manager.test_connection()}")
    
    # Test database stats
    stats = sql_manager.get_database_stats()
    print(f"✅ Database stats: {stats}")
    
    # Test creating a recruiter
    print("\n👥 Testing Recruiter Creation...")
    recruiter_data = RecruiterCreate(
        name="Test Recruiter",
        email="test@example.com",
        phone="+1-555-0100"
    )
    recruiter = sql_manager.create_recruiter(recruiter_data)
    print(f"✅ Created recruiter: {recruiter.name} (ID: {recruiter.id})")
    
    # Test getting recruiters
    recruiters = sql_manager.get_recruiters()
    print(f"✅ Found {len(recruiters)} recruiters")
    
    # Test creating an available slot
    print("\n📅 Testing Available Slot Creation...")
    tomorrow = date.today() + timedelta(days=1)
    slot_data = AvailableSlotCreate(
        recruiter_id=recruiter.id,
        slot_date=tomorrow,
        start_time=time(9, 0),
        end_time=time(10, 0)
    )
    slot = sql_manager.create_available_slot(slot_data)
    print(f"✅ Created slot: {slot.slot_date} {slot.start_time}-{slot.end_time}")
    
    # Test getting available slots
    slots = sql_manager.get_available_slots()
    print(f"✅ Found {len(slots)} available slots")
    
    # Test creating an appointment
    print("\n📝 Testing Appointment Creation...")
    appointment_data = AppointmentCreate(
        slot_id=slot.id,
        candidate_name="John Doe",
        candidate_email="john.doe@example.com",
        interview_type="Technical Interview"
    )
    appointment = sql_manager.create_appointment(appointment_data)
    print(f"✅ Created appointment: {appointment.candidate_name} for slot {appointment.slot_id}")
    
    # Test getting appointments
    appointments = sql_manager.get_appointments()
    print(f"✅ Found {len(appointments)} appointments")
    
    # Test next available slots
    print("\n🔍 Testing Next Available Slots...")
    next_slots = sql_manager.get_next_available_slots(count=3)
    print(f"✅ Found {len(next_slots)} next available slots")
    
    print("\n🎉 All database tests passed!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 