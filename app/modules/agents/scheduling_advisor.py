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
from app.modules.utils.datetime_parser import DateTimeParser, parse_scheduling_intent
from app.modules.database.sql_manager import SQLManager
from config.phase1_settings import get_settings


class SchedulingDecision(Enum):
    """Possible scheduling decisions."""
    SCHEDULE = "SCHEDULE"
    NOT_SCHEDULE = "NOT_SCHEDULE"


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
        
        # Initialize datetime parser
        self.datetime_parser = DateTimeParser()
        
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
        Make a scheduling decision based on conversation context and available slots.
        
        Args:
            candidate_info: Information about the candidate
            conversation_messages: Full conversation history
            latest_message: Most recent user message
            reference_datetime: Reference time for parsing (defaults to now)
            
        Returns:
            Tuple of (decision, reasoning, suggested_slots, response_message)
        """
        try:
            # Parse scheduling intent from the latest message
            scheduling_intent = parse_scheduling_intent(latest_message, reference_datetime)
            
            # Get available time slots based on parsed intent
            available_slots = self._get_available_slots(
                scheduling_intent.get('parsed_datetimes', []),
                reference_datetime or datetime.now()
            )
            
            # Prepare context for the LLM
            scheduling_context = {
                "candidate_info": candidate_info,
                "latest_message": latest_message,
                "message_count": len(conversation_messages),
                "availability_mentioned": scheduling_intent.get('has_scheduling_intent', False),
                "available_slots": available_slots
            }
            
            # Generate decision prompt
            decision_prompt = self.prompts.get_decision_prompt(
                candidate_info=candidate_info,
                latest_message=latest_message,
                message_count=len(conversation_messages),
                availability_mentioned=scheduling_intent.get('has_scheduling_intent', False),
                available_slots=available_slots
            )
            
            # Get decision from LLM
            response = self.scheduling_chain.invoke({"scheduling_input": decision_prompt})
            response_text = response.content
            
            # Parse the LLM response
            decision, reasoning, suggested_slots, response_message = self._parse_scheduling_response(
                response_text, available_slots
            )
            
            # Validate and enhance the decision
            decision = self._validate_scheduling_decision(decision, candidate_info, scheduling_intent)
            
            self.logger.info(f"Scheduling decision: {decision.value}, Reasoning: {reasoning}")
            
            return decision, reasoning, suggested_slots, response_message
            
        except Exception as e:
            self.logger.error(f"Error in scheduling decision: {e}")
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
                # No specific preferences, return next few available slots
                return all_slots[:5]  # Return up to 5 slots
            
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
            
            # If we have good matches, return them; otherwise return general available slots
            if matched_slots:
                return matched_slots[:3]  # Top 3 matches
            else:
                return all_slots[:3]  # Next 3 available slots
                
        except Exception as e:
            self.logger.error(f"Error getting available slots: {e}")
            return []
    
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
                        # Use the top available slots if LLM suggested scheduling
                        suggested_slots = available_slots[:3]
                
                return decision, reasoning, suggested_slots, response_message
            
            # If structured format not found, try to infer from content
            if any(keyword in response_text.lower() for keyword in ['schedule', 'appointment', 'available slots']):
                decision = SchedulingDecision.SCHEDULE
                reasoning = "Response indicates scheduling intent"
                suggested_slots = available_slots[:3]
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
        duration_minutes: int = 45
    ) -> Dict:
        """
        Book an interview appointment in the database.
        
        Args:
            candidate_info: Information about the candidate
            slot_datetime: Chosen appointment datetime
            recruiter_id: ID of the recruiter
            duration_minutes: Duration of the interview
            
        Returns:
            Dictionary with booking confirmation details
        """
        try:
            # Create appointment in database
            appointment_data = {
                'candidate_name': candidate_info.get('name', 'Unknown'),
                'candidate_email': candidate_info.get('email', ''),
                'candidate_phone': candidate_info.get('phone', ''),
                'scheduled_datetime': slot_datetime,
                'recruiter_id': recruiter_id,
                'duration_minutes': duration_minutes,
                'status': 'scheduled',
                'notes': f"Scheduled via chatbot. Experience: {candidate_info.get('experience', 'Not specified')}"
            }
            
            appointment_id = self.sql_manager.create_appointment(appointment_data)
            
            if appointment_id:
                self.logger.info(f"Successfully booked appointment {appointment_id}")
                
                # Get recruiter details
                recruiter = self.sql_manager.get_recruiter_by_id(recruiter_id)
                
                return {
                    'success': True,
                    'appointment_id': appointment_id,
                    'datetime': slot_datetime,
                    'recruiter': recruiter,
                    'duration': duration_minutes,
                    'confirmation_message': self._generate_confirmation_message(
                        slot_datetime, recruiter, duration_minutes
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
        
        return f"""🎉 **Interview Confirmed!**

📅 **Date & Time:** {formatted_datetime}
👤 **Interviewer:** {recruiter_name}
⏱️ **Duration:** {duration_minutes} minutes
📧 **Format:** Video call (link will be sent via email)

I'll send you a calendar invitation with all the details shortly. Please let me know if you need to reschedule or have any questions!"""
    
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
    
    def parse_candidate_time_preference(
        self,
        user_message: str,
        reference_datetime: datetime = None
    ) -> Dict:
        """
        Parse time preferences from candidate message.
        
        Args:
            user_message: Candidate's message
            reference_datetime: Reference time for parsing
            
        Returns:
            Dictionary with parsed time preferences
        """
        return parse_scheduling_intent(user_message, reference_datetime)
    
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