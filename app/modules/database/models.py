"""
SQLAlchemy Database Models
Phase 1: Recruitment Scheduling System
"""

from datetime import datetime, date, time
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Time, Boolean, 
    Text, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional, List

Base = declarative_base()


class Recruiter(Base):
    """Recruiter model for storing recruiter information."""
    
    __tablename__ = 'recruiters'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    department = Column(String(50), default='Engineering')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    available_slots = relationship("AvailableSlot", back_populates="recruiter")
    
    def __repr__(self):
        return f"<Recruiter(id={self.id}, name='{self.name}', email='{self.email}')>"


class AvailableSlot(Base):
    """Available time slot model for recruiter availability."""
    
    __tablename__ = 'available_slots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recruiter_id = Column(Integer, ForeignKey('recruiters.id'), nullable=False)
    slot_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, default=True)
    timezone = Column(String(50), default='UTC')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('recruiter_id', 'slot_date', 'start_time', 
                        name='unique_recruiter_slot'),
    )
    
    # Relationships
    recruiter = relationship("Recruiter", back_populates="available_slots")
    appointments = relationship("Appointment", back_populates="slot")
    
    @property
    def is_booked(self):
        """Check if this slot has any scheduled appointments."""
        return any(apt.status in ['scheduled', 'confirmed'] for apt in self.appointments)
    
    def __repr__(self):
        return f"<AvailableSlot(id={self.id}, date={self.slot_date}, time={self.start_time}-{self.end_time})>"


class Appointment(Base):
    """Appointment model for scheduled interviews."""
    
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_id = Column(Integer, ForeignKey('available_slots.id'), nullable=False)
    candidate_name = Column(String(100))
    candidate_email = Column(String(255))
    candidate_phone = Column(String(20))
    interview_type = Column(String(50), default='Technical Interview')
    status = Column(String(20), default='scheduled')
    notes = Column(Text)
    conversation_id = Column(String(100))
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            status.in_(['scheduled', 'confirmed', 'cancelled', 'completed', 'no_show']),
            name='valid_appointment_status'
        ),
    )
    
    # Relationships
    slot = relationship("AvailableSlot", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, candidate='{self.candidate_name}', status='{self.status}')>"


# Pydantic models for API serialization and validation
class RecruiterBase(BaseModel):
    """Base Pydantic model for Recruiter."""
    name: str
    email: str
    phone: Optional[str] = None
    department: str = 'Engineering'
    is_active: bool = True


class RecruiterCreate(RecruiterBase):
    """Pydantic model for creating a recruiter."""
    pass


class RecruiterResponse(RecruiterBase):
    """Pydantic model for recruiter API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AvailableSlotBase(BaseModel):
    """Base Pydantic model for AvailableSlot."""
    recruiter_id: int
    slot_date: date
    start_time: time
    end_time: time
    is_available: bool = True
    timezone: str = 'UTC'


class AvailableSlotCreate(AvailableSlotBase):
    """Pydantic model for creating an available slot."""
    pass


class AvailableSlotResponse(AvailableSlotBase):
    """Pydantic model for available slot API responses."""
    id: int
    is_booked: bool
    recruiter: RecruiterResponse
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    """Base Pydantic model for Appointment."""
    slot_id: int
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    interview_type: str = 'Technical Interview'
    status: str = 'scheduled'
    notes: Optional[str] = None
    conversation_id: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Pydantic model for creating an appointment."""
    pass


class AppointmentResponse(AppointmentBase):
    """Pydantic model for appointment API responses."""
    id: int
    slot: AvailableSlotResponse
    scheduled_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentUpdate(BaseModel):
    """Pydantic model for updating an appointment."""
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    interview_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None 