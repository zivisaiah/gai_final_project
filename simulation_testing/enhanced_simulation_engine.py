"""
Enhanced Simulation Engine with Critical Fixes Applied
Implements the fixes identified in Phase 3A conversation failure analysis
"""

import sys
import time
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation_testing.config.test_config import config
from simulation_testing.personas.persona_loader import persona_loader
from simulation_testing.metrics.metrics_collector import metrics_collector
from simulation_testing.agents.smart_mock_agent import SmartMockAgent


class EnhancedSimulatedUser:
    """Enhanced simulated user with improved conversation flow"""
    
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.persona_data = persona_loader.get_persona(persona_id)
        self.logger = logging.getLogger(f"{__name__}.{persona_id}")
        
        if not self.persona_data:
            raise ValueError(f"Could not load persona data for {persona_id}")
        
        # Enhanced response templates with more detail and engagement
        self.enhanced_response_templates = {
            "eager_junior": [
                "Hi! I'm really excited about this opportunity! I've been learning Python for about {timeframe} and I'm passionate about developing my skills in a professional environment. I've worked on several personal projects including {project_type} and I'm eager to contribute to a team. What aspects of the role would you like to know more about?",
                "Hello! Thank you for reaching out! I'm very interested in this Python developer position. I have experience with basic web frameworks and I've been building projects to strengthen my skills. I'm particularly drawn to backend development and would love to learn more about how I could contribute to your team.",
                "Hi there! This sounds like an amazing opportunity! I've been studying Python development intensively and have created several projects to demonstrate my skills. I'm especially interested in API development and I'm excited about the possibility of growing with your team. Could you tell me more about the day-to-day responsibilities?"
            ],
            "experienced_senior": [
                "Good day. I have 8+ years of experience in Python development, specializing in backend systems and API design. I've led teams of 3-5 developers and have experience with Django, FastAPI, and microservices architecture. I'm interested in understanding more about the technical challenges this role involves and the team structure.",
                "Hello. I'm currently a Senior Python Developer with extensive experience in fintech applications. I've architected and deployed scalable web applications and am skilled in database optimization and system design. What I'd like to know is how this role would leverage my expertise in distributed systems and what growth opportunities exist.",
                "Hi. I bring 10+ years of Python development experience across various industries including healthcare and e-commerce. I've managed full-stack development projects and have deep expertise in performance optimization. I'm evaluating this opportunity based on technical complexity, team dynamics, and potential for innovation. Could you elaborate on the current technical stack and challenges?"
            ],
            "career_changer": [
                "Hello! I'm in the process of transitioning from marketing to Python development. I've been learning for about 18 months and I'm eager to find the right opportunity to start my tech career. I've completed several bootcamp projects and built a portfolio website. I bring strong analytical and communication skills from my previous role. What kind of mentorship and growth opportunities does your team offer?",
                "Hi there! I'm making a career change into Python development after 5 years in project management. I've been studying intensively and have completed projects in web development and data analysis. I'm particularly interested in how my background in stakeholder management could complement technical skills. Could you tell me about the learning curve and support available for someone with my profile?",
                "Good day! I'm transitioning into Python development from a finance background. I've been coding for over a year and have built applications for portfolio management and data visualization. I believe my domain expertise combined with programming skills could bring unique value. What opportunities are there for someone looking to bridge business and technical domains?"
            ],
            "passive_candidate": [
                "Hi, thanks for reaching out. I'm not actively looking but I'm always open to hearing about interesting opportunities. I currently work as a Python developer focusing on automation and data processing. What makes this role particularly compelling? I'd need to understand the unique aspects that would make a move worthwhile.",
                "Hello. While I'm content in my current position, I'm curious about what you have in mind. I specialize in Python for data science and machine learning applications. What specific challenges or projects would I be working on that might not be available elsewhere?",
                "Good afternoon. I appreciate you thinking of me for this role. I'm currently employed and reasonably satisfied, but I'm always interested in learning about opportunities that could advance my career significantly. What can you tell me about the technical challenges and growth potential in this position?"
            ],
            "difficult_candidate": [
                "Hmm, I'm not sure this is what I'm looking for. I've had some bad experiences with recruitment processes before. What makes your company different? I need to know this isn't going to be a waste of my time. What exactly are the requirements and what's the compensation range?",
                "I suppose I can hear you out, but I have some concerns. I've seen a lot of job descriptions that don't match reality. How do I know this role is actually what you're describing? What evidence can you provide about the company culture and actual day-to-day work?",
                "Okay, I'll listen, but I need straight answers. I don't have time for generic responses. What specific technologies are you using? What are the real challenges I'd be facing? And let's be honest about the expectations and growth potential."
            ]
        }
        
        # Explicit rejection patterns (when user should end conversation)
        self.rejection_patterns = [
            "not interested", "no thank you", "not right for me", "changed my mind",
            "not looking", "found another", "withdraw application", "pass on this"
        ]
        
        # Track conversation state
        self.engagement_level = self._get_initial_engagement()
        self.conversation_turns = 0
        self.received_good_info = False
        
    def _get_initial_engagement(self) -> float:
        """Get initial engagement level based on persona"""
        engagement_levels = {
            "eager_junior": 0.9,
            "experienced_senior": 0.7,
            "career_changer": 0.8,
            "passive_candidate": 0.4,
            "difficult_candidate": 0.3
        }
        return engagement_levels.get(self.persona_id, 0.6)
    
    def generate_response(self, agent_message: str, conversation_context: Dict) -> str:
        """Generate enhanced, more detailed user response"""
        self.conversation_turns += 1
        conversation_log = conversation_context.get('conversation_log', [])
        
        # For first response, use enhanced templates
        if self.conversation_turns == 1:
            return self._generate_enhanced_first_response(agent_message)
        
        # Analyze agent message for quality and relevance
        agent_quality = self._analyze_agent_message_quality(agent_message)
        
        # Update engagement based on agent quality
        if agent_quality > 0.7:
            self.engagement_level = min(1.0, self.engagement_level + 0.1)
            self.received_good_info = True
        elif agent_quality < 0.3:
            self.engagement_level = max(0.0, self.engagement_level - 0.2)
        
        # Generate appropriate response based on context
        if self.engagement_level < 0.2:
            return self._generate_disengagement_response()
        elif self.engagement_level > 0.8:
            return self._generate_high_engagement_response(agent_message)
        else:
            return self._generate_moderate_response(agent_message)
    
    def _generate_enhanced_first_response(self, agent_message: str) -> str:
        """Generate enhanced first response using detailed templates"""
        templates = self.enhanced_response_templates.get(self.persona_id, [])
        
        if not templates:
            # Fallback to basic response with enhancement
            basic_response = f"Hello! I'm interested in learning more about this Python developer position."
            return self._enhance_response(basic_response)
        
        # Choose template and customize
        template = random.choice(templates)
        
        # Fill in placeholders with realistic values
        customizations = {
            "timeframe": random.choice(["6 months", "1 year", "18 months"]),
            "project_type": random.choice(["web scraping tools", "REST APIs", "data analysis scripts"]),
            "project_count": random.choice(["3", "5", "several"]),
            "specialization": random.choice(["backend development", "data processing", "web applications"]),
            "tech_stack": random.choice(["Django and PostgreSQL", "Flask and SQLite", "FastAPI and Redis"])
        }
        
        # Apply customizations
        enhanced_response = template
        for key, value in customizations.items():
            enhanced_response = enhanced_response.replace(f"{{{key}}}", value)
        
        return enhanced_response
    
    def _analyze_agent_message_quality(self, agent_message: str) -> float:
        """Analyze the quality of agent message to determine engagement impact"""
        score = 0.5  # Base score
        
        # Positive indicators
        if len(agent_message) > 50:  # Detailed response
            score += 0.2
        if "?" in agent_message:  # Asks questions
            score += 0.1
        if any(word in agent_message.lower() for word in ['experience', 'skills', 'background']):
            score += 0.1
        if any(word in agent_message.lower() for word in ['team', 'company', 'role', 'opportunity']):
            score += 0.1
        
        # Negative indicators
        if len(agent_message) < 20:  # Too short
            score -= 0.3
        if agent_message.count('.') <= 1:  # Not enough detail
            score -= 0.1
        if "thank you" in agent_message.lower() and len(agent_message) < 30:  # Generic thanks
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _generate_disengagement_response(self) -> str:
        """Generate response when user is becoming disengaged"""
        disengagement_responses = {
            "eager_junior": "I'm not sure this is the right fit for me right now. Thanks anyway.",
            "experienced_senior": "I don't think this aligns with what I'm looking for. Thank you for your time.",
            "career_changer": "This might not be the best opportunity for someone at my experience level.",
            "passive_candidate": "I think I'll pass on this opportunity. Thanks for reaching out.",
            "difficult_candidate": "This doesn't sound like what I expected. I'm not interested."
        }
        
        return disengagement_responses.get(self.persona_id, "I don't think this is right for me.")
    
    def _generate_high_engagement_response(self, agent_message: str) -> str:
        """Generate response when user is highly engaged"""
        high_engagement_responses = {
            "eager_junior": "That sounds really exciting! I'd love to learn more about the technical challenges and how I could contribute. When could we schedule a more detailed discussion?",
            "experienced_senior": "This aligns well with my experience and interests. I'd like to discuss the technical architecture and team dynamics in more detail. What would be the next step?",
            "career_changer": "This sounds like exactly the kind of opportunity I've been preparing for! I'm very interested in moving forward. Could we schedule an interview to discuss my background in detail?",
            "passive_candidate": "You know what, this actually sounds quite interesting. I wasn't expecting such a compelling opportunity. I'd be open to learning more about the role and team.",
            "difficult_candidate": "Okay, I have to admit this sounds better than I expected. You've addressed my main concerns. What's the interview process like?"
        }
        
        base_response = high_engagement_responses.get(self.persona_id, "This sounds very interesting! I'd like to know more.")
        return base_response
    
    def _generate_moderate_response(self, agent_message: str) -> str:
        """Generate moderate engagement response"""
        # Extract what the agent is asking about
        if "experience" in agent_message.lower():
            return self._respond_about_experience()
        elif "schedule" in agent_message.lower() or "interview" in agent_message.lower():
            return self._respond_about_scheduling()
        elif "company" in agent_message.lower() or "team" in agent_message.lower():
            return self._respond_about_company()
        else:
            return self._generate_general_response()
        
    def _respond_about_experience(self) -> str:
        """Generate response about experience"""
        experience_responses = {
            "eager_junior": "I have about a year of experience with Python, mostly through personal projects and online courses. I've built web scrapers, worked with APIs, and created some data analysis tools. I'm really eager to apply these skills in a professional environment.",
            "experienced_senior": "I have 8+ years of Python development experience, primarily in backend systems. I've worked with Django, Flask, and FastAPI, and have experience with database design and optimization. I've also led development teams and mentored junior developers.",
            "career_changer": "While I'm newer to Python professionally, I've been coding intensively for the past 18 months. I've completed several projects including a portfolio tracker and data visualization dashboard. My previous background in business analysis helps me understand requirements and user needs.",
            "passive_candidate": "I currently work as a Python developer focusing on automation and data processing. I have solid experience with pandas, numpy, and web frameworks. I'm comfortable with both scripting and application development.",
            "difficult_candidate": "I have several years of Python experience, but I want to make sure this role actually uses modern practices. Are you using current versions of Python? What about testing frameworks and deployment practices?"
        }
        
        return experience_responses.get(self.persona_id, "I have experience with Python development and am looking to grow my skills further.")
    
    def _respond_about_scheduling(self) -> str:
        """Generate response about scheduling"""
        scheduling_responses = {
            "eager_junior": "Yes, I'd love to schedule an interview! I'm very flexible with timing. When works best for your team?",
            "experienced_senior": "I'd be interested in scheduling a technical interview. I prefer early morning or late afternoon slots. What does your interview process typically involve?",
            "career_changer": "I'd be very interested in scheduling an interview. I'm available most days and would appreciate the opportunity to discuss how my background could contribute to your team.",
            "passive_candidate": "I could be open to scheduling a conversation, though I'd want to understand more about the role first. What would the interview process look like?",
            "difficult_candidate": "Before we schedule anything, I need to know more about what the interview involves. Are we talking about technical tests, multiple rounds, or what exactly?"
        }
        
        return scheduling_responses.get(self.persona_id, "I'd be open to scheduling a discussion about the role.")
    
    def _respond_about_company(self) -> str:
        """Generate response about company/team"""
        company_responses = {
            "eager_junior": "I'd love to learn more about the team and company culture! What's it like working there? Are there opportunities for mentorship and growth?",
            "experienced_senior": "I'm interested in understanding the team structure and technical culture. How do you handle code reviews, technical decisions, and professional development?",
            "career_changer": "Company culture is really important to me, especially as someone transitioning careers. How supportive is the environment for people learning and growing?",
            "passive_candidate": "I'd want to know what makes your company different from others. What are the unique aspects of working there?",
            "difficult_candidate": "I need to know the real story about the company culture. What are the actual pros and cons of working there?"
        }
        
        return company_responses.get(self.persona_id, "I'd like to know more about the company and team.")
    
    def _generate_general_response(self) -> str:
        """Generate general response when topic is unclear"""
        general_responses = {
            "eager_junior": "That's interesting! Could you tell me more about what a typical day would look like in this role?",
            "experienced_senior": "I'd like to understand more about the technical challenges and opportunities this role offers.",
            "career_changer": "Could you help me understand how someone with my background would fit into this role?",
            "passive_candidate": "What specific aspects of this opportunity make it worth considering?",
            "difficult_candidate": "I need more concrete details about what this role actually involves."
        }
        
        return general_responses.get(self.persona_id, "Could you tell me more about this opportunity?")
    
    def _enhance_response(self, base_response: str) -> str:
        """Enhance a basic response to be more detailed and engaging"""
        if len(base_response) < 30:  # Too short, needs enhancement
            enhancements = {
                "eager_junior": " I'm really excited about this opportunity and would love to learn more!",
                "experienced_senior": " I have significant experience in this area and am interested in the technical challenges.",
                "career_changer": " I'm passionate about transitioning into this field and bringing my unique perspective.",
                "passive_candidate": " While I wasn't actively looking, this opportunity caught my attention.",
                "difficult_candidate": " I have some questions about the role and company culture."
            }
            
            enhancement = enhancements.get(self.persona_id, " I'd like to know more about this opportunity.")
            return base_response + enhancement
        
        return base_response
    
    def should_continue_conversation(self, conversation_context: Dict) -> bool:
        """Enhanced logic for determining if user should continue conversation"""
        conversation_log = conversation_context.get('conversation_log', [])
        
        # Always continue for at least 2 exchanges (prevent immediate dropout)
        if len(conversation_log) < 4:  # 2 user messages, 2 agent messages
            return True
        
        # Check engagement level
        if self.engagement_level < 0.2:
            return False
        
        # Persona-specific continuation logic
        if self.persona_id == "difficult_candidate" and self.conversation_turns > 8:
            return False  # Gets impatient
        elif self.persona_id == "passive_candidate" and not self.received_good_info and self.conversation_turns > 5:
            return False  # Loses interest if not convinced
        elif self.persona_id == "eager_junior":
            return self.conversation_turns < 15  # Very persistent
        
        # Default: continue if engaged
        return self.engagement_level > 0.3
    
    def should_accept_scheduling(self, conversation_context: Dict) -> bool:
        """Enhanced logic for accepting scheduling offers"""
        # Always more likely to accept if highly engaged
        if self.engagement_level > 0.8:
            return True
        
        # Persona-specific acceptance rates
        acceptance_rates = {
            "eager_junior": 0.9,
            "experienced_senior": 0.7,
            "career_changer": 0.8,
            "passive_candidate": 0.5,
            "difficult_candidate": 0.4
        }
        
        base_rate = acceptance_rates.get(self.persona_id, 0.6)
        
        # Adjust based on engagement
        adjusted_rate = base_rate * (0.5 + 0.5 * self.engagement_level)
        
        return random.random() < adjusted_rate


class EnhancedSmartMockAgent(SmartMockAgent):
    """Enhanced agent with improved decision logic and conversation flow"""
    
    def __init__(self, agent_name: str):
        super().__init__(agent_name)
        
        # Persona-specific greetings to prevent immediate dropout
        self.improved_greetings = {
            "eager_junior": "Hi there! I'm excited to learn about your background and interest in our Python developer role. What drew you to apply for this position?",
            "experienced_senior": "Good day! I'd love to discuss how your experience aligns with our Python developer position. Could you share what interests you most about this opportunity?",
            "career_changer": "Hello! I understand you're exploring opportunities in Python development. I'd be happy to discuss how this role might fit your career transition goals. What's driving your interest in this field?",
            "passive_candidate": "Hi! Thanks for taking the time to explore this Python developer opportunity. I know you might not be actively looking, so I'd love to understand what caught your attention about this role.",
            "difficult_candidate": "Hello! I appreciate you considering our Python developer position. What would you like to know about the role and our team?"
        }
        
        # Explicit rejection patterns that should lead to END
        self.explicit_rejection_patterns = [
            "not interested", "no thank you", "not right for me", "changed my mind",
            "not looking", "found another", "withdraw application", "pass on this"
        ]
    
    def get_personalized_greeting(self, persona_id: str) -> str:
        """Get personalized greeting based on persona"""
        return self.improved_greetings.get(persona_id, 
            "Hello! Thank you for your interest in our Python developer position. Could you tell me a bit about yourself and your experience?")
    
    def process_message(self, user_message: str, conversation_id: str, 
                       conversation_length: int = 0, persona_id: str = None) -> Tuple[str, str, str]:
        """Enhanced message processing with improved decision logic"""
        
        # Check for explicit rejection first
        user_lower = user_message.lower()
        has_explicit_rejection = any(pattern in user_lower for pattern in self.explicit_rejection_patterns)
        
        if has_explicit_rejection:
            return (
                "Thank you for your time and honesty. I understand this isn't the right fit for you. Best of luck with your career!",
                "END",
                "User explicitly rejected the opportunity"
            )
        
        # Prevent premature END decisions - require minimum conversation length
        if conversation_length < 3:
            # For early conversation, be more engaging and informative
            if "experience" in user_lower:
                response = "That's great to hear about your experience! Our Python developer role involves working on scalable web applications and APIs. We use modern frameworks like Django and FastAPI. What specific areas of Python development are you most passionate about?"
                return (response, "CONTINUE", "Early conversation - gathering more information about experience")
            
            elif "interested" in user_lower or "excited" in user_lower:
                response = "Wonderful! I can tell you're enthusiastic about this opportunity. Let me share more about what makes this role special - you'd be working with a collaborative team on challenging technical problems. What aspects of the role would you like to explore first?"
                return (response, "CONTINUE", "User showing strong interest - continuing engagement")
            
            else:
                response = "I'd love to learn more about your background and interests. This Python developer position offers great opportunities for growth and technical challenges. What draws you to Python development?"
                return (response, "CONTINUE", "Early conversation - building engagement")
        
        # For longer conversations, use original decision logic but with more conservative END criteria
        response, decision, reasoning = super().process_message(user_message, conversation_id)
        
        # Override END decisions unless clearly justified
        if decision == "END" and conversation_length < 5:
            # Check if user is showing any engagement signals
            engagement_signals = ['interested', 'excited', 'want', 'would like', 'tell me more', 'learn more']
            has_engagement = any(signal in user_lower for signal in engagement_signals)
            
            if has_engagement:
                return (response, "CONTINUE", "Overriding END - user showing engagement signals")
        
        return (response, decision, reasoning)


def main():
    """Test the enhanced simulation engine"""
    print(">> Testing Enhanced Simulation Engine")
    print("=" * 50)
    
    # Test each persona with enhanced flow
    personas_to_test = ["eager_junior", "experienced_senior", "career_changer"]
    
    for persona_id in personas_to_test:
        print(f"\n>> Testing enhanced flow for {persona_id}:")
        
        try:
            # Create enhanced components
            user = EnhancedSimulatedUser(persona_id)
            agent = EnhancedSmartMockAgent("EnhancedAgent")
            
            # Test personalized greeting
            greeting = agent.get_personalized_greeting(persona_id)
            print(f"   Greeting: {greeting[:100]}...")
            
            # Test enhanced first response
            first_response = user.generate_response(greeting, {'conversation_log': []})
            print(f"   First Response: {first_response[:100]}...")
            
            # Test agent processing
            agent_response, decision, reasoning = agent.process_message(
                first_response, f"test_{persona_id}", conversation_length=1, persona_id=persona_id
            )
            print(f"   Agent Decision: {decision}")
            print(f"   Decision Quality: {'GOOD' if decision != 'END' else 'NEEDS_WORK'}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print(f"\n>> Enhanced simulation engine ready for testing!")


if __name__ == "__main__":
    main()