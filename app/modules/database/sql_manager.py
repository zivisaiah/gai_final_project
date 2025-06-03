"""
SQL Manager for Database Operations
Phase 1: Recruitment Scheduling System
"""

import os
import sqlite3
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.modules.database.models import (
    Base, Recruiter, AvailableSlot, Appointment,
    RecruiterCreate, AvailableSlotCreate, AppointmentCreate,
    RecruiterResponse, AvailableSlotResponse, AppointmentResponse
)


class SQLManager:
    """SQL Database Manager for recruitment scheduling operations."""
    
    def __init__(self, database_url: str = None):
        """Initialize the SQL Manager with database connection."""
        if database_url is None:
            # Default to SQLite database in data directory
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            database_url = f"sqlite:///{data_dir}/recruitment.db"
        
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        self._create_tables()
        
        # Initialize with sample data if database is empty
        self._initialize_sample_data()
    
    def _create_tables(self):
        """Create database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise
    
    def _initialize_sample_data(self):
        """Initialize database with sample data if empty."""
        try:
            with self.get_session() as session:
                # Check if we already have data
                if session.query(Recruiter).count() > 0:
                    return
                
                # Execute SQL schema to populate sample data
                sql_file = Path(__file__).parent.parent.parent.parent / "data" / "db_Tech.sql"
                if sql_file.exists():
                    with open(sql_file, 'r') as f:
                        sql_content = f.read()
                    
                    # Split SQL commands and execute them
                    for command in sql_content.split(';'):
                        command = command.strip()
                        if command and not command.startswith('--'):
                            try:
                                session.execute(command)
                            except Exception as e:
                                # Skip errors for INSERT OR IGNORE commands
                                if "UNIQUE constraint failed" not in str(e):
                                    print(f"Warning: SQL command failed: {e}")
                    
                    session.commit()
                    print("✅ Sample data initialized")
                
        except Exception as e:
            print(f"❌ Error initializing sample data: {e}")
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    # Recruiter CRUD Operations
    def create_recruiter(self, recruiter_data: RecruiterCreate) -> RecruiterResponse:
        """Create a new recruiter."""
        with self.get_session() as session:
            try:
                recruiter = Recruiter(**recruiter_data.model_dump())
                session.add(recruiter)
                session.commit()
                session.refresh(recruiter)
                return RecruiterResponse.model_validate(recruiter)
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"Error creating recruiter: {e}")
    
    def get_recruiters(self, active_only: bool = True) -> List[RecruiterResponse]:
        """Get all recruiters."""
        with self.get_session() as session:
            query = session.query(Recruiter)
            if active_only:
                query = query.filter(Recruiter.is_active == True)
            recruiters = query.all()
            return [RecruiterResponse.model_validate(r) for r in recruiters]
    
    def get_recruiter_by_id(self, recruiter_id: int) -> Optional[RecruiterResponse]:
        """Get a recruiter by ID."""
        with self.get_session() as session:
            recruiter = session.query(Recruiter).filter(Recruiter.id == recruiter_id).first()
            return RecruiterResponse.model_validate(recruiter) if recruiter else None
    
    # Available Slots CRUD Operations
    def get_available_slots(
        self, 
        start_date: date = None, 
        end_date: date = None,
        recruiter_id: int = None,
        available_only: bool = True
    ) -> List[AvailableSlotResponse]:
        """Get available time slots with optional filters."""
        with self.get_session() as session:
            query = session.query(AvailableSlot).join(Recruiter)
            
            # Apply filters
            if start_date:
                query = query.filter(AvailableSlot.slot_date >= start_date)
            if end_date:
                query = query.filter(AvailableSlot.slot_date <= end_date)
            if recruiter_id:
                query = query.filter(AvailableSlot.recruiter_id == recruiter_id)
            if available_only:
                query = query.filter(AvailableSlot.is_available == True)
            
            # Order by date and time
            query = query.order_by(AvailableSlot.slot_date, AvailableSlot.start_time)
            
            slots = query.all()
            
            # Filter out booked slots if available_only is True
            if available_only:
                slots = [slot for slot in slots if not slot.is_booked]
            
            return [AvailableSlotResponse.model_validate(slot) for slot in slots]
    
    def get_slot_by_id(self, slot_id: int) -> Optional[AvailableSlotResponse]:
        """Get an available slot by ID."""
        with self.get_session() as session:
            slot = session.query(AvailableSlot).filter(AvailableSlot.id == slot_id).first()
            return AvailableSlotResponse.model_validate(slot) if slot else None
    
    def create_available_slot(self, slot_data: AvailableSlotCreate) -> AvailableSlotResponse:
        """Create a new available slot."""
        with self.get_session() as session:
            try:
                slot = AvailableSlot(**slot_data.model_dump())
                session.add(slot)
                session.commit()
                session.refresh(slot)
                return AvailableSlotResponse.model_validate(slot)
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"Error creating available slot: {e}")
    
    # Appointment CRUD Operations
    def create_appointment(self, appointment_data: AppointmentCreate) -> AppointmentResponse:
        """Create a new appointment."""
        with self.get_session() as session:
            try:
                # Check if slot is available
                slot = session.query(AvailableSlot).filter(
                    AvailableSlot.id == appointment_data.slot_id
                ).first()
                
                if not slot:
                    raise Exception(f"Slot {appointment_data.slot_id} not found")
                
                if not slot.is_available:
                    raise Exception(f"Slot {appointment_data.slot_id} is not available")
                
                if slot.is_booked:
                    raise Exception(f"Slot {appointment_data.slot_id} is already booked")
                
                # Create appointment
                appointment = Appointment(**appointment_data.model_dump())
                session.add(appointment)
                session.commit()
                session.refresh(appointment)
                
                return AppointmentResponse.model_validate(appointment)
                
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"Error creating appointment: {e}")
    
    def get_appointments(
        self, 
        status: str = None,
        recruiter_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> List[AppointmentResponse]:
        """Get appointments with optional filters."""
        with self.get_session() as session:
            query = session.query(Appointment).join(AvailableSlot).join(Recruiter)
            
            # Apply filters
            if status:
                query = query.filter(Appointment.status == status)
            if recruiter_id:
                query = query.filter(AvailableSlot.recruiter_id == recruiter_id)
            if start_date:
                query = query.filter(AvailableSlot.slot_date >= start_date)
            if end_date:
                query = query.filter(AvailableSlot.slot_date <= end_date)
            
            # Order by date and time
            query = query.order_by(AvailableSlot.slot_date, AvailableSlot.start_time)
            
            appointments = query.all()
            return [AppointmentResponse.model_validate(apt) for apt in appointments]
    
    def get_appointment_by_id(self, appointment_id: int) -> Optional[AppointmentResponse]:
        """Get an appointment by ID."""
        with self.get_session() as session:
            appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
            return AppointmentResponse.model_validate(appointment) if appointment else None
    
    def update_appointment_status(self, appointment_id: int, status: str) -> Optional[AppointmentResponse]:
        """Update appointment status."""
        with self.get_session() as session:
            try:
                appointment = session.query(Appointment).filter(Appointment.id == appointment_id).first()
                if not appointment:
                    return None
                
                appointment.status = status
                appointment.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(appointment)
                
                return AppointmentResponse.model_validate(appointment)
                
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"Error updating appointment: {e}")
    
    # Specialized query methods for scheduling
    def find_available_slots_by_date_preference(
        self, 
        preferred_date: date = None, 
        days_range: int = 7,
        limit: int = 5
    ) -> List[AvailableSlotResponse]:
        """Find available slots near a preferred date."""
        if preferred_date is None:
            preferred_date = date.today()
        
        start_date = preferred_date
        end_date = preferred_date + timedelta(days=days_range)
        
        return self.get_available_slots(
            start_date=start_date,
            end_date=end_date,
            available_only=True
        )[:limit]
    
    def get_next_available_slots(self, count: int = 3) -> List[AvailableSlotResponse]:
        """Get the next available slots starting from today."""
        today = date.today()
        return self.get_available_slots(
            start_date=today,
            available_only=True
        )[:count]
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                result = session.execute("SELECT 1").fetchone()
                return result[0] == 1
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.get_session() as session:
            stats = {
                'recruiters_count': session.query(Recruiter).count(),
                'total_slots': session.query(AvailableSlot).count(),
                'available_slots': session.query(AvailableSlot).filter(
                    AvailableSlot.is_available == True
                ).count(),
                'total_appointments': session.query(Appointment).count(),
                'scheduled_appointments': session.query(Appointment).filter(
                    Appointment.status == 'scheduled'
                ).count()
            }
            return stats 