#!/usr/bin/env python3
"""Debug scheduling issue - check available slots"""

import sys
sys.path.append('.')

from app.modules.database.sql_manager import SQLManager
from app.modules.utils.datetime_parser import parse_scheduling_intent
from datetime import date, timedelta, datetime

def debug_scheduling():
    """Debug the scheduling issue with Monday vs Friday slots."""
    
    sql = SQLManager()
    print('🗄️ Checking available slots in database...')
    
    # Get all available slots
    start_date = date.today()
    end_date = start_date + timedelta(days=14)
    all_slots = sql.get_available_slots(start_date, end_date)
    
    print(f'📊 Found {len(all_slots)} total available slots:')
    for slot in all_slots:
        weekday_name = slot.slot_date.strftime('%A')
        print(f'  {slot.slot_date} ({weekday_name}) {slot.start_time} - {slot.recruiter.name} (ID: {slot.id})')
    
    # Check specifically for Monday vs Friday
    monday_slots = [s for s in all_slots if s.slot_date.weekday() == 0]  # Monday = 0
    friday_slots = [s for s in all_slots if s.slot_date.weekday() == 4]  # Friday = 4
    
    print(f'\n📅 Monday slots available: {len(monday_slots)}')
    for slot in monday_slots:
        print(f'  {slot.slot_date} {slot.start_time} - {slot.recruiter.name}')
    
    print(f'\n📅 Friday slots available: {len(friday_slots)}')
    for slot in friday_slots:
        print(f'  {slot.slot_date} {slot.start_time} - {slot.recruiter.name}')
    
    # Test the parsing of "I can do Mondays only"
    print(f'\n🔍 Testing parsing of "I can do Mondays only"...')
    result = parse_scheduling_intent("I can do Mondays only")
    print(f'📊 Parsing result: {result}')
    
    if result.get('parsed_datetimes'):
        print('📅 Parsed datetimes:')
        for dt in result['parsed_datetimes']:
            print(f'  {dt}')

if __name__ == "__main__":
    debug_scheduling() 