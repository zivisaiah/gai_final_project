"""
Main Simulation Engine
Automated Python simulation framework for user conversation testing
"""

import sys
import time
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import simulation components
from simulation_testing.config.test_config import config
from simulation_testing.personas.persona_loader import persona_loader
from simulation_testing.metrics.metrics_collector import metrics_collector

# Import application components (with error handling for missing dependencies)
try:
    from app.modules.agents.core_agent import CoreAgent, AgentDecision
    from app.modules.agents.scheduling_advisor import SchedulingAdvisor
    from app.modules.utils.conversation import ConversationContext
    APPLICATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import application components: {e}")
    print("   Running in mock mode for framework testing")
    APPLICATION_AVAILABLE = False

class SimulatedUser:
    """Simulates a user with a specific persona"""
    
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.persona = persona_loader.get_persona(persona_id)
        self.conversation_history = []
        self.message_count = 0
        
        if not self.persona:
            raise ValueError(f"Persona not found: {persona_id}")
    
    def generate_response(self, agent_message: str, context: Dict) -> str:
        """Generate a response based on persona characteristics"""
        self.message_count += 1
        
        # Determine response type based on context and conversation flow
        if self.message_count == 1:
            # First response - greeting
            response = persona_loader.get_persona_response(
                self.persona_id, 'greeting_responses', context
            )
        elif 'experience' in agent_message.lower() or 'background' in agent_message.lower():
            # Experience-related question
            response = persona_loader.get_persona_response(
                self.persona_id, 'experience_responses', context
            )
        elif 'why' in agent_message.lower() or 'motivation' in agent_message.lower():
            # Motivation question
            response = persona_loader.get_persona_response(
                self.persona_id, 'motivation_responses', context
            )
        else:
            # General response
            if self.persona.get('type') == 'Passive Candidate':
                response = persona_loader.get_persona_response(
                    self.persona_id, 'typical_responses', context
                )
                
                # Sometimes provide more info when prompted
                if random.random() < 0.3:  # 30% chance
                    response = persona_loader.get_persona_response(
                        self.persona_id, 'when_prompted_responses', context
                    )
            elif self.persona.get('type') == 'Difficult Candidate':
                # Mix of evasive and challenging responses
                if random.random() < 0.4:
                    response = persona_loader.get_persona_response(
                        self.persona_id, 'evasive_responses', context
                    )
                elif random.random() < 0.3:
                    response = persona_loader.get_persona_response(
                        self.persona_id, 'challenging_responses', context
                    )
                else:
                    response = "I guess that's fine."
            else:
                # Default response for other personas
                response = f"That sounds good. I'm interested in learning more."
        
        # Add questions if persona tends to ask them
        if persona_loader.should_ask_question(self.persona_id, self.message_count):
            question = persona_loader.get_persona_question(self.persona_id)
            if question:
                response += f" {question}"
        
        self.conversation_history.append({
            'type': 'user',
            'message': response,
            'timestamp': time.time()
        })
        
        return response
    
    def should_accept_scheduling(self, context: Dict) -> bool:
        """Determine if user would accept scheduling based on persona"""
        likelihood = persona_loader.get_decision_likelihood(
            self.persona_id, 'SCHEDULE', context
        )
        return random.random() < likelihood
    
    def should_continue_conversation(self, context: Dict) -> bool:
        """Determine if user wants to continue conversation"""
        likelihood = persona_loader.get_decision_likelihood(
            self.persona_id, 'CONTINUE', context
        )
        return random.random() < likelihood

class MockAgent:
    """Mock agent for testing when application is not available"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.decisions = ['CONTINUE', 'SCHEDULE', 'INFO', 'END']
    
    def process_message(self, message: str, conversation_id: str = None) -> Tuple[str, str, str]:
        """Mock agent processing"""
        time.sleep(random.uniform(0.5, 2.0))  # Simulate processing time
        
        decision = random.choice(self.decisions)
        reasoning = f"Mock {self.agent_type} decision based on message length and content"
        
        responses = {
            'CONTINUE': "Tell me more about your experience with Python development.",
            'SCHEDULE': "Based on our conversation, I'd like to schedule an interview. Are you available this week?",
            'INFO': "Here's some information about our Python development role...",
            'END': "Thank you for your time. We'll be in touch soon."
        }
        
        response = responses.get(decision, "Thank you for that information.")
        
        return response, decision, reasoning

class ConversationSimulator:
    """Simulates complete conversations between users and agents"""
    
    def __init__(self):
        self.setup_logging()
        self.agents = {}
        self.initialize_agents()
    
    def setup_logging(self):
        """Set up logging for simulation"""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler() if config.CONSOLE_OUTPUT else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_agents(self):
        """Initialize agents (real or mock)"""
        if APPLICATION_AVAILABLE and config.OPENAI_API_KEY:
            try:
                self.agents['core'] = CoreAgent(
                    openai_api_key=config.OPENAI_API_KEY,
                    model_name=config.OPENAI_MODEL
                )
                self.logger.info("OK Real Core Agent initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize real agent: {e}")
                self.agents['core'] = MockAgent('CoreAgent')
                self.logger.info(">> Mock Core Agent initialized")
        else:
            self.agents['core'] = MockAgent('CoreAgent')
            self.logger.info(">> Mock Core Agent initialized (no API key or app unavailable)")
    
    def simulate_conversation(self, persona_id: str, max_turns: int = 10) -> Dict:
        """Simulate a complete conversation"""
        conversation_id = f"sim_{persona_id}_{int(time.time())}"
        
        # Start metrics collection
        persona = persona_loader.get_persona(persona_id)
        persona_type = persona.get('type', 'Unknown') if persona else 'Unknown'
        
        conv_metrics = metrics_collector.start_conversation(
            conversation_id, persona_id, persona_type
        )
        
        self.logger.info(f">> Starting conversation simulation: {conversation_id}")
        self.logger.info(f"   Persona: {persona.get('name', persona_id)} ({persona_type})")
        
        # Initialize simulated user
        try:
            user = SimulatedUser(persona_id)
        except ValueError as e:
            metrics_collector.record_error(conversation_id, str(e))
            metrics_collector.complete_conversation(conversation_id, False, "failed")
            return {"error": str(e)}
        
        # Conversation state
        conversation_log = []
        agent = self.agents['core']
        context = {"conversation_log": conversation_log}
        
        # Start conversation
        if config.CONSOLE_OUTPUT:
            print(f"\n{'='*60}")
            print(f">> CONVERSATION SIMULATION: {persona.get('name', persona_id)}")
            print(f"   Type: {persona_type}")
            print(f"   ID: {conversation_id}")
            print(f"{'='*60}")
        
        success = False
        completion_stage = "chatting"
        
        try:
            # Initial agent greeting
            agent_message = "Hello! Thank you for your interest in our Python developer position. Could you tell me a bit about yourself and your experience?"
            
            if config.CONSOLE_OUTPUT:
                print(f"\nAGENT: {agent_message}")
            
            conversation_log.append({
                'type': 'agent',
                'message': agent_message,
                'timestamp': time.time()
            })
            
            for turn in range(max_turns):
                metrics_collector.increment_message_count(conversation_id)
                
                # User response
                start_time = time.time()
                user_message = user.generate_response(agent_message, context)
                
                if config.CONSOLE_OUTPUT:
                    print(f"\nUSER ({persona.get('name', 'User')}): {user_message}")
                
                conversation_log.append({
                    'type': 'user',
                    'message': user_message,
                    'timestamp': time.time()
                })
                
                # Agent processing
                agent_start_time = time.time()
                
                if APPLICATION_AVAILABLE and hasattr(agent, 'process_message'):
                    agent_response, decision, reasoning = agent.process_message(
                        user_message, conversation_id
                    )
                else:
                    agent_response, decision, reasoning = agent.process_message(user_message)
                
                agent_response_time = time.time() - agent_start_time
                
                # Record metrics
                metrics_collector.record_agent_decision(
                    conversation_id, decision, reasoning, agent_response_time
                )
                
                if config.CONSOLE_OUTPUT:
                    print(f"\nAGENT: {agent_response}")
                    print(f"   [Decision: {decision}, Time: {agent_response_time:.2f}s]")
                
                conversation_log.append({
                    'type': 'agent',
                    'message': agent_response,
                    'decision': decision,
                    'reasoning': reasoning,
                    'response_time': agent_response_time,
                    'timestamp': time.time()
                })
                
                # Handle agent decisions
                if decision == 'SCHEDULE':
                    completion_stage = "scheduling"
                    if user.should_accept_scheduling(context):
                        success = True
                        completion_stage = "completed"
                        if config.CONSOLE_OUTPUT:
                            print(f"\nOK {persona.get('name')}: Yes, I'd like to schedule an interview!")
                        break
                    else:
                        if config.CONSOLE_OUTPUT:
                            print(f"\nX {persona.get('name')}: I need to think about it more.")
                        completion_stage = "scheduling_declined"
                
                elif decision == 'END':
                    completion_stage = "ended"
                    success = True  # Completed conversation successfully
                    break
                
                elif decision == 'INFO':
                    # Continue conversation after providing information
                    pass
                
                # Check if user wants to continue
                if not user.should_continue_conversation(context):
                    completion_stage = "user_ended"
                    break
                
                # Prepare for next turn
                agent_message = agent_response
                
                # Add delay between messages
                if config.DEFAULT_DELAY_BETWEEN_MESSAGES > 0:
                    time.sleep(config.DEFAULT_DELAY_BETWEEN_MESSAGES)
            
            else:
                # Max turns reached
                completion_stage = "max_turns_reached"
            
        except Exception as e:
            self.logger.error(f"Error in conversation simulation: {e}")
            metrics_collector.record_error(conversation_id, str(e))
            completion_stage = "error"
        
        # Complete metrics collection
        metrics_collector.complete_conversation(conversation_id, success, completion_stage)
        
        if config.CONSOLE_OUTPUT:
            print(f"\n>> Conversation ended: {completion_stage}")
            print(f"   Success: {'OK' if success else 'FAILED'}")
            print(f"   Duration: {conv_metrics.get_duration():.1f}s")
            print(f"   Messages: {conv_metrics.total_messages}")
            print(f"{'='*60}\n")
        
        return {
            "conversation_id": conversation_id,
            "persona_id": persona_id,
            "persona_type": persona_type,
            "success": success,
            "completion_stage": completion_stage,
            "duration": conv_metrics.get_duration(),
            "total_messages": conv_metrics.total_messages,
            "conversation_log": conversation_log if config.SAVE_CONVERSATION_TRANSCRIPTS else None
        }
    
    def run_simulation_batch(self, personas: List[str], conversations_per_persona: int = 1) -> Dict:
        """Run a batch of conversations for multiple personas"""
        self.logger.info(f">> Starting simulation batch: {len(personas)} personas, {conversations_per_persona} conversations each")
        
        if config.CONSOLE_OUTPUT:
            print(f"\n>> STARTING SIMULATION BATCH")
            print(f"   Personas: {len(personas)}")
            print(f"   Conversations per persona: {conversations_per_persona}")
            print(f"   Total conversations: {len(personas) * conversations_per_persona}")
            print()
        
        results = []
        
        for persona_id in personas:
            for i in range(conversations_per_persona):
                if config.CONSOLE_OUTPUT:
                    print(f">> Running conversation {i+1}/{conversations_per_persona} for {persona_id}...")
                
                result = self.simulate_conversation(persona_id)
                results.append(result)
                
                # Brief pause between conversations
                time.sleep(1)
        
        # Generate and display summary
        if config.CONSOLE_OUTPUT:
            metrics_collector.print_summary()
        
        # Save detailed results
        results_file = metrics_collector.save_results()
        
        return {
            "total_conversations": len(results),
            "results": results,
            "results_file": str(results_file)
        }

def main():
    """Main simulation entry point"""
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        print("X Configuration issues found:")
        for issue in config_issues:
            print(f"   - {issue}")
        return
    
    config.print_config_summary()
    
    # Initialize simulator
    simulator = ConversationSimulator()
    
    # Get available personas
    available_personas = persona_loader.get_available_personas()
    
    if not available_personas:
        print("X No personas found! Please check personas directory.")
        return
    
    print(f">> Available personas: {available_personas}")
    
    # Run simulation with all personas
    results = simulator.run_simulation_batch(available_personas, conversations_per_persona=1)
    
    print(f"\n>> Simulation completed!")
    print(f"   Total conversations: {results['total_conversations']}")
    print(f"   Results saved to: {results['results_file']}")

if __name__ == "__main__":
    main()