#!/usr/bin/env python3
"""Fix Monday slots and test scheduling parsing."""

import sys
sys.path.append('.')

from app.modules.database.sql_manager import SQLManager
from app.modules.database.models import AvailableSlotCreate
from datetime import date, time, timedelta

def add_monday_slots():
    """Add Monday slots to the database."""
    print("🔧 Adding Monday slots to database...")
    
    sql = SQLManager()
    
    # Find next Monday
    today = date.today()
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:  # Today is Monday or later in the week
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    
    # Add another Monday a week later
    monday_after = next_monday + timedelta(days=7)
    
    print(f"📅 Adding slots for {next_monday} and {monday_after}")
    
    # Monday slots for next Monday
    monday_slots = [
        {'date': next_monday, 'time': time(9, 0), 'recruiter_id': 1},  # 9:00 AM
        {'date': next_monday, 'time': time(10, 0), 'recruiter_id': 2}, # 10:00 AM  
        {'date': next_monday, 'time': time(11, 0), 'recruiter_id': 3}, # 11:00 AM
        {'date': next_monday, 'time': time(14, 0), 'recruiter_id': 1}, # 2:00 PM
        {'date': next_monday, 'time': time(15, 0), 'recruiter_id': 2}, # 3:00 PM
        
        # Monday after
        {'date': monday_after, 'time': time(9, 0), 'recruiter_id': 1},  # 9:00 AM
        {'date': monday_after, 'time': time(10, 0), 'recruiter_id': 2}, # 10:00 AM  
        {'date': monday_after, 'time': time(11, 0), 'recruiter_id': 3}, # 11:00 AM
        {'date': monday_after, 'time': time(14, 0), 'recruiter_id': 1}, # 2:00 PM
        {'date': monday_after, 'time': time(15, 0), 'recruiter_id': 2}, # 3:00 PM
    ]
    
    added_count = 0
    for slot_data in monday_slots:
        try:
            slot_create = AvailableSlotCreate(
                recruiter_id=slot_data['recruiter_id'],
                slot_date=slot_data['date'],
                start_time=slot_data['time'],
                end_time=time(slot_data['time'].hour + 1, slot_data['time'].minute),  # 1 hour duration
                is_available=True,
                timezone='UTC'
            )
            slot_response = sql.create_available_slot(slot_create)
            if slot_response and slot_response.id:
                added_count += 1
                print(f"  ✅ Added slot: {slot_data['date']} {slot_data['time']} (ID: {slot_response.id})")
            else:
                print(f"  ⚠️ Failed to add slot: {slot_data['date']} {slot_data['time']}")
        except Exception as e:
            print(f"  ❌ Error adding slot: {e}")
    
    print(f"\n🎯 Successfully added {added_count} Monday slots!")
    
    # Verify Monday slots now exist
    print("\n🔍 Verifying Monday slots...")
    start_date = date.today()
    end_date = start_date + timedelta(days=14)
    all_slots = sql.get_available_slots(start_date, end_date)
    
    monday_slots = [s for s in all_slots if s.slot_date.weekday() == 0]
    print(f'📅 Monday slots now available: {len(monday_slots)}')
    for slot in monday_slots:
        print(f'  {slot.slot_date} {slot.start_time} - {slot.recruiter.name}')

if __name__ == "__main__":
    add_monday_slots() 