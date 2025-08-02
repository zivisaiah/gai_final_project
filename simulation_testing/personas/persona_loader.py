"""
Persona Loading and Management System
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Any

class PersonaLoader:
    """Loads and manages persona configurations"""
    
    def __init__(self, personas_dir: Optional[Path] = None):
        if personas_dir is None:
            personas_dir = Path(__file__).parent
        self.personas_dir = personas_dir
        self.personas = {}
        self.load_all_personas()
    
    def load_all_personas(self):
        """Load all persona JSON files"""
        print(">> Loading personas...")
        
        for persona_file in self.personas_dir.glob("*.json"):
            if persona_file.name != "persona_loader.py":
                try:
                    with open(persona_file, 'r', encoding='utf-8') as f:
                        persona_data = json.load(f)
                        persona_id = persona_data.get('id')
                        if persona_id:
                            self.personas[persona_id] = persona_data
                            print(f"   OK Loaded: {persona_data.get('name', persona_id)} ({persona_data.get('type', 'Unknown')})")
                        else:
                            print(f"   X Invalid persona file (no ID): {persona_file.name}")
                except Exception as e:
                    print(f"   X Error loading {persona_file.name}: {e}")
        
        print(f">> Total personas loaded: {len(self.personas)}\n")
    
    def get_persona(self, persona_id: str) -> Optional[Dict]:
        """Get a specific persona by ID"""
        return self.personas.get(persona_id)
    
    def get_available_personas(self) -> List[str]:
        """Get list of available persona IDs"""
        return list(self.personas.keys())
    
    def get_random_persona(self) -> Dict:
        """Get a random persona"""
        persona_id = random.choice(list(self.personas.keys()))
        return self.personas[persona_id]
    
    def get_persona_response(self, persona_id: str, response_type: str, context: Optional[Dict] = None) -> str:
        """Get a contextual response from a persona"""
        persona = self.get_persona(persona_id)
        if not persona:
            return f"I'm {persona_id}."
        
        conversation_patterns = persona.get('conversation_patterns', {})
        
        # Get responses for the specified type
        responses = conversation_patterns.get(response_type, [])
        
        if not responses:
            # Fallback to typical responses for passive candidates
            if persona.get('type') == 'Passive Candidate':
                responses = conversation_patterns.get('typical_responses', ['OK.'])
            else:
                responses = [f"I'm {persona.get('name', 'a candidate')}."]
        
        # Select response based on persona characteristics
        if isinstance(responses, list) and responses:
            if persona.get('characteristics', {}).get('response_length') == 'short':
                # Prefer shorter responses
                return min(responses, key=len)
            else:
                # Random selection for varied responses
                return random.choice(responses)
        
        return str(responses) if responses else "I'm here for the interview."
    
    def should_ask_question(self, persona_id: str, conversation_length: int) -> bool:
        """Determine if persona should ask a question based on their characteristics"""
        persona = self.get_persona(persona_id)
        if not persona:
            return False
        
        characteristics = persona.get('characteristics', {})
        question_frequency = characteristics.get('question_frequency', 'medium')
        
        # Base probability of asking questions
        probabilities = {
            'high': 0.7,
            'medium': 0.4,
            'low': 0.1
        }
        
        base_prob = probabilities.get(question_frequency, 0.4)
        
        # Adjust based on conversation length (less likely to ask as conversation progresses)
        adjusted_prob = base_prob * max(0.2, 1 - (conversation_length * 0.1))
        
        return random.random() < adjusted_prob
    
    def get_persona_question(self, persona_id: str) -> Optional[str]:
        """Get a question from the persona"""
        persona = self.get_persona(persona_id)
        if not persona:
            return None
        
        questions = persona.get('conversation_patterns', {}).get('question_examples', [])
        if questions:
            return random.choice(questions)
        
        return None
    
    def get_decision_likelihood(self, persona_id: str, agent_decision: str, context: Dict) -> float:
        """Get likelihood of persona accepting an agent decision"""
        persona = self.get_persona(persona_id)
        if not persona:
            return 0.5  # neutral likelihood
        
        decision_triggers = persona.get('decision_triggers', {})
        
        if agent_decision.upper() == 'SCHEDULE':
            triggers = decision_triggers.get('likely_to_schedule', [])
            # Check if any positive triggers are in the context
            positive_signals = sum(1 for trigger in triggers if trigger.lower() in str(context).lower())
            return min(0.9, 0.3 + (positive_signals * 0.2))
        
        elif agent_decision.upper() == 'END':
            unlikely_triggers = decision_triggers.get('unlikely_to_end_early', [])
            negative_signals = sum(1 for trigger in unlikely_triggers if trigger.lower() in str(context).lower())
            return max(0.1, 0.7 - (negative_signals * 0.2))
        
        elif agent_decision.upper() == 'CONTINUE':
            triggers = decision_triggers.get('likely_to_continue', [])
            positive_signals = sum(1 for trigger in triggers if trigger.lower() in str(context).lower())
            return min(0.9, 0.5 + (positive_signals * 0.15))
        
        return 0.5  # default neutral likelihood

# Global persona loader instance
persona_loader = PersonaLoader()