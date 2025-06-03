-- GAI Final Project - Database Schema
-- Phase 1: Recruitment Scheduling System
-- SQLite compatible schema

-- Create Recruiters table
CREATE TABLE IF NOT EXISTS recruiters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(50) DEFAULT 'Engineering',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create Available Time Slots table
CREATE TABLE IF NOT EXISTS available_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recruiter_id INTEGER NOT NULL,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recruiter_id) REFERENCES recruiters(id),
    UNIQUE(recruiter_id, slot_date, start_time)
);

-- Create Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL,
    candidate_name VARCHAR(100),
    candidate_email VARCHAR(255),
    candidate_phone VARCHAR(20),
    interview_type VARCHAR(50) DEFAULT 'Technical Interview',
    status VARCHAR(20) DEFAULT 'scheduled',
    notes TEXT,
    conversation_id VARCHAR(100),
    scheduled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slot_id) REFERENCES available_slots(id),
    CHECK (status IN ('scheduled', 'confirmed', 'cancelled', 'completed', 'no_show'))
);

-- Insert sample recruiters
INSERT OR IGNORE INTO recruiters (id, name, email, phone, department) VALUES 
(1, 'Sarah Johnson', 'sarah.johnson@techcorp.com', '+1-555-0101', 'Engineering'),
(2, 'Mike Chen', 'mike.chen@techcorp.com', '+1-555-0102', 'Engineering'),
(3, 'Elena Rodriguez', 'elena.rodriguez@techcorp.com', '+1-555-0103', 'Engineering');

-- Insert sample available time slots for the next 2 weeks
-- Recruiter 1 (Sarah Johnson) - Available Mon-Fri 9AM-5PM
INSERT OR IGNORE INTO available_slots (recruiter_id, slot_date, start_time, end_time) VALUES
-- This week
(1, DATE('now', '+1 day'), '09:00', '10:00'),
(1, DATE('now', '+1 day'), '11:00', '12:00'),
(1, DATE('now', '+1 day'), '14:00', '15:00'),
(1, DATE('now', '+2 days'), '09:00', '10:00'),
(1, DATE('now', '+2 days'), '10:30', '11:30'),
(1, DATE('now', '+2 days'), '15:00', '16:00'),
(1, DATE('now', '+3 days'), '09:00', '10:00'),
(1, DATE('now', '+3 days'), '13:00', '14:00'),
(1, DATE('now', '+3 days'), '16:00', '17:00'),
-- Next week
(1, DATE('now', '+8 days'), '09:00', '10:00'),
(1, DATE('now', '+8 days'), '11:00', '12:00'),
(1, DATE('now', '+9 days'), '14:00', '15:00'),
(1, DATE('now', '+10 days'), '10:00', '11:00'),
(1, DATE('now', '+10 days'), '15:00', '16:00');

-- Recruiter 2 (Mike Chen) - Available Tue-Thu 10AM-4PM
INSERT OR IGNORE INTO available_slots (recruiter_id, slot_date, start_time, end_time) VALUES
-- This week
(2, DATE('now', '+1 day'), '10:00', '11:00'),
(2, DATE('now', '+1 day'), '13:00', '14:00'),
(2, DATE('now', '+2 days'), '10:00', '11:00'),
(2, DATE('now', '+2 days'), '15:00', '16:00'),
(2, DATE('now', '+3 days'), '11:00', '12:00'),
(2, DATE('now', '+3 days'), '14:00', '15:00'),
-- Next week
(2, DATE('now', '+8 days'), '10:00', '11:00'),
(2, DATE('now', '+9 days'), '13:00', '14:00'),
(2, DATE('now', '+10 days'), '11:00', '12:00'),
(2, DATE('now', '+10 days'), '15:00', '16:00');

-- Recruiter 3 (Elena Rodriguez) - Available Mon, Wed, Fri 8AM-6PM
INSERT OR IGNORE INTO available_slots (recruiter_id, slot_date, start_time, end_time) VALUES
-- This week
(3, DATE('now', '+1 day'), '08:00', '09:00'),
(3, DATE('now', '+1 day'), '12:00', '13:00'),
(3, DATE('now', '+3 days'), '08:00', '09:00'),
(3, DATE('now', '+3 days'), '17:00', '18:00'),
(3, DATE('now', '+5 days'), '09:00', '10:00'),
(3, DATE('now', '+5 days'), '14:00', '15:00'),
-- Next week
(3, DATE('now', '+8 days'), '08:00', '09:00'),
(3, DATE('now', '+8 days'), '16:00', '17:00'),
(3, DATE('now', '+10 days'), '10:00', '11:00'),
(3, DATE('now', '+12 days'), '13:00', '14:00'),
(3, DATE('now', '+12 days'), '15:00', '16:00');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_available_slots_date ON available_slots(slot_date);
CREATE INDEX IF NOT EXISTS idx_available_slots_recruiter ON available_slots(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_available_slots_available ON available_slots(is_available);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_slot ON appointments(slot_id); 