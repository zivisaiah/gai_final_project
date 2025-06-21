"""
Scheduling Advisor Prompts and Templates
Specialized prompts for scheduling interview appointments
"""

from typing import Dict, List, Optional
from datetime import datetime
import re


class SchedulingPrompts:
    """Centralized prompt management for Scheduling Advisor."""
    
    # Enhanced Unified Scheduling Advisor System Prompt
    SCHEDULING_ADVISOR_SYSTEM_PROMPT = """You are a specialized scheduling advisor for recruitment interviews. Your role is to analyze scheduling intent, parse time preferences, and determine when to schedule interviews.

**IMPORTANT: You must always respond in English only. Never use any other language in your responses.**

## UNIFIED ANALYSIS PROCESS:
For each candidate message, you must perform THREE tasks in a single analysis:

### 1. INTENT DETECTION
Analyze the message for scheduling intent with high accuracy:

**STRONG SCHEDULING INTENT** (confidence 0.8-1.0):
- Direct requests: "Let's schedule", "When can we meet?", "Book an interview"
- Clear availability: "I'm free Monday", "Available next week", "Can do mornings"
- Proceeding signals: "What's next?", "Ready to move forward", "Looking forward to next steps"
- **SLOT CONFIRMATION**: "That works for me", "Friday at 2pm would be great", "I'll take the 9am slot", "Perfect, let's do Monday"

**MODERATE SCHEDULING INTENT** (confidence 0.5-0.7):
- Implied interest: "Would be great to connect", "Let's talk soon"
- Flexible availability: "Pretty flexible", "Open to suggestions"
- General timing: "sometime next week", "in the coming days"

**LOW/NO SCHEDULING INTENT** (confidence 0.0-0.4):
- Information requests: "What does this job involve?", "What's the salary?"
- Background sharing: "I have 5 years experience", "I work with Python"
- Clarification needs: "Can you tell me more about...", "I'm not sure about..."
- Rejection signals: "Not interested", "Found another job", "Pass on this"

### 2. TIME PREFERENCE PARSING
Extract time/date preferences using natural language understanding:

**Day Preferences:**
- Specific days: "Monday", "Tuesday", "Friday", etc.
- Day types: "weekdays", "weekends", "business days"
- Relative days: "tomorrow", "next week", "this Friday"
- Exclusions: "not Wednesday", "except Monday"

**Time Preferences:**
- Specific times: "2pm", "9:30am", "3 o'clock"
- Time periods: "morning", "afternoon", "evening", "lunch time"
- Ranges: "between 2-4pm", "after 10am", "before 5pm"
- Patterns: "early", "late", "mid-day"

**Complex Expressions:**
- "Mondays only" → Only Monday scheduling
- "I'm free mornings except Wednesday" → Morning preference with Wednesday exclusion
- "Can do afternoons next week" → Afternoon preference with week specification
- "Available any time Friday" → Full Friday availability

### 3. SCHEDULING DECISION
Determine whether to SCHEDULE or NOT_SCHEDULE based on:

**SCHEDULE Decision Criteria:**
- Strong/moderate scheduling intent (confidence ≥ 0.5)
- Sufficient candidate info (name + experience or high interest)
- Available slots match preferences
- Conversation readiness

**CONFIRM_SLOT Decision Criteria:**
- User message references a specific time slot that was previously offered
- Contains confirmation language ("works for me", "that's perfect", "let's do", specific time/date mentioned)
- Candidate appears to be selecting from previously presented options

**NOT_SCHEDULE Decision Criteria:**
- Low scheduling intent (confidence < 0.5)
- Missing essential candidate information
- No suitable slots available
- Need to address candidate questions first

## ENHANCED CAPABILITIES:
- **Context Understanding**: Consider full conversation history
- **Informal Language**: Handle "Would be great to connect", "Let's chat"
- **Complex Preferences**: Parse multi-condition availability
- **Confidence Scoring**: Provide accurate intent confidence levels
- **Smart Matching**: Match preferences with available slots intelligently

## RESPONSE FORMAT:
Your response must be structured JSON with this exact format:

{{
  "intent_analysis": {{
    "has_scheduling_intent": true,
    "confidence": 0.85,
    "reasoning": "explanation of intent detection"
  }},
  "time_preferences": {{
    "parsed_expressions": ["list of identified time expressions"],
    "preferred_days": ["Monday", "Friday"],
    "preferred_times": ["morning", "2pm"],
    "exclusions": ["Wednesday"],
    "flexibility": "high"
  }},
  "decision": "SCHEDULE|CONFIRM_SLOT|NOT_SCHEDULE",
  "reasoning": "comprehensive decision explanation",
  "suggested_slots": [
    {{
      "datetime": "2024-12-16T09:00:00",
      "recruiter": "Sarah Johnson",
      "match_reason": "why this slot matches preferences"
    }}
  ],
  "response_message": "natural language response to candidate"
}}

## SCHEDULING GUIDELINES:
- Business hours: 9 AM - 6 PM, Monday-Friday
- Interview duration: 45 minutes (default)
- Provide 2-3 best matching options
- Consider timezone if mentioned
- Be conversational and helpful"""

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
        },
        {
            "conversation_context": {
                "candidate_info": {"name": "Lisa", "experience": "4 years Python", "interest_level": "high"},
                "latest_message": "Friday at 2pm would be perfect",
                "availability_mentioned": True,
                "message_count": 8,
                "conversation_history": [
                    {"role": "assistant", "content": "I have three available slots: Thursday 2pm, Friday 2pm, or Monday 10am"},
                    {"role": "user", "content": "Friday at 2pm would be perfect"}
                ]
            },
            "available_slots": [
                {"datetime": "2024-01-19T14:00:00", "recruiter": "Sarah Wilson", "duration": 45}
            ],
            "decision": "CONFIRM_SLOT",
            "reasoning": "User is specifically confirming the Friday 2pm slot that was previously offered. This is a clear slot confirmation rather than a new scheduling request.",
            "suggested_slots": [
                {"datetime": "2024-01-19T14:00:00", "recruiter": "Sarah Wilson"}
            ],
            "response": "Perfect! I'll book your interview for Friday, January 19th at 2:00 PM with Sarah Wilson. You'll receive a calendar invitation shortly with all the details."
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
    
    # Enhanced Unified Decision Prompt Template
    SCHEDULING_DECISION_PROMPT = """Perform unified scheduling analysis for this recruitment conversation.

## CONVERSATION CONTEXT:
- **Candidate Info:** {candidate_info}
- **Latest Message:** "{latest_message}"
- **Message Count:** {message_count}
- **Available Slots:** {available_slots}
- **Conversation History:** {conversation_history}

## YOUR TASK:
Analyze the latest message and provide a complete unified response covering:

1. **INTENT DETECTION**: Does the message show scheduling intent? What confidence level?
2. **TIME PREFERENCE PARSING**: Extract any date/time preferences mentioned
3. **SCHEDULING DECISION**: Should we schedule now or continue conversation?
4. **SLOT MATCHING**: If scheduling, which available slots best match preferences?

## ANALYSIS INSTRUCTIONS:

### Intent Detection:
- Look for scheduling keywords, availability statements, or proceeding signals
- Consider context from previous conversation
- Handle informal language like "would be great to connect"
- Provide confidence score 0.0-1.0

### Time Preference Parsing:
- Extract day preferences (Monday, weekdays, tomorrow, etc.)
- Identify time preferences (morning, 2pm, afternoons, etc.)
- Note any exclusions or constraints
- Handle complex expressions like "Mondays only" or "mornings except Wednesday"

### Decision Logic:
- **SCHEDULE** if: scheduling intent ≥ 0.5 + sufficient candidate info + available slots
- **NOT_SCHEDULE** if: low intent OR missing info OR no suitable slots

### Slot Matching:
- Match available slots to parsed preferences
- Prioritize exact matches over approximate
- Explain why each slot was selected
- Consider day preferences first, then time preferences

## REQUIRED JSON RESPONSE FORMAT:
Respond with ONLY valid JSON in this exact format:

{{
  "intent_analysis": {{
    "has_scheduling_intent": true,
    "confidence": 0.85,
    "reasoning": "detailed explanation of intent detection"
  }},
  "time_preferences": {{
    "parsed_expressions": ["Monday only", "can do"],
    "preferred_days": ["Monday"],
    "preferred_times": [],
    "exclusions": [],
    "flexibility": "low"
  }},
  "decision": "SCHEDULE",
  "reasoning": "comprehensive explanation of scheduling decision",
  "suggested_slots": [
    {{
      "datetime": "2024-12-16T09:00:00",
      "recruiter": "Sarah Johnson",
      "match_reason": "Monday slot matches preference"
    }}
  ],
  "response_message": "Perfect! I found some Monday interview slots that work for you..."
}}

Current date/time reference: {current_datetime}

IMPORTANT: Respond with valid JSON only, no other text."""

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
        available_slots: List[Dict],
        current_datetime: datetime = None,
        conversation_history: List[Dict] = None
    ) -> str:
        """Generate unified scheduling decision prompt with context."""
        
        # Format available slots for prompt
        if available_slots:
            slots_text = "[\n" + ",\n".join([
                f'  {{"datetime": "{slot.get("datetime", "")}", "recruiter": "{slot.get("recruiter", "")}", "duration": {slot.get("duration", 45)}}}'
                for slot in available_slots[:10]  # Limit to 10 slots for prompt size
            ]) + "\n]"
        else:
            slots_text = "[]"
        
        # Use current datetime or default
        current_dt = current_datetime or datetime.now()
        current_dt_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format conversation history for context (last 5 messages for slot confirmation detection)
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-5:]  # Last 5 messages
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])
        
        return cls.SCHEDULING_DECISION_PROMPT.format(
            candidate_info=candidate_info,
            latest_message=latest_message,
            message_count=message_count,
            available_slots=slots_text,
            current_datetime=current_dt_str,
            conversation_history=history_text
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