"""
Database Tests for Phase 1
Testing SQL Manager and Models functionality
"""

import pytest
import sys
import os
from datetime import date, time, datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.database.sql_manager import SQLManager
from app.modules.database.models import (
    RecruiterCreate, AvailableSlotCreate, AppointmentCreate
)
from config.phase1_settings import Settings


class TestSQLManager:
    """Test cases for SQL Manager."""
    
    @pytest.fixture
    def sql_manager(self):
        """Create a test SQL manager with in-memory database."""
        # Use in-memory SQLite for testing
        return SQLManager("sqlite:///:memory:")
    
    def test_database_connection(self, sql_manager):
        """Test database connection."""
        assert sql_manager.test_connection() == True
    
    def test_database_stats(self, sql_manager):
        """Test database statistics."""
        stats = sql_manager.get_database_stats()
        assert isinstance(stats, dict)
        assert 'recruiters_count' in stats
        assert 'total_slots' in stats
        assert 'available_slots' in stats
        assert 'total_appointments' in stats
    
    def test_create_recruiter(self, sql_manager):
        """Test creating a recruiter."""
        recruiter_data = RecruiterCreate(
            name="Test Recruiter",
            email="test@example.com",
            phone="+1-555-0100",
            department="Engineering"
        )
        
        recruiter = sql_manager.create_recruiter(recruiter_data)
        assert recruiter.name == "Test Recruiter"
        assert recruiter.email == "test@example.com"
        assert recruiter.id is not None
    
    def test_get_recruiters(self, sql_manager):
        """Test getting recruiters."""
        # Create a test recruiter
        recruiter_data = RecruiterCreate(
            name="Test Recruiter 2",
            email="test2@example.com"
        )
        sql_manager.create_recruiter(recruiter_data)
        
        recruiters = sql_manager.get_recruiters()
        assert len(recruiters) >= 1
        assert any(r.name == "Test Recruiter 2" for r in recruiters)
    
    def test_create_available_slot(self, sql_manager):
        """Test creating an available slot."""
        # First create a recruiter
        recruiter_data = RecruiterCreate(
            name="Test Recruiter 3",
            email="test3@example.com"
        )
        recruiter = sql_manager.create_recruiter(recruiter_data)
        
        # Create available slot
        tomorrow = date.today() + timedelta(days=1)
        slot_data = AvailableSlotCreate(
            recruiter_id=recruiter.id,
            slot_date=tomorrow,
            start_time=time(9, 0),
            end_time=time(10, 0)
        )
        
        slot = sql_manager.create_available_slot(slot_data)
        assert slot.recruiter_id == recruiter.id
        assert slot.slot_date == tomorrow
        assert slot.start_time == time(9, 0)
    
    def test_get_available_slots(self, sql_manager):
        """Test getting available slots."""
        # Create recruiter and slot
        recruiter_data = RecruiterCreate(
            name="Test Recruiter 4",
            email="test4@example.com"
        )
        recruiter = sql_manager.create_recruiter(recruiter_data)
        
        tomorrow = date.today() + timedelta(days=1)
        slot_data = AvailableSlotCreate(
            recruiter_id=recruiter.id,
            slot_date=tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0)
        )
        sql_manager.create_available_slot(slot_data)
        
        # Get available slots
        slots = sql_manager.get_available_slots()
        assert len(slots) >= 1
    
    def test_create_appointment(self, sql_manager):
        """Test creating an appointment."""
        # Create recruiter and slot
        recruiter_data = RecruiterCreate(
            name="Test Recruiter 5",
            email="test5@example.com"
        )
        recruiter = sql_manager.create_recruiter(recruiter_data)
        
        tomorrow = date.today() + timedelta(days=1)
        slot_data = AvailableSlotCreate(
            recruiter_id=recruiter.id,
            slot_date=tomorrow,
            start_time=time(11, 0),
            end_time=time(12, 0)
        )
        slot = sql_manager.create_available_slot(slot_data)
        
        # Create appointment
        appointment_data = AppointmentCreate(
            slot_id=slot.id,
            candidate_name="John Doe",
            candidate_email="john.doe@example.com",
            interview_type="Technical Interview"
        )
        
        appointment = sql_manager.create_appointment(appointment_data)
        assert appointment.candidate_name == "John Doe"
        assert appointment.slot_id == slot.id
        assert appointment.status == "scheduled"
    
    def test_get_appointments(self, sql_manager):
        """Test getting appointments."""
        # Create recruiter, slot, and appointment
        recruiter_data = RecruiterCreate(
            name="Test Recruiter 6",
            email="test6@example.com"
        )
        recruiter = sql_manager.create_recruiter(recruiter_data)
        
        tomorrow = date.today() + timedelta(days=1)
        slot_data = AvailableSlotCreate(
            recruiter_id=recruiter.id,
            slot_date=tomorrow,
            start_time=time(16, 0),
            end_time=time(17, 0)
        )
        slot = sql_manager.create_available_slot(slot_data)
        
        appointment_data = AppointmentCreate(
            slot_id=slot.id,
            candidate_name="Jane Smith",
            candidate_email="jane.smith@example.com"
        )
        sql_manager.create_appointment(appointment_data)
        
        # Get appointments
        appointments = sql_manager.get_appointments()
        assert len(appointments) >= 1
        assert any(apt.candidate_name == "Jane Smith" for apt in appointments)
    
    def test_find_available_slots_by_date_preference(self, sql_manager):
        """Test finding slots by date preference."""
        # Create recruiter and slot
        recruiter_data = RecruiterCreate(
            name="Test Recruiter 7",
            email="test7@example.com"
        )
        recruiter = sql_manager.create_recruiter(recruiter_data)
        
        target_date = date.today() + timedelta(days=3)
        slot_data = AvailableSlotCreate(
            recruiter_id=recruiter.id,
            slot_date=target_date,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        sql_manager.create_available_slot(slot_data)
        
        # Find slots near target date
        slots = sql_manager.find_available_slots_by_date_preference(
            preferred_date=target_date,
            days_range=7
        )
        assert len(slots) >= 1
    
    def test_get_next_available_slots(self, sql_manager):
        """Test getting next available slots."""
        # Create recruiter and slot
        recruiter_data = RecruiterCreate(
            name="Test Recruiter 8",
            email="test8@example.com"
        )
        recruiter = sql_manager.create_recruiter(recruiter_data)
        
        tomorrow = date.today() + timedelta(days=1)
        slot_data = AvailableSlotCreate(
            recruiter_id=recruiter.id,
            slot_date=tomorrow,
            start_time=time(13, 0),
            end_time=time(14, 0)
        )
        sql_manager.create_available_slot(slot_data)
        
        # Get next available slots
        slots = sql_manager.get_next_available_slots(count=3)
        assert len(slots) >= 1


def test_settings_configuration():
    """Test settings configuration."""
    settings = Settings()
    assert settings.APP_NAME == "GAI Final Project - Phase 1"
    assert settings.ENVIRONMENT in ["development", "production"]
    assert settings.DATABASE_URL is not None


if __name__ == "__main__":
    # Run a quick manual test
    print("🧪 Running Database Tests...")
    
    # Test basic functionality
    sql_manager = SQLManager("sqlite:///:memory:")
    
    print("✅ Database connection:", sql_manager.test_connection())
    
    stats = sql_manager.get_database_stats()
    print("✅ Database stats:", stats)
    
    # Test creating a recruiter
    recruiter_data = RecruiterCreate(
        name="Manual Test Recruiter",
        email="manual@test.com"
    )
    recruiter = sql_manager.create_recruiter(recruiter_data)
    print(f"✅ Created recruiter: {recruiter.name} (ID: {recruiter.id})")
    
    # Test getting next available slots
    slots = sql_manager.get_next_available_slots(count=3)
    print(f"✅ Found {len(slots)} available slots")
    
    print("\n🎉 All manual tests passed!") 