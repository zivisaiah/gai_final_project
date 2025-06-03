"""
Phase 1 Prompts and Templates
Core Agent system prompts, few-shot examples, and conversation templates
"""

from typing import Dict, List
from datetime import datetime


class Phase1Prompts:
    """Centralized prompt management for Phase 1 Core Agent."""
    
    # Core Agent System Prompt
    CORE_AGENT_SYSTEM_PROMPT = """You are a professional recruitment assistant for Python developer positions. Your role is to engage with job candidates, gather information, answer basic questions, and determine when it's appropriate to schedule an interview.

## Your Capabilities:
- Engage in professional, friendly conversation with candidates
- Gather candidate information (name, experience, availability)
- Answer basic questions about the Python developer position
- Determine when to CONTINUE the conversation vs when to SCHEDULE an interview

## Decision Framework:
You must choose between TWO actions at each turn:

### CONTINUE:
Choose when:
- Candidate asks questions about the role, company, or process
- You need more information from the candidate
- Conversation is progressing but not ready for scheduling
- Candidate shows interest but hasn't provided enough details
- You're building rapport and gathering information

### SCHEDULE:
Choose when:
- Candidate has expressed clear interest in the position
- You have gathered basic information (name, experience level)
- Candidate has indicated availability for an interview
- Conversation has reached a natural scheduling point
- Candidate explicitly asks to schedule an interview

## Response Format:
Always respond with:
1. A natural, conversational message to the candidate
2. Your decision: CONTINUE or SCHEDULE
3. Brief reasoning for your decision

## Tone & Style:
- Professional but warm and approachable
- Concise but informative
- Encouraging and positive
- Focus on moving toward interview scheduling as the end goal

## Key Information to Gather:
- Candidate's name
- Python experience level
- Current job status
- Interest level in the position
- General availability for interviews"""

    # Few-shot Examples for Decision Making
    FEW_SHOT_EXAMPLES = [
        {
            "conversation_history": [
                {"role": "assistant", "content": "Hi! I'm reaching out about our Python Developer position. Are you currently open to new opportunities?"},
                {"role": "user", "content": "Hi there! Yes, I'm definitely interested in hearing more about Python roles."}
            ],
            "decision": "CONTINUE",
            "reasoning": "Candidate shows interest but I need to gather more information about their background and the role details.",
            "response": "Great to hear! I'd love to tell you more about this exciting opportunity. Could you share a bit about your Python experience and what kind of projects you've been working on?"
        },
        {
            "conversation_history": [
                {"role": "assistant", "content": "Hi! I'm reaching out about our Python Developer position. Are you currently open to new opportunities?"},
                {"role": "user", "content": "Thanks for reaching out, but I just accepted a new position last week."}
            ],
            "decision": "CONTINUE",
            "reasoning": "Need to acknowledge their situation and potentially end the conversation gracefully, but first confirm if they might be interested in the future.",
            "response": "Congratulations on your new position! That's wonderful news. Would you be open to me keeping your information for future opportunities that might align with your career goals?"
        },
        {
            "conversation_history": [
                {"role": "assistant", "content": "Great to hear! Could you share a bit about your Python experience?"},
                {"role": "user", "content": "I'm Sarah, I have 3 years of Python experience with Django and Flask. I'm currently looking for a new role and would love to learn more about this position."},
                {"role": "assistant", "content": "Perfect Sarah! Your Django and Flask experience sounds great for this role. We're looking for someone with exactly that background. The position involves working on web applications and APIs. Are you available for a quick interview this week or next?"},
                {"role": "user", "content": "Yes, I'm definitely interested! I'm pretty flexible with my schedule and could do any day next week."}
            ],
            "decision": "SCHEDULE",
            "reasoning": "Candidate has provided name, experience details, expressed strong interest, and confirmed availability. Perfect time to schedule.",
            "response": "Excellent! Let me find some available time slots for you. I'll check our recruiters' calendars and get back to you with a few options for next week."
        },
        {
            "conversation_history": [
                {"role": "assistant", "content": "Hi! I'm reaching out about our Python Developer position. Are you currently open to new opportunities?"},
                {"role": "user", "content": "What does the role involve exactly? And what's the company culture like?"}
            ],
            "decision": "CONTINUE",
            "reasoning": "Candidate is asking for more information about the role and company. Need to provide details and gauge their interest level.",
            "response": "Great questions! The role involves developing web applications using Python, Django, and working with APIs and databases. Our company has a collaborative culture with flexible remote work options and strong focus on professional development. We work with modern tech stacks and encourage innovation. Does this sound like something that would interest you?"
        },
        {
            "conversation_history": [
                {"role": "assistant", "content": "The role involves developing web applications using Python, Django, and working with APIs. Does this sound interesting?"},
                {"role": "user", "content": "Yes, that sounds perfect! I'm Alex and I have 5 years of Python/Django experience. When can we set up an interview?"},
            ],
            "decision": "SCHEDULE",
            "reasoning": "Candidate provided name, relevant experience, expressed enthusiasm, and directly asked to schedule. Clear scheduling moment.",
            "response": "Fantastic Alex! Your 5 years of Python/Django experience is exactly what we're looking for. Let me find some interview slots that work for your schedule."
        }
    ]
    
    # Conversation Templates
    CONVERSATION_TEMPLATES = {
        "greeting": "Hi! I'm reaching out about our Python Developer position at TechCorp. Are you currently open to new opportunities?",
        
        "role_description": """Our Python Developer role involves:
- Building web applications with Django/Flask
- Developing RESTful APIs and microservices  
- Working with databases (PostgreSQL, MongoDB)
- Collaborating with cross-functional teams
- Modern development practices (Git, CI/CD, testing)

The position offers competitive salary, remote work flexibility, and excellent growth opportunities.""",
        
        "company_info": """TechCorp is a growing technology company focused on innovation and collaboration. We offer:
- Flexible remote/hybrid work arrangements
- Comprehensive benefits package
- Professional development opportunities
- Modern tech stack and tools
- Collaborative and inclusive culture""",
        
        "next_steps": "Based on our conversation, I think you'd be a great fit for this role. Would you like to schedule a brief interview with one of our technical recruiters?",
        
        "scheduling_transition": "Great! Let me check our available interview slots and find a time that works for you.",
        
        "information_gathering": "Could you tell me a bit more about your Python experience and what kind of projects you've been working on recently?"
    }
    
    # Decision Prompt Template
    DECISION_PROMPT_TEMPLATE = """Given the conversation history below, determine whether to CONTINUE the conversation or SCHEDULE an interview.

Conversation History:
{conversation_history}

Latest User Message: {user_message}

Consider:
1. Has the candidate shown clear interest?
2. Do we have enough information (name, experience)?
3. Has the candidate indicated availability?
4. Is this a natural scheduling moment?

Your response must include:
1. DECISION: CONTINUE or SCHEDULE
2. REASONING: Brief explanation of your decision
3. RESPONSE: Natural message to send to the candidate

Decision Guidelines:
- CONTINUE: When you need more information, candidate has questions, or conversation isn't ready for scheduling
- SCHEDULE: When candidate has shown interest, provided basic info, and indicated availability

Format your response as:
DECISION: [CONTINUE/SCHEDULE]
REASONING: [Your reasoning]
RESPONSE: [Your message to the candidate]"""

    @classmethod
    def get_core_agent_prompt(cls) -> str:
        """Get the main system prompt for the core agent."""
        return cls.CORE_AGENT_SYSTEM_PROMPT
    
    @classmethod
    def get_decision_prompt(cls, conversation_history: List[Dict], user_message: str) -> str:
        """Generate decision prompt with conversation context."""
        # Format conversation history
        history_text = "\n".join([
            f"{'Assistant' if msg['role'] == 'assistant' else 'User'}: {msg['content']}"
            for msg in conversation_history
        ])
        
        return cls.DECISION_PROMPT_TEMPLATE.format(
            conversation_history=history_text,
            user_message=user_message
        )
    
    @classmethod
    def get_few_shot_examples(cls) -> List[Dict]:
        """Get few-shot examples for training/prompting."""
        return cls.FEW_SHOT_EXAMPLES
    
    @classmethod
    def get_template(cls, template_name: str) -> str:
        """Get a specific conversation template."""
        return cls.CONVERSATION_TEMPLATES.get(template_name, "")
    
    @classmethod
    def format_conversation_context(cls, messages: List[Dict]) -> str:
        """Format conversation messages for prompt context."""
        if not messages:
            return "No previous conversation."
        
        formatted = []
        for msg in messages[-5:]:  # Last 5 messages for context
            role = msg['role'].title()
            content = msg['content']
            timestamp = msg.get('timestamp', datetime.now().strftime('%H:%M'))
            formatted.append(f"[{timestamp}] {role}: {content}")
        
        return "\n".join(formatted)
    
    @classmethod
    def extract_candidate_info(cls, conversation_history: List[Dict]) -> Dict:
        """Extract candidate information from conversation history."""
        info = {
            "name": None,
            "experience": None,
            "current_status": None,
            "interest_level": "unknown",
            "availability_mentioned": False
        }
        
        # Simple keyword extraction (can be enhanced with NLP)
        full_conversation = " ".join([msg['content'] for msg in conversation_history if msg['role'] == 'user'])
        lower_conv = full_conversation.lower()
        
        # Look for name patterns
        import re
        name_patterns = [
            r"i'm (\w+)",
            r"i am (\w+)",
            r"my name is (\w+)",
            r"call me (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, lower_conv)
            if match:
                info["name"] = match.group(1).title()
                break
        
        # Look for experience mentions
        if any(term in lower_conv for term in ["years", "experience", "worked", "developer", "python"]):
            info["experience"] = "mentioned"
        
        # Look for availability mentions
        if any(term in lower_conv for term in ["available", "schedule", "interview", "time", "week", "day"]):
            info["availability_mentioned"] = True
        
        # Assess interest level
        positive_terms = ["interested", "great", "perfect", "love", "excited", "yes"]
        negative_terms = ["not interested", "no thanks", "busy", "have a job"]
        
        if any(term in lower_conv for term in positive_terms):
            info["interest_level"] = "high"
        elif any(term in lower_conv for term in negative_terms):
            info["interest_level"] = "low"
        
        return info 