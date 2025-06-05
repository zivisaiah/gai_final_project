"""
Scheduling Advisor Implementation
Specialized agent for handling interview scheduling decisions and time slot management
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.modules.prompts.scheduling_prompts import SchedulingPrompts
from app.modules.database.sql_manager import SQLManager
from config.phase1_settings import get_settings


class SchedulingDecision(Enum):
    """Possible scheduling decisions."""
    SCHEDULE = "SCHEDULE"
    NOT_SCHEDULE = "NOT_SCHEDULE"
    CONFIRM_SLOT = "CONFIRM_SLOT"  # User is confirming a previously offered slot


class SchedulingAdvisor:
    """
    Scheduling Advisor for interview appointment management.
    
    This agent determines when to schedule interviews, finds suitable time slots,
    and manages the scheduling process with natural language understanding.
    """
    
    def __init__(self, openai_api_key: str = None, model_name: str = None):
        """Initialize the Scheduling Advisor with LangChain and database components."""
        self.settings = get_settings()
        
        # Initialize OpenAI client
        self.llm = ChatOpenAI(
            api_key=openai_api_key or self.settings.OPENAI_API_KEY,
            model=model_name or self.settings.OPENAI_MODEL,
            temperature=self.settings.OPENAI_TEMPERATURE,
            max_tokens=self.settings.OPENAI_MAX_TOKENS
        )
        
        # Initialize database manager
        self.sql_manager = SQLManager()
        
        # Initialize prompts
        self.prompts = SchedulingPrompts()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Create the scheduling decision chain
        self._setup_scheduling_chain()
    
    def _setup_scheduling_chain(self):
        """Set up the LangChain scheduling decision chain."""
        # Create prompt template
        self.scheduling_prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompts.get_scheduling_system_prompt()),
            ("human", "{scheduling_input}")
        ])
        
        # Create the chain
        self.scheduling_chain = self.scheduling_prompt | self.llm
    
    def make_scheduling_decision(
        self,
        candidate_info: Dict,
        conversation_messages: List[Dict],
        latest_message: str,
        reference_datetime: datetime = None
    ) -> Tuple[SchedulingDecision, str, List[Dict], str]:
        """
        Make a unified scheduling decision with integrated intent detection and time parsing.
        
        Args:
            candidate_info: Information about the candidate
            conversation_messages: Full conversation history
            latest_message: Most recent user message
            reference_datetime: Reference time for parsing (defaults to now)
            
        Returns:
            Tuple of (decision, reasoning, suggested_slots, response_message)
        """
        try:
            reference_dt = reference_datetime or datetime.now()
            
            # Get ALL available slots in the next 2 weeks (LLM will do the matching)
            available_slots = self._get_all_available_slots(reference_dt, 14)
            
            # Generate unified decision prompt
            decision_prompt = self.prompts.get_decision_prompt(
                candidate_info=candidate_info,
                latest_message=latest_message,
                message_count=len(conversation_messages),
                available_slots=available_slots,
                current_datetime=reference_dt,
                conversation_history=conversation_messages
            )
            
            # Get unified analysis from LLM
            response = self.scheduling_chain.invoke({"scheduling_input": decision_prompt})
            response_text = response.content
            
            # Parse the unified LLM response
            decision, reasoning, suggested_slots, response_message = self._parse_unified_response(
                response_text, available_slots
            )
            
            # Apply validation rules if needed
            decision = self._validate_unified_decision(decision, candidate_info, latest_message)
            
            self.logger.info(f"Unified scheduling decision: {decision.value}")
            self.logger.info(f"Intent confidence: {getattr(self, '_last_intent_confidence', 'N/A')}")
            self.logger.info(f"Reasoning: {reasoning}")
            
            return decision, reasoning, suggested_slots, response_message
            
        except Exception as e:
            self.logger.error(f"Error in unified scheduling decision: {e}")
            return self._fallback_scheduling_decision(candidate_info, latest_message)
    
    def _get_available_slots(
        self,
        preferred_datetimes: List[Dict],
        reference_datetime: datetime,
        days_ahead: int = 14
    ) -> List[Dict]:
        """
        Get available time slots based on candidate preferences and recruiter availability.
        
        Args:
            preferred_datetimes: Parsed datetime preferences from candidate
            reference_datetime: Reference time for searching
            days_ahead: How many days ahead to search
            
        Returns:
            List of available time slots
        """
        try:
            # Define search window
            start_date = reference_datetime.date()
            end_date = start_date + timedelta(days=days_ahead)
            
            # Get available slots from database
            all_slots_raw = self.sql_manager.get_available_slots(start_date, end_date)
            
            # Convert AvailableSlotResponse objects to dictionaries for compatibility
            all_slots = []
            for slot in all_slots_raw:
                slot_dict = {
                    'id': slot.id,
                    'datetime': datetime.combine(slot.slot_date, slot.start_time).isoformat(),
                    'recruiter': slot.recruiter.name if slot.recruiter else 'Our team',
                    'recruiter_id': slot.recruiter_id,
                    'is_available': slot.is_available,
                    'timezone': slot.timezone
                }
                all_slots.append(slot_dict)
            
            if not preferred_datetimes:
                # No specific preferences, return diversified available slots
                return self._diversify_slot_selection(all_slots)
            
            # Match slots with candidate preferences
            matched_slots = []
            
            for pref in preferred_datetimes:
                pref_dt = pref['datetime']
                
                # Find slots within 2 hours of preferred time
                for slot in all_slots:
                    slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                    
                    # Check if slot is on the same day
                    if slot_dt.date() == pref_dt.date():
                        time_diff = abs((slot_dt - pref_dt).total_seconds() / 3600)  # Hours
                        
                        if time_diff <= 2:  # Within 2 hours
                            slot['preference_match'] = True
                            slot['time_difference'] = time_diff
                            matched_slots.append(slot)
            
            # Sort matched slots by preference match and time difference
            matched_slots.sort(key=lambda x: x.get('time_difference', 999))
            
            # If we have good matches, return them; otherwise return diversified available slots
            if matched_slots:
                return self._diversify_slot_selection(matched_slots, max_slots=3)
            else:
                return self._diversify_slot_selection(all_slots, max_slots=3)
                
        except Exception as e:
            self.logger.error(f"Error getting available slots: {e}")
            return []

    def _diversify_slot_selection(self, available_slots: List[Dict], max_slots: int = 3) -> List[Dict]:
        """
        Select diversified slots across different days and times.
        
        Args:
            available_slots: All available slots to choose from
            max_slots: Maximum number of slots to return
            
        Returns:
            List of diversified slots across different days and times
        """
        if not available_slots:
            return []
        
        if len(available_slots) <= max_slots:
            return available_slots
        
        try:
            selected_slots = []
            used_days = set()
            used_time_blocks = set()  # Track morning/afternoon/evening blocks
            used_global_time_blocks = set()  # Track time blocks globally across all days
            
            # Group slots by day to enable smart day+time selection
            slots_by_day = {}
            for slot in available_slots:
                slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                slot_date = slot_dt.date()
                if slot_date not in slots_by_day:
                    slots_by_day[slot_date] = []
                slots_by_day[slot_date].append(slot)
            
            # Sort days by date to start with earliest available days
            sorted_days = sorted(slots_by_day.keys())
            
            # PHASE 1: Select one slot per day, diversifying time blocks across days
            time_block_priority = ['morning', 'afternoon', 'evening']  # Rotation preference
            time_block_index = 0
            
            for day in sorted_days:
                if len(selected_slots) >= max_slots:
                    break
                
                day_slots = slots_by_day[day]
                # Sort slots within this day by time
                day_slots.sort(key=lambda x: x['datetime'])
                
                # Try to find a slot in the preferred time block for diversity
                preferred_time_block = time_block_priority[time_block_index % len(time_block_priority)]
                selected_slot = None
                
                # First, try to find a slot in the preferred time block
                for slot in day_slots:
                    slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                    slot_hour = slot_dt.hour
                    
                    # Determine time block
                    if 6 <= slot_hour < 12:
                        time_block = 'morning'
                    elif 12 <= slot_hour < 17:
                        time_block = 'afternoon'
                    else:
                        time_block = 'evening'
                    
                    # Prefer the time block we haven't used globally yet
                    if time_block == preferred_time_block and time_block not in used_global_time_blocks:
                        selected_slot = slot
                        break
                
                # If no slot in preferred time block, try any unused global time block
                if not selected_slot:
                    for slot in day_slots:
                        slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                        slot_hour = slot_dt.hour
                        
                        if 6 <= slot_hour < 12:
                            time_block = 'morning'
                        elif 12 <= slot_hour < 17:
                            time_block = 'afternoon'
                        else:
                            time_block = 'evening'
                        
                        if time_block not in used_global_time_blocks:
                            selected_slot = slot
                            break
                
                # If all global time blocks are used, just take the first available slot
                if not selected_slot:
                    selected_slot = day_slots[0]
                
                # Add the selected slot
                if selected_slot:
                    slot_dt = datetime.fromisoformat(selected_slot['datetime'].replace('Z', '+00:00'))
                    slot_hour = slot_dt.hour
                    
                    if 6 <= slot_hour < 12:
                        time_block = 'morning'
                    elif 12 <= slot_hour < 17:
                        time_block = 'afternoon'
                    else:
                        time_block = 'evening'
                    
                    selected_slots.append(selected_slot)
                    used_days.add(day)
                    used_time_blocks.add(f"{day}_{time_block}")
                    used_global_time_blocks.add(time_block)
                    
                    self.logger.debug(f"Selected slot for new day: {day} at {slot_hour}:00 ({time_block}) - global time diversity")
                    
                    # Move to next time block for diversity
                    time_block_index += 1
            
            # PHASE 2: If we still need slots, add different time blocks on existing days
            if len(selected_slots) < max_slots:
                # Create a flat list of all remaining slots
                all_remaining_slots = []
                for day, day_slots in slots_by_day.items():
                    for slot in day_slots:
                        if slot not in selected_slots:
                            all_remaining_slots.append(slot)
                
                # Sort remaining slots by datetime
                all_remaining_slots.sort(key=lambda x: x['datetime'])
                
                for slot in all_remaining_slots:
                    if len(selected_slots) >= max_slots:
                        break
                    
                    slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                    slot_date = slot_dt.date()
                    slot_hour = slot_dt.hour
                    
                    # Determine time block
                    if 6 <= slot_hour < 12:
                        time_block = 'morning'
                    elif 12 <= slot_hour < 17:
                        time_block = 'afternoon'
                    else:
                        time_block = 'evening'
                    
                    day_time_key = f"{slot_date}_{time_block}"
                    
                    # Add if it's a new time block (even on existing days)
                    if day_time_key not in used_time_blocks:
                        selected_slots.append(slot)
                        used_time_blocks.add(day_time_key)
                        self.logger.debug(f"Selected slot for new time block: {slot_date} at {slot_hour}:00 ({time_block})")
            
            # PHASE 3: If we still need more slots, add any remaining ones
            if len(selected_slots) < max_slots:
                # Get all remaining slots
                all_remaining_slots = []
                for day, day_slots in slots_by_day.items():
                    for slot in day_slots:
                        if slot not in selected_slots:
                            all_remaining_slots.append(slot)
                
                all_remaining_slots.sort(key=lambda x: x['datetime'])
                
                for slot in all_remaining_slots:
                    if slot not in selected_slots and len(selected_slots) < max_slots:
                        selected_slots.append(slot)
            
            # Calculate diversity metrics
            unique_days = len(used_days)
            unique_time_blocks = len(used_global_time_blocks)
            
            self.logger.info(f"Diversified slot selection: {len(selected_slots)} slots across {unique_days} days and {unique_time_blocks} time blocks")
            
            # Log the diversity for debugging
            for i, slot in enumerate(selected_slots, 1):
                slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                day_name = slot_dt.strftime('%A')
                time_str = slot_dt.strftime('%I:%M %p')
                
                # Determine time block for logging
                slot_hour = slot_dt.hour
                if 6 <= slot_hour < 12:
                    time_block = 'morning'
                elif 12 <= slot_hour < 17:
                    time_block = 'afternoon'
                else:
                    time_block = 'evening'
                
                self.logger.debug(f"  Slot {i}: {day_name} {slot_dt.date()} at {time_str} ({time_block})")
            
            return selected_slots
            
        except Exception as e:
            self.logger.error(f"Error in slot diversification: {e}")
            # Fallback to simple selection
            return available_slots[:max_slots]
    
    def _parse_scheduling_response(
        self,
        response_text: str,
        available_slots: List[Dict]
    ) -> Tuple[SchedulingDecision, str, List[Dict], str]:
        """Parse the LLM response to extract scheduling decision and details."""
        try:
            # Look for structured response format
            decision_match = re.search(r'DECISION:\s*(SCHEDULE|NOT_SCHEDULE)', response_text, re.IGNORECASE)
            reasoning_match = re.search(r'REASONING:\s*(.+?)(?=SUGGESTED_SLOTS:|RESPONSE:|$)', response_text, re.DOTALL)
            slots_match = re.search(r'SUGGESTED_SLOTS:\s*(.+?)(?=RESPONSE:|$)', response_text, re.DOTALL)
            response_match = re.search(r'RESPONSE:\s*(.+)', response_text, re.DOTALL)
            
            if decision_match and reasoning_match and response_match:
                decision = SchedulingDecision(decision_match.group(1).upper())
                reasoning = reasoning_match.group(1).strip()
                response_message = response_match.group(1).strip()
                
                # Parse suggested slots
                suggested_slots = []
                if decision == SchedulingDecision.SCHEDULE and slots_match:
                    slots_text = slots_match.group(1).strip()
                    if slots_text and slots_text != "[]" and "empty" not in slots_text.lower():
                        # Use diversified available slots if LLM suggested scheduling
                        suggested_slots = self._diversify_slot_selection(available_slots, max_slots=3)
                
                return decision, reasoning, suggested_slots, response_message
            
            # If structured format not found, try to infer from content
            if any(keyword in response_text.lower() for keyword in ['schedule', 'appointment', 'available slots']):
                decision = SchedulingDecision.SCHEDULE
                reasoning = "Response indicates scheduling intent"
                suggested_slots = self._diversify_slot_selection(available_slots, max_slots=3)
            else:
                decision = SchedulingDecision.NOT_SCHEDULE
                reasoning = "Continuing conversation to gather more information"
                suggested_slots = []
            
            response_message = response_text.strip()
            
            return decision, reasoning, suggested_slots, response_message
            
        except Exception as e:
            self.logger.error(f"Error parsing scheduling response: {e}")
            return SchedulingDecision.NOT_SCHEDULE, "Error parsing response", [], response_text
    
    def _validate_scheduling_decision(
        self,
        decision: SchedulingDecision,
        candidate_info: Dict,
        scheduling_intent: Dict
    ) -> SchedulingDecision:
        """Validate and potentially override the scheduling decision based on context."""
        
        # Override to SCHEDULE if conditions are strongly met
        if (decision == SchedulingDecision.NOT_SCHEDULE and
            candidate_info.get("name") and
            candidate_info.get("interest_level") == "high" and
            scheduling_intent.get("has_scheduling_intent") and
            scheduling_intent.get("confidence", 0) > 0.7):
            
            self.logger.info("Overriding NOT_SCHEDULE to SCHEDULE based on strong indicators")
            return SchedulingDecision.SCHEDULE
        
        # Override to NOT_SCHEDULE if essential info is missing
        if (decision == SchedulingDecision.SCHEDULE and
            not candidate_info.get("name") and
            candidate_info.get("interest_level") != "high"):
            
            self.logger.info("Overriding SCHEDULE to NOT_SCHEDULE - missing essential info")
            return SchedulingDecision.NOT_SCHEDULE
        
        return decision
    
    def _fallback_scheduling_decision(
        self,
        candidate_info: Dict,
        latest_message: str
    ) -> Tuple[SchedulingDecision, str, List[Dict], str]:
        """Fallback rule-based scheduling decision when LLM fails."""
        
        message_lower = latest_message.lower()
        
        # Clear scheduling intent
        if any(word in message_lower for word in ['schedule', 'interview', 'appointment', 'when can', 'available']):
            if candidate_info.get("name") and candidate_info.get("interest_level") == "high":
                return (
                    SchedulingDecision.SCHEDULE,
                    "User expressed scheduling intent with sufficient information",
                    [],
                    "Great! Let me check our available interview slots for you."
                )
        
        # Default to not scheduling
        return (
            SchedulingDecision.NOT_SCHEDULE,
            "Need more information before scheduling",
            [],
            "Could you tell me a bit more about your availability and when you'd prefer to have the interview?"
        )
    
    def book_appointment(
        self,
        candidate_info: Dict,
        slot_datetime: datetime,
        recruiter_id: int,
        duration_minutes: int = 45,
        slot_id: int = None
    ) -> Dict:
        """
        Book an interview appointment in the database.
        
        Args:
            candidate_info: Information about the candidate
            slot_datetime: Chosen appointment datetime
            recruiter_id: ID of the recruiter
            duration_minutes: Duration of the interview
            slot_id: ID of the specific slot to book
            
        Returns:
            Dictionary with booking confirmation details
        """
        try:
            # If no slot_id provided, try to find the matching slot
            if not slot_id:
                # Find matching slot by datetime and recruiter
                available_slots = self.sql_manager.get_available_slots(
                    start_date=slot_datetime.date(),
                    end_date=slot_datetime.date(),
                    recruiter_id=recruiter_id,
                    available_only=True
                )
                
                # Find exact time match
                matching_slot = None
                for slot in available_slots:
                    slot_dt = datetime.combine(slot.slot_date, slot.start_time)
                    if slot_dt == slot_datetime:
                        matching_slot = slot
                        break
                
                if not matching_slot:
                    return {
                        'success': False,
                        'error': f'No available slot found for {slot_datetime} with recruiter {recruiter_id}'
                    }
                
                slot_id = matching_slot.id
            
            # Create appointment in database using AppointmentCreate model
            from app.modules.database.models import AppointmentCreate
            
            appointment_data = AppointmentCreate(
                slot_id=slot_id,
                candidate_name=candidate_info.get('name', 'Unknown'),
                candidate_email=candidate_info.get('email', ''),
                candidate_phone=candidate_info.get('phone', ''),
                interview_type='Technical Interview',
                status='scheduled',
                notes=f"Scheduled via chatbot. Experience: {candidate_info.get('experience', 'Not specified')}",
                conversation_id=candidate_info.get('conversation_id', '')
            )
            
            appointment = self.sql_manager.create_appointment(appointment_data)
            
            if appointment:
                self.logger.info(f"Successfully booked appointment {appointment.id}")
                
                # Get recruiter details from the appointment slot
                recruiter_dict = {
                    'id': appointment.slot.recruiter.id,
                    'name': appointment.slot.recruiter.name,
                    'email': appointment.slot.recruiter.email
                }
                
                return {
                    'success': True,
                    'appointment_id': appointment.id,
                    'datetime': slot_datetime,
                    'recruiter': recruiter_dict,
                    'duration': duration_minutes,
                    'confirmation_message': self._generate_confirmation_message(
                        slot_datetime, recruiter_dict, duration_minutes
                    )
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create appointment in database'
                }
                
        except Exception as e:
            self.logger.error(f"Error booking appointment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_confirmation_message(
        self,
        slot_datetime: datetime,
        recruiter: Dict,
        duration_minutes: int
    ) -> str:
        """Generate a confirmation message for the booked appointment."""
        
        formatted_datetime = slot_datetime.strftime("%A, %B %d, %Y at %I:%M %p")
        recruiter_name = recruiter.get('name', 'Our recruiter') if recruiter else 'Our recruiter'
        
        return f"""🎉 **Interview Successfully Scheduled!**

📅 **Date & Time:** {formatted_datetime}
👤 **Interviewer:** {recruiter_name}
⏱️ **Duration:** {duration_minutes} minutes
📧 **Format:** Video call (link will be sent via email)

You'll receive a calendar invitation with the meeting link and all details within the next few minutes.

✅ **All set!** Thank you for your interest in our Python developer position. We look forward to speaking with you soon!

---
*This conversation is now complete. If you need to reschedule or have any questions, please contact our HR team directly.*"""
    
    def get_scheduling_statistics(self) -> Dict:
        """Get statistics about scheduling operations."""
        try:
            # Get database statistics
            stats = self.sql_manager.get_database_stats()
            
            return {
                'total_appointments': stats.get('total_appointments', 0),
                'scheduled_appointments': stats.get('appointments', 0),
                'available_slots': stats.get('available_slots', 0),
                'recruiter_count': stats.get('recruiters', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting scheduling statistics: {e}")
            return {
                'total_appointments': 0,
                'scheduled_appointments': 0,
                'available_slots': 0,
                'recruiter_count': 0
            }
    
    def _get_all_available_slots(
        self,
        reference_datetime: datetime,
        days_ahead: int = 14
    ) -> List[Dict]:
        """
        Get all available time slots for LLM to analyze and match.
        
        Args:
            reference_datetime: Reference time for searching
            days_ahead: How many days ahead to search
            
        Returns:
            List of all available time slots
        """
        try:
            # Define search window
            start_date = reference_datetime.date()
            end_date = start_date + timedelta(days=days_ahead)
            
            # Get available slots from database
            all_slots_raw = self.sql_manager.get_available_slots(start_date, end_date)
            
            # Convert AvailableSlotResponse objects to dictionaries for LLM analysis
            all_slots = []
            for slot in all_slots_raw:
                slot_dict = {
                    'id': slot.id,
                    'datetime': datetime.combine(slot.slot_date, slot.start_time).isoformat(),
                    'recruiter': slot.recruiter.name if slot.recruiter else 'Our team',
                    'recruiter_id': slot.recruiter_id,
                    'is_available': slot.is_available,
                    'timezone': slot.timezone,
                    'duration': 45  # Default interview duration
                }
                all_slots.append(slot_dict)
            
            return all_slots
            
        except Exception as e:
            self.logger.error(f"Error getting available slots: {e}")
            return []

    def _parse_unified_response(
        self,
        response_text: str,
        available_slots: List[Dict]
    ) -> Tuple[SchedulingDecision, str, List[Dict], str]:
        """
        Parse the unified LLM response containing intent analysis, preferences, and decision.
        
        Args:
            response_text: Raw LLM response text
            available_slots: Available slots for validation
            
        Returns:
            Tuple of (decision, reasoning, suggested_slots, response_message)
        """
        try:
            # Clean response text and extract JSON
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Look for JSON object in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            # Parse JSON response
            response_data = json.loads(response_text)
            
            # Extract components
            intent_analysis = response_data.get('intent_analysis', {})
            time_preferences = response_data.get('time_preferences', {})
            decision_str = response_data.get('decision', 'NOT_SCHEDULE')
            reasoning = response_data.get('reasoning', 'No reasoning provided')
            suggested_slots = response_data.get('suggested_slots', [])
            response_message = response_data.get('response_message', 'Let me know how I can help you further.')
            
            # Store intent confidence for logging
            self._last_intent_confidence = intent_analysis.get('confidence', 0.0)
            
            # Convert decision string to enum
            if decision_str == 'SCHEDULE':
                decision = SchedulingDecision.SCHEDULE
            elif decision_str == 'CONFIRM_SLOT':
                decision = SchedulingDecision.CONFIRM_SLOT
            else:
                decision = SchedulingDecision.NOT_SCHEDULE
            
            # Handle slot selection based on decision
            if decision == SchedulingDecision.SCHEDULE:
                # When scheduling, always provide diversified available slots regardless of LLM suggestions
                final_slots = self._diversify_slot_selection(available_slots, max_slots=3)
                self.logger.info(f"Decision: SCHEDULE - providing {len(final_slots)} diversified slots")
            else:
                # For non-scheduling decisions, validate LLM suggestions if any
                final_slots = self._validate_suggested_slots(suggested_slots, available_slots)
                self.logger.info(f"Decision: {decision_str} - validated {len(final_slots)} suggested slots")
            
            self.logger.info(f"Intent analysis: {intent_analysis}")
            self.logger.info(f"Time preferences: {time_preferences}")
            self.logger.info(f"Suggested {len(final_slots)} slots")
            
            return decision, reasoning, final_slots, response_message
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing unified response: {e}")
            self.logger.error(f"Raw response (first 500 chars): {response_text[:500]}")
            
            # Fallback to simple parsing
            return self._fallback_response_parsing(response_text, available_slots)
    
    def _validate_suggested_slots(
        self,
        suggested_slots: List[Dict],
        available_slots: List[Dict]
    ) -> List[Dict]:
        """
        Validate that suggested slots exist in available slots and format them properly.
        
        Args:
            suggested_slots: Slots suggested by LLM
            available_slots: Actually available slots
            
        Returns:
            List of validated and formatted slots
        """
        validated = []
        
        # Create lookup for available slots
        available_lookup = {slot['datetime']: slot for slot in available_slots}
        
        for suggested in suggested_slots:
            suggested_dt = suggested.get('datetime', '')
            
            # Check if suggested slot exists in available slots
            if suggested_dt in available_lookup:
                available_slot = available_lookup[suggested_dt]
                validated_slot = {
                    'id': available_slot['id'],
                    'datetime': suggested_dt,
                    'recruiter': suggested.get('recruiter', available_slot['recruiter']),
                    'recruiter_id': available_slot['recruiter_id'],
                    'duration': available_slot.get('duration', 45),
                    'match_reason': suggested.get('match_reason', 'Selected for you'),
                    'is_available': True
                }
                validated.append(validated_slot)
        
        # Apply diversification to validated slots as well
        return self._diversify_slot_selection(validated, max_slots=3)
    
    def _validate_unified_decision(
        self,
        decision: SchedulingDecision,
        candidate_info: Dict,
        latest_message: str
    ) -> SchedulingDecision:
        """
        Apply final validation rules to the unified decision.
        
        Args:
            decision: LLM's decision
            candidate_info: Candidate information
            latest_message: Latest user message
            
        Returns:
            Validated decision
        """
        # Override to NOT_SCHEDULE if essential info is missing
        if (decision == SchedulingDecision.SCHEDULE and 
            not candidate_info.get("name") and
            candidate_info.get("interest_level") != "high"):
            
            self.logger.info("Overriding SCHEDULE to NOT_SCHEDULE - missing essential candidate info")
            return SchedulingDecision.NOT_SCHEDULE
        
        # Check for clear rejection signals
        rejection_signals = ['not interested', 'found another', 'pass on', 'not a good fit']
        if any(signal in latest_message.lower() for signal in rejection_signals):
            self.logger.info("Overriding to NOT_SCHEDULE - detected rejection signal")
            return SchedulingDecision.NOT_SCHEDULE
        
        return decision
    
    def _fallback_response_parsing(
        self,
        response_text: str,
        available_slots: List[Dict]
    ) -> Tuple[SchedulingDecision, str, List[Dict], str]:
        """
        Fallback parsing when JSON parsing fails.
        
        Args:
            response_text: Raw response text
            available_slots: Available slots
            
        Returns:
            Tuple of (decision, reasoning, suggested_slots, response_message)
        """
        # Simple keyword-based parsing as fallback
        if 'SCHEDULE' in response_text.upper():
            decision = SchedulingDecision.SCHEDULE
            reasoning = "LLM indicated scheduling (fallback parsing)"
            suggested_slots = self._diversify_slot_selection(available_slots, max_slots=3)
        else:
            decision = SchedulingDecision.NOT_SCHEDULE
            reasoning = "LLM indicated not to schedule (fallback parsing)"
            suggested_slots = []
        
        response_message = "Let me help you with scheduling. Could you tell me your availability preferences?"
        
        return decision, reasoning, suggested_slots, response_message

    def format_slots_for_candidate(self, slots: List[Dict]) -> str:
        """Format available slots for display to candidate."""
        return self.prompts.format_time_slots(slots)
    
    def check_slot_availability(self, datetime_str: str) -> bool:
        """Check if a specific time slot is still available."""
        try:
            target_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            available_slots = self.sql_manager.get_available_slots(
                target_datetime.date(),
                target_datetime.date()
            )
            
            # Check if any slot matches the requested time
            for slot in available_slots:
                slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                if abs((slot_dt - target_datetime).total_seconds()) < 300:  # Within 5 minutes
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking slot availability: {e}")
            return False 