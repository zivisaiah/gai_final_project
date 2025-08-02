"""
Smart Mock Agent with Realistic Decision Logic
Enhanced mock agent that makes intelligent decisions based on conversation context
"""

import re
import random
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ConversationAnalysis:
    """Analysis of conversation context for decision making"""
    message_count: int
    user_engagement_level: str  # high, medium, low
    information_gathered: Dict[str, bool]  # experience, motivation, skills, etc.
    user_questions_asked: int
    technical_depth: str  # basic, intermediate, advanced
    readiness_for_scheduling: float  # 0.0 to 1.0

class SmartMockAgent:
    """Enhanced mock agent with realistic decision-making logic"""
    
    def __init__(self, agent_type: str = "CoreAgent"):
        self.agent_type = agent_type
        self.conversation_history: Dict[str, List] = {}
        self.decision_weights = {
            'CONTINUE': 0.4,
            'SCHEDULE': 0.2,
            'INFO': 0.25,
            'END': 0.15
        }
        
        # Keywords for different decision types
        self.continue_keywords = [
            'experience', 'background', 'tell me', 'about yourself', 'projects',
            'skills', 'worked on', 'current role', 'previous'
        ]
        
        self.info_keywords = [
            'what', 'how', 'why', 'when', 'where', 'company', 'team', 'role',
            'opportunities', 'culture', 'benefits', 'salary', 'remote', 'framework'
        ]
        
        self.schedule_indicators = [
            'interested', 'sounds good', 'like to', 'excited', 'when can',
            'available', 'schedule', 'interview', 'meet'
        ]
        
        self.end_indicators = [
            'not interested', 'not a fit', 'think about it', 'get back to you',
            'not sure', 'maybe later', 'not ready'
        ]
        
        # Response templates for each decision type
        self.response_templates = {
            'CONTINUE': [
                "Tell me more about your experience with Python development.",
                "Can you describe some of the projects you've worked on?",
                "What motivated you to pursue Python development?",
                "How would you describe your technical background?",
                "What kind of development work interests you most?",
                "Can you walk me through your programming experience?",
                "What technologies have you worked with recently?",
                "Tell me about your current role and responsibilities."
            ],
            'SCHEDULE': [
                "Based on our conversation, I'd like to schedule an interview. Are you available this week?",
                "You seem like a great fit for our team. Would you like to set up an interview?",
                "I'm impressed with your background. Let's schedule a technical interview.",
                "Your experience aligns well with what we're looking for. Can we schedule an interview?",
                "I'd love to continue this conversation in a formal interview. Are you interested?",
                "Based on what you've shared, I think you'd be a good candidate. Shall we schedule an interview?",
                "Your skills and experience look promising. Would you like to move forward with an interview?"
            ],
            'INFO': [
                "Our Python development team works primarily with Django and FastAPI for web applications.",
                "We focus on building scalable web applications and APIs using modern Python frameworks.",
                "The role involves working on microservices architecture with Docker and Kubernetes.",
                "Our team uses agile development practices with code reviews and continuous integration.",
                "We offer competitive salary, remote work flexibility, and excellent learning opportunities.",
                "The position includes working on both backend APIs and some full-stack development.",
                "Our company culture emphasizes collaboration, continuous learning, and work-life balance."
            ],
            'END': [
                "Thank you for your time today. We'll review your information and get back to you soon.",
                "I appreciate you sharing your background with me. We'll be in touch regarding next steps.",
                "Thanks for the conversation. We'll evaluate all candidates and follow up accordingly.",
                "I'll pass along your information to our hiring team. Expect to hear from us within a week.",
                "Thank you for your interest. We'll review your profile and contact you with any updates."
            ]
        }
    
    def analyze_conversation_context(self, conversation_id: str, user_message: str) -> ConversationAnalysis:
        """Analyze conversation context to make informed decisions"""
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        history = self.conversation_history[conversation_id]
        history.append(user_message.lower())
        
        # Count messages
        message_count = len(history)
        
        # Analyze user engagement
        avg_length = sum(len(msg) for msg in history) / len(history) if history else 0
        user_questions = sum(1 for msg in history if '?' in msg)
        
        if avg_length > 100 and user_questions > 0:
            engagement_level = "high"
        elif avg_length > 50 or user_questions > 0:
            engagement_level = "medium"  
        else:
            engagement_level = "low"
        
        # Check what information has been gathered
        full_text = ' '.join(history)
        information_gathered = {
            'experience': any(word in full_text for word in ['year', 'experience', 'worked', 'developer']),
            'technical_skills': any(word in full_text for word in ['python', 'django', 'flask', 'api', 'database']),
            'motivation': any(word in full_text for word in ['passionate', 'interested', 'excited', 'love']),
            'projects': any(word in full_text for word in ['project', 'built', 'developed', 'created']),
            'current_status': any(word in full_text for word in ['currently', 'working', 'employed', 'job'])
        }
        
        # Determine technical depth
        technical_terms = ['django', 'flask', 'fastapi', 'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes']
        tech_mentions = sum(1 for term in technical_terms if term in full_text)
        
        if tech_mentions >= 3:
            technical_depth = "advanced"
        elif tech_mentions >= 1:
            technical_depth = "intermediate"
        else:
            technical_depth = "basic"
        
        # Calculate readiness for scheduling
        info_score = sum(information_gathered.values()) / len(information_gathered)
        engagement_score = {'high': 1.0, 'medium': 0.6, 'low': 0.2}[engagement_level]
        length_score = min(1.0, message_count / 5.0)  # Optimal at 5 messages
        
        readiness = (info_score * 0.5) + (engagement_score * 0.3) + (length_score * 0.2)
        
        return ConversationAnalysis(
            message_count=message_count,
            user_engagement_level=engagement_level,
            information_gathered=information_gathered,
            user_questions_asked=user_questions,
            technical_depth=technical_depth,
            readiness_for_scheduling=readiness
        )
    
    def make_smart_decision(self, user_message: str, conversation_id: str) -> str:
        """Make an intelligent decision based on conversation context"""
        analysis = self.analyze_conversation_context(conversation_id, user_message)
        user_msg_lower = user_message.lower()
        
        # Decision logic based on context
        decision_scores = {'CONTINUE': 0, 'SCHEDULE': 0, 'INFO': 0, 'END': 0}
        
        # CONTINUE score - need more information
        if analysis.message_count < 3:
            decision_scores['CONTINUE'] += 0.6
        if sum(analysis.information_gathered.values()) < 3:
            decision_scores['CONTINUE'] += 0.4
        if analysis.user_engagement_level == 'high':
            decision_scores['CONTINUE'] += 0.2
        
        # INFO score - user asking questions
        if any(keyword in user_msg_lower for keyword in self.info_keywords):
            decision_scores['INFO'] += 0.8
        if '?' in user_message:
            decision_scores['INFO'] += 0.3
        if analysis.user_questions_asked > 0:
            decision_scores['INFO'] += 0.2
        
        # SCHEDULE score - good candidate, enough info gathered
        if analysis.readiness_for_scheduling > 0.7:
            decision_scores['SCHEDULE'] += 0.8
        if any(indicator in user_msg_lower for indicator in self.schedule_indicators):
            decision_scores['SCHEDULE'] += 0.5
        if analysis.user_engagement_level != 'low' and analysis.message_count >= 3:
            decision_scores['SCHEDULE'] += 0.3
        
        # END score - conversation not going well or complete
        if analysis.user_engagement_level == 'low' and analysis.message_count >= 4:
            decision_scores['END'] += 0.6
        if any(indicator in user_msg_lower for indicator in self.end_indicators):
            decision_scores['END'] += 0.8
        if analysis.message_count >= 8:  # Long conversation
            decision_scores['END'] += 0.4
        
        # Add some randomness for variety
        for decision in decision_scores:
            decision_scores[decision] += random.uniform(-0.1, 0.1)
        
        # Choose decision with highest score
        best_decision = max(decision_scores, key=decision_scores.get)
        
        # Fallback to CONTINUE if scores are too low
        if decision_scores[best_decision] < 0.3:
            best_decision = 'CONTINUE'
        
        return best_decision
    
    def generate_contextual_response(self, decision: str, user_message: str, conversation_id: str) -> str:
        """Generate a contextual response based on decision and conversation history"""
        templates = self.response_templates[decision]
        
        # For INFO responses, try to be more specific
        if decision == 'INFO':
            user_msg_lower = user_message.lower()
            if 'framework' in user_msg_lower or 'technology' in user_msg_lower:
                return "Our Python development team works primarily with Django and FastAPI for web applications."
            elif 'culture' in user_msg_lower or 'team' in user_msg_lower:
                return "Our company culture emphasizes collaboration, continuous learning, and work-life balance."
            elif 'remote' in user_msg_lower or 'work from home' in user_msg_lower:
                return "We offer flexible remote work options and support work-life balance."
            elif 'salary' in user_msg_lower or 'compensation' in user_msg_lower:
                return "We offer competitive salary packages with excellent benefits and growth opportunities."
        
        # For CONTINUE, vary the questions based on what we know
        if decision == 'CONTINUE':
            analysis = self.analyze_conversation_context(conversation_id, user_message)
            if not analysis.information_gathered.get('experience', False):
                return "Tell me more about your experience with Python development."
            elif not analysis.information_gathered.get('projects', False):
                return "Can you describe some of the projects you've worked on?"
            elif not analysis.information_gathered.get('motivation', False):
                return "What motivated you to pursue Python development?"
        
        # Default: random selection from templates
        return random.choice(templates)
    
    def process_message(self, message: str, conversation_id: str = None) -> Tuple[str, str, str]:
        """Process message and return response, decision, and reasoning"""
        if conversation_id is None:
            conversation_id = f"mock_{int(time.time())}"
        
        # Simulate processing time
        processing_time = random.uniform(0.8, 2.5)
        time.sleep(processing_time)
        
        # Make smart decision
        decision = self.make_smart_decision(message, conversation_id)
        
        # Generate contextual response
        response = self.generate_contextual_response(decision, message, conversation_id)
        
        # Generate reasoning
        analysis = self.analyze_conversation_context(conversation_id, message)
        reasoning = f"Smart {self.agent_type} decision: {decision} based on {analysis.message_count} messages, " \
                   f"{analysis.user_engagement_level} engagement, readiness: {analysis.readiness_for_scheduling:.2f}"
        
        return response, decision, reasoning
    
    def get_conversation_analysis(self, conversation_id: str) -> Optional[ConversationAnalysis]:
        """Get detailed analysis of a conversation"""
        if conversation_id not in self.conversation_history:
            return None
        
        # Get last message for analysis
        last_message = self.conversation_history[conversation_id][-1] if self.conversation_history[conversation_id] else ""
        return self.analyze_conversation_context(conversation_id, last_message)