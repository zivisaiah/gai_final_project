
"""
Improved Conversation Flow Implementation
Fixes for immediate dropout and early termination issues
"""

import random
from typing import Dict, List, Any

class ImprovedConversationFlow:
    """Enhanced conversation flow with fixes for common failure patterns"""
    
    def __init__(self):
        self.improved_greetings = {
            "eager_junior": "Hi there! I'm excited to learn about your background and interest in our Python developer role. What drew you to apply for this position?",
            "experienced_senior": "Good day! I'd love to discuss how your experience aligns with our Python developer position. Could you share what interests you most about this opportunity?",
            "career_changer": "Hello! I understand you're exploring opportunities in Python development. I'd be happy to discuss how this role might fit your career transition goals.",
            "passive_candidate": "Hi! Thanks for taking the time to explore this Python developer opportunity. What caught your attention about this role?",
            "difficult_candidate": "Hello! I appreciate you considering our Python developer position. What would you like to know about the role and our team?"
        }
        
        self.explicit_rejection_patterns = [
            "not interested", "no thank you", "not right for me", "changed my mind",
            "not looking", "found another", "withdraw application"
        ]
    
    def get_personalized_greeting(self, persona_id: str) -> str:
        """Get a personalized greeting based on persona"""
        return self.improved_greetings.get(persona_id, self.improved_greetings["eager_junior"])
    
    def should_end_conversation(self, user_message: str, conversation_length: int, 
                               agent_decision: str) -> bool:
        """Improved logic for determining if conversation should end"""
        
        # Minimum conversation length requirement
        if conversation_length < 3:
            return False
        
        # Check for explicit rejection
        user_lower = user_message.lower()
        has_explicit_rejection = any(pattern in user_lower for pattern in self.explicit_rejection_patterns)
        
        if has_explicit_rejection:
            return True
        
        # Check for engagement signals
        engagement_signals = ['interested', 'excited', 'want', 'would like', 'tell me more']
        has_engagement = any(signal in user_lower for signal in engagement_signals)
        
        if has_engagement:
            return False
        
        # Default: continue conversation unless explicit rejection
        return False
    
    def enhance_persona_response(self, base_response: str, persona_id: str) -> str:
        """Enhance persona responses to be more detailed and engaging"""
        
        if len(base_response) < 20:  # Too short, enhance it
            enhancements = {
                "eager_junior": " I'm really excited about this opportunity and would love to learn more!",
                "experienced_senior": " I have significant experience in this area and am interested in the technical challenges.",
                "career_changer": " I'm passionate about transitioning into this field and bringing my unique perspective.",
                "passive_candidate": " While I wasn't actively looking, this opportunity caught my attention.",
                "difficult_candidate": " I have some questions about the role and company culture."
            }
            
            enhancement = enhancements.get(persona_id, " I'd like to know more about this opportunity.")
            return base_response + enhancement
        
        return base_response
