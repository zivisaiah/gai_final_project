"""
Scheduling Advisor Prompts and Templates
Specialized prompts for scheduling interview appointments
"""

from typing import Dict, List, Optional
from datetime import datetime
import re


class SchedulingPrompts:
    """Centralized prompt management for Scheduling Advisor."""
    
    # Scheduling Advisor System Prompt
    SCHEDULING_ADVISOR_SYSTEM_PROMPT = """You are a specialized scheduling advisor for recruitment interviews. Your role is to determine when it's appropriate to schedule an interview and help find suitable time slots.

## Your Capabilities:
- Analyze conversation context to determine scheduling readiness
- Parse natural language date/time preferences from candidates
- Check available time slots in the recruiter calendar database
- Suggest optimal interview times based on candidate preferences
- Handle scheduling conflicts and alternatives

## Decision Framework:
You must determine whether to SCHEDULE or NOT_SCHEDULE based on:

### SCHEDULE Decision Criteria:
- Candidate has expressed clear interest in the position
- Basic candidate information has been gathered (name, experience)
- Candidate has indicated availability or requested scheduling
- Conversation has reached a natural scheduling point
- No major red flags or concerns

### NOT_SCHEDULE Decision Criteria:
- Insufficient candidate information
- Candidate hasn't expressed clear interest
- Timing concerns (too early in conversation)
- Candidate seems uncertain or hesitant
- Need to address candidate questions first

## Time Slot Selection Process:
1. Parse candidate's time preferences from conversation
2. Query available slots from recruiter calendars
3. Match candidate preferences with available slots
4. Suggest 2-3 best options with rationale
5. Consider business hours and recruiter availability

## Response Format:
Always provide:
1. DECISION: SCHEDULE or NOT_SCHEDULE
2. REASONING: Clear explanation of your decision
3. TIME_SLOTS: List of suggested slots (if scheduling)
4. RESPONSE: Natural message to candidate

## Scheduling Guidelines:
- Business hours: 9 AM - 6 PM, Monday-Friday
- Interview duration: 30-60 minutes (default 45 minutes)
- Provide multiple options when possible
- Consider candidate's timezone if mentioned
- Be flexible but professional"""

    # Few-shot Examples for Scheduling Decisions
    SCHEDULING_EXAMPLES = [
        {
            "conversation_context": {
                "candidate_info": {"name": "Sarah", "experience": "3 years Python", "interest_level": "high"},
                "latest_message": "I'm very interested! When can we schedule an interview?",
                "availability_mentioned": "next week",
                "message_count": 5
            },
            "available_slots": [
                {"datetime": "2024-01-15T10:00:00", "recruiter": "Alice Smith", "duration": 45},
                {"datetime": "2024-01-15T14:00:00", "recruiter": "Bob Johnson", "duration": 45},
                {"datetime": "2024-01-16T09:00:00", "recruiter": "Alice Smith", "duration": 45}
            ],
            "decision": "SCHEDULE",
            "reasoning": "Candidate has provided name, experience, expressed strong interest, and directly requested scheduling. Ready to proceed.",
            "suggested_slots": [
                {"datetime": "2024-01-15T10:00:00", "recruiter": "Alice Smith"},
                {"datetime": "2024-01-15T14:00:00", "recruiter": "Bob Johnson"},
                {"datetime": "2024-01-16T09:00:00", "recruiter": "Alice Smith"}
            ],
            "response": "Perfect! I have several time slots available next week. Here are three options that might work for you:\n\n1. Monday, January 15th at 10:00 AM with Alice Smith\n2. Monday, January 15th at 2:00 PM with Bob Johnson\n3. Tuesday, January 16th at 9:00 AM with Alice Smith\n\nEach interview will take about 45 minutes. Which of these times works best for your schedule?"
        },
        {
            "conversation_context": {
                "candidate_info": {"name": None, "experience": "mentioned", "interest_level": "medium"},
                "latest_message": "This sounds interesting. What's the next step?",
                "availability_mentioned": False,
                "message_count": 3
            },
            "available_slots": [],
            "decision": "NOT_SCHEDULE",
            "reasoning": "While candidate shows interest, we don't have their name yet and they haven't specifically indicated availability. Need more information first.",
            "suggested_slots": [],
            "response": "Great to hear you're interested! To move forward with scheduling an interview, I'd love to get your name and learn a bit more about your availability. Could you tell me your name and when you might be free for a 45-minute interview call?"
        },
        {
            "conversation_context": {
                "candidate_info": {"name": "Mike", "experience": "5 years Django", "interest_level": "high"},
                "latest_message": "I'm available tomorrow afternoon or Friday morning",
                "availability_mentioned": "tomorrow afternoon, Friday morning",
                "message_count": 6
            },
            "available_slots": [
                {"datetime": "2024-01-12T14:00:00", "recruiter": "Alice Smith", "duration": 45},
                {"datetime": "2024-01-12T15:30:00", "recruiter": "Bob Johnson", "duration": 45},
                {"datetime": "2024-01-14T09:00:00", "recruiter": "Alice Smith", "duration": 45},
                {"datetime": "2024-01-14T10:30:00", "recruiter": "Carol Davis", "duration": 45}
            ],
            "decision": "SCHEDULE",
            "reasoning": "Candidate provided specific availability preferences that match available slots. Ready to schedule with preference matching.",
            "suggested_slots": [
                {"datetime": "2024-01-12T14:00:00", "recruiter": "Alice Smith"},
                {"datetime": "2024-01-12T15:30:00", "recruiter": "Bob Johnson"},
                {"datetime": "2024-01-14T09:00:00", "recruiter": "Alice Smith"}
            ],
            "response": "Excellent, Mike! I have availability that matches your preferences perfectly:\n\n**Tomorrow Afternoon:**\n• 2:00 PM with Alice Smith\n• 3:30 PM with Bob Johnson\n\n**Friday Morning:**\n• 9:00 AM with Alice Smith\n\nAll interviews are about 45 minutes. Which option works best for you?"
        }
    ]
    
    # Prompt Templates
    SCHEDULING_TEMPLATES = {
        "slot_suggestion": """Here are the available interview times that match your preferences:

{formatted_slots}

Each interview will take approximately {duration} minutes. Which time slot works best for your schedule?""",
        
        "confirmation_request": """Great! I'd like to confirm your interview appointment:

📅 **Date & Time:** {formatted_datetime}
👤 **Interviewer:** {recruiter_name}
⏱️ **Duration:** {duration} minutes
📧 **Location:** Video call (link will be sent via email)

Does this time work for you? If yes, I'll send you a calendar invitation with all the details.""",
        
        "no_slots_available": """I checked our calendar and unfortunately don't have any available slots that match your preferred times. 

Our next available appointments are:
{alternative_slots}

Would any of these alternative times work for you, or would you prefer different days?""",
        
        "need_more_info": """To find the best interview time for you, could you let me know:

• Your preferred days (e.g., this week, next week, specific days)
• Your preferred times (e.g., morning, afternoon, specific hours)
• Any days or times you're NOT available

This will help me find the perfect slot for your interview!""",
        
        "timezone_clarification": """Just to confirm the timing - I'm showing {local_time} in our system. Is this in your local timezone, or should I adjust for a different timezone?""",
        
        "reschedule_options": """No problem! Let me find alternative times for you:

{alternative_slots}

Which of these would work better for your schedule?"""
    }
    
    # Decision Prompt Template
    SCHEDULING_DECISION_PROMPT = """Based on the conversation context and candidate information, determine whether to SCHEDULE an interview or NOT_SCHEDULE yet.

## Conversation Context:
- **Candidate Info:** {candidate_info}
- **Latest Message:** "{latest_message}"
- **Message Count:** {message_count}
- **Availability Mentioned:** {availability_mentioned}

## Available Time Slots:
{available_slots}

Consider:
1. Does the candidate have sufficient information provided (name, basic experience)?
2. Have they expressed clear interest in proceeding?
3. Is there scheduling intent in their message?
4. Are there suitable time slots available?

**Decision Guidelines:**
- SCHEDULE: When candidate is ready and suitable slots exist
- NOT_SCHEDULE: When need more info or conversation isn't ready

Your response must include:
1. **DECISION:** SCHEDULE or NOT_SCHEDULE
2. **REASONING:** Why you made this decision
3. **SUGGESTED_SLOTS:** List of best matching slots (if scheduling)
4. **RESPONSE:** Natural message to send to candidate

Format:
DECISION: [SCHEDULE/NOT_SCHEDULE]
REASONING: [Your reasoning]
SUGGESTED_SLOTS: [List of slots or empty if not scheduling]
RESPONSE: [Your message to candidate]"""

    @classmethod
    def get_scheduling_system_prompt(cls) -> str:
        """Get the main system prompt for scheduling advisor."""
        return cls.SCHEDULING_ADVISOR_SYSTEM_PROMPT
    
    @classmethod
    def get_decision_prompt(
        cls,
        candidate_info: Dict,
        latest_message: str,
        message_count: int,
        availability_mentioned: bool,
        available_slots: List[Dict]
    ) -> str:
        """Generate scheduling decision prompt with context."""
        
        # Format available slots for prompt
        if available_slots:
            slots_text = "\n".join([
                f"• {slot['datetime']} with {slot['recruiter']} ({slot['duration']} min)"
                for slot in available_slots
            ])
        else:
            slots_text = "No available slots in the specified timeframe"
        
        return cls.SCHEDULING_DECISION_PROMPT.format(
            candidate_info=candidate_info,
            latest_message=latest_message,
            message_count=message_count,
            availability_mentioned=availability_mentioned,
            available_slots=slots_text
        )
    
    @classmethod
    def format_time_slots(cls, slots: List[Dict], duration: int = 45) -> str:
        """Format time slots for display to candidate."""
        if not slots:
            return "No available time slots found."
        
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
            formatted_time = dt.strftime("%A, %B %d at %I:%M %p")
            recruiter = slot.get('recruiter', 'Our team')
            formatted_slots.append(f"{i}. {formatted_time} with {recruiter}")
        
        return "\n".join(formatted_slots)
    
    @classmethod
    def format_confirmation_details(
        cls,
        datetime_str: str,
        recruiter_name: str,
        duration: int = 45
    ) -> str:
        """Format appointment confirmation details."""
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        formatted_datetime = dt.strftime("%A, %B %d, %Y at %I:%M %p")
        
        return cls.SCHEDULING_TEMPLATES["confirmation_request"].format(
            formatted_datetime=formatted_datetime,
            recruiter_name=recruiter_name,
            duration=duration
        )
    
    @classmethod
    def get_template(cls, template_name: str) -> str:
        """Get a specific scheduling template."""
        return cls.SCHEDULING_TEMPLATES.get(template_name, "")
    
    @classmethod
    def get_scheduling_examples(cls) -> List[Dict]:
        """Get few-shot examples for scheduling decisions."""
        return cls.SCHEDULING_EXAMPLES
    
    @classmethod
    def extract_time_preferences(cls, conversation_messages: List[Dict]) -> Dict:
        """Extract time preferences from conversation history."""
        preferences = {
            "specific_times": [],
            "general_availability": [],
            "timezone": None,
            "preferred_days": [],
            "blackout_times": []
        }
        
        # Combine all user messages for analysis
        user_messages = [
            msg['content'] for msg in conversation_messages 
            if msg['role'] == 'user'
        ]
        full_text = " ".join(user_messages).lower()
        
        # Extract specific time mentions
        time_patterns = [
            r'\d{1,2}:\d{2}\s*(am|pm)',   # 2:30pm
            r'\d{1,2}\s*(am|pm)',         # 2pm
            r'morning', r'afternoon', r'evening', r'night'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, full_text)
            preferences["specific_times"].extend(matches)
        
        # Extract day preferences
        day_patterns = [
            r'monday', r'tuesday', r'wednesday', r'thursday', 
            r'friday', r'saturday', r'sunday',
            r'weekday', r'weekend', r'next week', r'this week'
        ]
        
        for pattern in day_patterns:
            if pattern in full_text:
                preferences["preferred_days"].append(pattern)
        
        # Extract availability statements
        availability_patterns = [
            r'available (.+?)(?:\.|$)',
            r'free (.+?)(?:\.|$)',
            r'can do (.+?)(?:\.|$)'
        ]
        
        for pattern in availability_patterns:
            matches = re.findall(pattern, full_text)
            preferences["general_availability"].extend(matches)
        
        return preferences 