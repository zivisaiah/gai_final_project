"""
DateTime Parser Utility
Natural language date/time parsing for scheduling conversations
"""

import re
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Union
from dateutil.parser import parse as dateutil_parse
from dateutil.relativedelta import relativedelta
import calendar


class DateTimeParser:
    """
    Parses natural language date and time expressions for scheduling.
    
    Supports expressions like:
    - "tomorrow", "today", "next week"
    - "Monday", "next Friday", "this Thursday"
    - "in 2 days", "in 3 weeks"
    - "morning", "afternoon", "evening"
    - "9am", "2:30pm", "14:00"
    """
    
    def __init__(self, reference_datetime: datetime = None):
        """Initialize with reference datetime (defaults to now)."""
        self.reference_dt = reference_datetime or datetime.now()
        
        # Day name mappings
        self.day_names = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
            'fri': 4, 'sat': 5, 'sun': 6
        }
        
        # Time period mappings
        self.time_periods = {
            'morning': time(9, 0),    # 9:00 AM
            'afternoon': time(14, 0), # 2:00 PM
            'evening': time(18, 0),   # 6:00 PM
            'night': time(20, 0)      # 8:00 PM
        }
        
        # Relative day mappings
        self.relative_days = {
            'today': 0,
            'tomorrow': 1,
            'yesterday': -1
        }
    
    def parse_datetime_expression(self, expression: str) -> List[Dict]:
        """
        Parse a natural language datetime expression and return possible interpretations.
        
        Args:
            expression: Natural language expression like "next Friday afternoon"
            
        Returns:
            List of dictionaries with 'datetime', 'confidence', and 'interpretation' keys
        """
        expression = expression.lower().strip()
        results = []
        
        # Try different parsing strategies
        results.extend(self._parse_relative_expressions(expression))
        results.extend(self._parse_day_expressions(expression))
        results.extend(self._parse_time_expressions(expression))
        results.extend(self._parse_combined_expressions(expression))
        results.extend(self._parse_absolute_dates(expression))
        
        # Sort by confidence and remove duplicates
        results = self._deduplicate_results(results)
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return results
    
    def _parse_relative_expressions(self, expression: str) -> List[Dict]:
        """Parse relative expressions like 'tomorrow', 'in 2 days', 'next week'."""
        results = []
        
        # Simple relative days
        for rel_day, offset in self.relative_days.items():
            if rel_day in expression:
                target_date = self.reference_dt + timedelta(days=offset)
                results.append({
                    'datetime': target_date.replace(hour=9, minute=0, second=0, microsecond=0),
                    'confidence': 0.9,
                    'interpretation': f'{rel_day.title()} at 9:00 AM'
                })
        
        # "in X days/weeks/months" patterns
        in_pattern = r'in (\d+) (day|days|week|weeks|month|months)'
        match = re.search(in_pattern, expression)
        if match:
            quantity = int(match.group(1))
            unit = match.group(2)
            
            if 'day' in unit:
                target_date = self.reference_dt + timedelta(days=quantity)
            elif 'week' in unit:
                target_date = self.reference_dt + timedelta(weeks=quantity)
            elif 'month' in unit:
                target_date = self.reference_dt + relativedelta(months=quantity)
            
            results.append({
                'datetime': target_date.replace(hour=9, minute=0, second=0, microsecond=0),
                'confidence': 0.85,
                'interpretation': f'In {quantity} {unit} at 9:00 AM'
            })
        
        # "next week" patterns
        if 'next week' in expression:
            next_week = self.reference_dt + timedelta(weeks=1)
            # Default to Monday of next week
            days_ahead = 0 - next_week.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target_date = next_week + timedelta(days=days_ahead)
            
            results.append({
                'datetime': target_date.replace(hour=9, minute=0, second=0, microsecond=0),
                'confidence': 0.8,
                'interpretation': 'Next week Monday at 9:00 AM'
            })
        
        return results
    
    def _parse_day_expressions(self, expression: str) -> List[Dict]:
        """Parse day name expressions like 'Monday', 'next Friday'."""
        results = []
        
        for day_name, day_num in self.day_names.items():
            if day_name in expression:
                # Determine if it's "next" day or "this" day
                is_next = 'next' in expression
                
                current_weekday = self.reference_dt.weekday()
                days_ahead = day_num - current_weekday
                
                if is_next or days_ahead <= 0:
                    days_ahead += 7
                
                target_date = self.reference_dt + timedelta(days=days_ahead)
                
                # Check for time period in the same expression
                time_obj = self._extract_time_period(expression)
                if time_obj:
                    target_date = target_date.replace(
                        hour=time_obj.hour, 
                        minute=time_obj.minute, 
                        second=0, 
                        microsecond=0
                    )
                    time_desc = time_obj.strftime('%I:%M %p')
                else:
                    target_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                    time_desc = '9:00 AM'
                
                prefix = 'Next' if is_next or days_ahead > 7 else 'This'
                results.append({
                    'datetime': target_date,
                    'confidence': 0.9,
                    'interpretation': f'{prefix} {day_name.title()} at {time_desc}'
                })
        
        return results
    
    def _parse_time_expressions(self, expression: str) -> List[Dict]:
        """Parse time expressions like '2pm', '14:30', 'morning'."""
        results = []
        
        # Time period expressions (morning, afternoon, etc.)
        for period, time_obj in self.time_periods.items():
            if period in expression:
                # Default to tomorrow if just time period mentioned
                target_date = self.reference_dt + timedelta(days=1)
                target_date = target_date.replace(
                    hour=time_obj.hour, 
                    minute=time_obj.minute, 
                    second=0, 
                    microsecond=0
                )
                
                results.append({
                    'datetime': target_date,
                    'confidence': 0.7,
                    'interpretation': f'Tomorrow {period} at {time_obj.strftime("%I:%M %p")}'
                })
        
        # Specific time expressions (9am, 2:30pm, etc.)
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 2:30pm
            r'(\d{1,2})\s*(am|pm)',          # 2pm
            r'(\d{1,2}):(\d{2})',            # 14:30
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, expression)
            if match:
                try:
                    if len(match.groups()) == 3:  # Hour:minute am/pm
                        hour, minute, period = match.groups()
                        hour = int(hour)
                        minute = int(minute)
                        
                        if period.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif period.lower() == 'am' and hour == 12:
                            hour = 0
                            
                    elif len(match.groups()) == 2:
                        if match.groups()[1] in ['am', 'pm']:  # Hour am/pm
                            hour, period = match.groups()
                            hour = int(hour)
                            minute = 0
                            
                            if period.lower() == 'pm' and hour != 12:
                                hour += 12
                            elif period.lower() == 'am' and hour == 12:
                                hour = 0
                        else:  # Hour:minute (24-hour)
                            hour, minute = match.groups()
                            hour = int(hour)
                            minute = int(minute)
                    
                    # Default to tomorrow if just time specified
                    target_date = self.reference_dt + timedelta(days=1)
                    target_date = target_date.replace(
                        hour=hour, 
                        minute=minute, 
                        second=0, 
                        microsecond=0
                    )
                    
                    results.append({
                        'datetime': target_date,
                        'confidence': 0.85,
                        'interpretation': f'Tomorrow at {target_date.strftime("%I:%M %p")}'
                    })
                    
                except ValueError:
                    continue
        
        return results
    
    def _parse_combined_expressions(self, expression: str) -> List[Dict]:
        """Parse combined expressions like 'next Friday morning', 'Monday 2pm'."""
        results = []
        
        # Get day and time components separately
        day_results = self._parse_day_expressions(expression)
        time_obj = self._extract_time_period(expression) or self._extract_specific_time(expression)
        
        if day_results and time_obj:
            for day_result in day_results:
                combined_dt = day_result['datetime'].replace(
                    hour=time_obj.hour,
                    minute=time_obj.minute,
                    second=0,
                    microsecond=0
                )
                
                results.append({
                    'datetime': combined_dt,
                    'confidence': 0.95,
                    'interpretation': f"{day_result['interpretation'].split(' at ')[0]} at {time_obj.strftime('%I:%M %p')}"
                })
        
        return results
    
    def _parse_absolute_dates(self, expression: str) -> List[Dict]:
        """Parse absolute date expressions like '2024-01-15', 'January 15'."""
        results = []
        
        # Date patterns
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',          # 2024-01-15
            r'\d{1,2}/\d{1,2}/\d{4}',          # 01/15/2024
            r'\d{1,2}-\d{1,2}-\d{4}',          # 01-15-2024
            r'[A-Za-z]+ \d{1,2}',              # January 15
            r'\d{1,2} [A-Za-z]+',              # 15 January
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, expression)
            if match:
                try:
                    parsed_date = dateutil_parse(match.group(0))
                    
                    # If year not specified, assume current or next year
                    if parsed_date.year < self.reference_dt.year:
                        parsed_date = parsed_date.replace(year=self.reference_dt.year + 1)
                    
                    # Default to 9 AM if no time specified
                    if parsed_date.time() == time(0, 0):
                        parsed_date = parsed_date.replace(hour=9, minute=0)
                    
                    results.append({
                        'datetime': parsed_date,
                        'confidence': 0.9,
                        'interpretation': f'{parsed_date.strftime("%B %d, %Y at %I:%M %p")}'
                    })
                    
                except (ValueError, TypeError):
                    continue
        
        return results
    
    def _extract_time_period(self, expression: str) -> Optional[time]:
        """Extract time period (morning, afternoon, etc.) from expression."""
        for period, time_obj in self.time_periods.items():
            if period in expression:
                return time_obj
        return None
    
    def _extract_specific_time(self, expression: str) -> Optional[time]:
        """Extract specific time (9am, 2:30pm, etc.) from expression."""
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, expression)
            if match:
                try:
                    if len(match.groups()) == 3:  # Hour:minute am/pm
                        hour, minute, period = match.groups()
                        hour = int(hour)
                        minute = int(minute)
                        
                        if period.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif period.lower() == 'am' and hour == 12:
                            hour = 0
                            
                        return time(hour, minute)
                        
                    elif len(match.groups()) == 2:
                        if match.groups()[1] in ['am', 'pm']:  # Hour am/pm
                            hour, period = match.groups()
                            hour = int(hour)
                            
                            if period.lower() == 'pm' and hour != 12:
                                hour += 12
                            elif period.lower() == 'am' and hour == 12:
                                hour = 0
                                
                            return time(hour, 0)
                        else:  # Hour:minute (24-hour)
                            hour, minute = match.groups()
                            return time(int(hour), int(minute))
                            
                except ValueError:
                    continue
        
        return None
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate datetime results."""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create a key based on datetime rounded to nearest 15 minutes
            dt = result['datetime']
            rounded_dt = dt.replace(
                minute=(dt.minute // 15) * 15,
                second=0,
                microsecond=0
            )
            
            if rounded_dt not in seen:
                seen.add(rounded_dt)
                unique_results.append(result)
        
        return unique_results
    
    def get_business_hours_datetime(self, target_date: datetime) -> datetime:
        """Adjust datetime to fall within business hours (9 AM - 6 PM)."""
        if target_date.hour < 9:
            return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        elif target_date.hour >= 18:
            # Move to next business day
            next_day = target_date + timedelta(days=1)
            return next_day.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            return target_date
    
    def is_business_day(self, target_date: datetime) -> bool:
        """Check if the date falls on a business day (Monday-Friday)."""
        return target_date.weekday() < 5  # Monday=0, Friday=4
    
    def get_next_business_day(self, target_date: datetime) -> datetime:
        """Get the next business day from the given date."""
        while not self.is_business_day(target_date):
            target_date += timedelta(days=1)
        return target_date


def parse_scheduling_intent(user_message: str, reference_datetime: datetime = None) -> Dict:
    """
    High-level function to parse scheduling intent from user messages.
    
    Args:
        user_message: User's message that may contain scheduling intent
        reference_datetime: Reference datetime for relative parsing
        
    Returns:
        Dictionary with scheduling information
    """
    parser = DateTimeParser(reference_datetime)
    
    # Look for scheduling keywords
    scheduling_keywords = [
        'schedule', 'appointment', 'interview', 'meeting',
        'available', 'free', 'when', 'time', 'date'
    ]
    
    has_scheduling_intent = any(keyword in user_message.lower() for keyword in scheduling_keywords)
    
    if not has_scheduling_intent:
        return {
            'has_scheduling_intent': False,
            'parsed_datetimes': [],
            'confidence': 0.0
        }
    
    # Parse datetime expressions
    parsed_results = parser.parse_datetime_expression(user_message)
    
    # Filter to business hours and days
    business_results = []
    for result in parsed_results:
        dt = result['datetime']
        
        # Adjust to business hours
        business_dt = parser.get_business_hours_datetime(dt)
        
        # Ensure it's a business day
        if not parser.is_business_day(business_dt):
            business_dt = parser.get_next_business_day(business_dt)
            business_dt = parser.get_business_hours_datetime(business_dt)
        
        business_results.append({
            'datetime': business_dt,
            'confidence': result['confidence'] * 0.9,  # Slight penalty for adjustment
            'interpretation': result['interpretation'],
            'original_datetime': result['datetime']
        })
    
    return {
        'has_scheduling_intent': True,
        'parsed_datetimes': business_results,
        'confidence': max([r['confidence'] for r in business_results]) if business_results else 0.5,
        'user_message': user_message
    } 