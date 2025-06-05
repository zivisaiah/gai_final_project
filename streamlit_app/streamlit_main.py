"""
Main Streamlit Application
Recruitment Chatbot with Core Agent, Scheduling Advisor, and Exit Advisor Integration
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import logging
from dotenv import load_dotenv
import traceback

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import our components
from streamlit_app.components.chat_interface import ChatInterface, create_chat_interface
from app.modules.agents.core_agent import CoreAgent, AgentDecision
from app.modules.agents.scheduling_advisor import SchedulingAdvisor, SchedulingDecision
from app.modules.utils.conversation import ConversationContext
from config.phase1_settings import get_settings

# Load environment variables
load_dotenv()

class RecruitmentChatbot:
    """Main recruitment chatbot application."""
    
    def __init__(self):
        """Initialize the chatbot with all components."""
        self.settings = get_settings()
        self.setup_logging()
        
        # Initialize agents only once using session state
        if 'agents_initialized' not in st.session_state:
            self.initialize_agents()
            st.session_state.agents_initialized = True
            st.session_state.core_agent = self.core_agent
            st.session_state.scheduling_advisor = self.scheduling_advisor
            st.session_state.conversation_context = self.conversation_context
        else:
            # Reuse existing agents from session state
            self.core_agent = st.session_state.core_agent
            self.scheduling_advisor = st.session_state.scheduling_advisor
            self.conversation_context = st.session_state.conversation_context
            
        self.chat_interface = create_chat_interface()
    
    def setup_logging(self):
        """Set up logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def initialize_agents(self):
        """Initialize the AI agents."""
        try:
            # Check if OpenAI API key is available
            if not self.settings.OPENAI_API_KEY:
                st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your environment.")
                st.stop()
            
            # Initialize Core Agent
            self.core_agent = CoreAgent(
                openai_api_key=self.settings.OPENAI_API_KEY,
                model_name=self.settings.OPENAI_MODEL
            )
            
            # Initialize Scheduling Advisor
            self.scheduling_advisor = SchedulingAdvisor(
                openai_api_key=self.settings.OPENAI_API_KEY,
                model_name=self.settings.OPENAI_MODEL
            )
            
            # Exit Advisor is now handled entirely within Core Agent (clean MVC architecture)
            
            # Initialize Conversation Context
            self.conversation_context = ConversationContext()
            
            self.logger.info("All agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
            st.error(f"❌ Error initializing AI agents: {e}")
            st.stop()
    
    def process_user_message(self, user_message: str) -> Dict:
        """Process user message through the agent system."""
        try:
            # CLEAN MVC ARCHITECTURE: Only call Core Agent (Controller)
            # Core Agent handles ALL business logic including exit decisions
            self.logger.info(f"CALLING CORE AGENT with user_message='{user_message}'")
            
            agent_response, decision, reasoning = self.core_agent.process_message(
                user_message,
                conversation_id="streamlit_session"
            )
            
            # Update candidate info from conversation state
            conversation_state = self.core_agent.get_or_create_conversation("streamlit_session")
            if conversation_state.candidate_info:
                self.chat_interface.update_candidate_info(conversation_state.candidate_info)
            
            response_metadata = {
                'decision': decision.value,
                'reasoning': reasoning,
                'agent_type': 'core_agent'
            }
            
            # Handle scheduling if needed
            if decision == AgentDecision.SCHEDULE:
                # Get conversation messages for scheduling
                conversation_messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in conversation_state.messages
                ]
                
                # Get candidate info to pass to scheduling advisor
                candidate_info = conversation_state.candidate_info
                
                # Since Core Agent decided to SCHEDULE, get available slots directly
                scheduling_result = self.get_available_slots_for_scheduling(
                    candidate_info,
                    user_message
                )
                response_metadata.update(scheduling_result)
            
            return {
                'response': agent_response,
                'metadata': response_metadata,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Error processing user message: {e}")
            print(traceback.format_exc())
            if st.sidebar.checkbox("Show Error Details", value=True):
                st.sidebar.error(f"Exception: {e}")
                st.sidebar.code(traceback.format_exc())
            return {
                'response': "I apologize, but I encountered an error processing your message. Please try again.",
                'metadata': {'error': str(e), 'agent_type': 'error'},
                'success': False
            }
    
    def get_available_slots_for_scheduling(self, candidate_info: Dict, user_message: str) -> Dict:
        """Get available slots when Core Agent has decided to schedule."""
        try:
            # Parse time preferences from user message
            time_prefs = self.scheduling_advisor.parse_candidate_time_preference(user_message)
            
            # Get available slots based on preferences
            from datetime import datetime
            available_slots = self.scheduling_advisor._get_available_slots(
                time_prefs.get('preferred_datetimes', []),
                datetime.now(),
                14  # 14 days ahead
            )
            
            scheduling_metadata = {
                'scheduling_decision': 'SCHEDULE',
                'scheduling_reasoning': 'Core Agent decided to schedule based on conversation flow',
                'suggested_slots': available_slots[:3]  # Top 3 slots
            }
            
            # Update scheduling context
            if available_slots:
                self.chat_interface.update_scheduling_context({
                    'slots_offered': available_slots[:3]
                })
            
            return scheduling_metadata
            
        except Exception as e:
            self.logger.error(f"Error getting available slots: {e}")
            return {
                'scheduling_error': str(e),
                'suggested_slots': []
            }
    
    def handle_scheduling_decision(self, conversation_messages: List[Dict], user_message: str) -> Dict:
        """Handle scheduling through the Scheduling Advisor."""
        try:
            # Get candidate info from session state
            candidate_info = st.session_state.candidate_info
            
            # Make scheduling decision
            scheduling_decision, reasoning, suggested_slots, scheduling_response = \
                self.scheduling_advisor.make_scheduling_decision(
                    candidate_info,
                    conversation_messages,
                    user_message
                )
            
            scheduling_metadata = {
                'scheduling_decision': scheduling_decision.value,
                'scheduling_reasoning': reasoning,
                'suggested_slots': suggested_slots
            }
            
            # Update scheduling context
            if suggested_slots:
                self.chat_interface.update_scheduling_context({
                    'slots_offered': suggested_slots
                })
            
            return scheduling_metadata
            
        except Exception as e:
            self.logger.error(f"Error in scheduling decision: {e}")
            return {
                'scheduling_error': str(e),
                'suggested_slots': []
            }
    
    def handle_slot_selection(self, selected_slot: Dict) -> Dict:
        """Handle when user selects a time slot for booking."""
        try:
            # Get candidate info
            candidate_info = st.session_state.candidate_info
            
            # Book the appointment
            slot_datetime = datetime.fromisoformat(selected_slot['datetime'].replace('Z', '+00:00'))
            recruiter_id = selected_slot.get('recruiter_id', 1)
            
            booking_result = self.scheduling_advisor.book_appointment(
                candidate_info,
                slot_datetime,
                recruiter_id,
                45  # 45 minutes duration
            )
            
            if booking_result['success']:
                # Update scheduling context
                self.chat_interface.update_scheduling_context({
                    'appointment_confirmed': True,
                    'selected_slot': selected_slot
                })
                
                # Update conversation stage
                self.chat_interface.update_conversation_stage('completed')
                
                return {
                    'appointment_confirmed': True,
                    'appointment_details': {
                        'datetime': slot_datetime.strftime("%A, %B %d, %Y at %I:%M %p"),
                        'recruiter': booking_result.get('recruiter', {}).get('name', 'Our recruiter'),
                        'duration': 45,
                        'appointment_id': booking_result.get('appointment_id')
                    },
                    'confirmation_message': booking_result.get('confirmation_message', '')
                }
            else:
                return {
                    'appointment_error': booking_result.get('error', 'Unknown error'),
                    'appointment_confirmed': False
                }
                
        except Exception as e:
            self.logger.error(f"Error booking appointment: {e}")
            return {
                'appointment_error': str(e),
                'appointment_confirmed': False
            }
    
    def display_system_status(self):
        """Display system status in the sidebar."""
        with st.sidebar:
            st.subheader("🔧 System Status")
            
            # Agent status
            st.write("**Core Agent:** ✅ Ready")
            st.write("**Scheduling Advisor:** ✅ Ready")
            st.write("**Exit Advisor:** ✅ Ready")
            
            # Database status
            try:
                stats = self.scheduling_advisor.get_scheduling_statistics()
                st.write("**Database:** ✅ Connected")
                st.write(f"**Available Slots:** {stats.get('available_slots', 0)}")
                st.write(f"**Recruiters:** {stats.get('recruiter_count', 0)}")
            except Exception as e:
                st.write("**Database:** ❌ Error")
                st.write(f"Error: {str(e)[:50]}...")
            
            # API status
            if self.settings.OPENAI_API_KEY:
                st.write("**OpenAI API:** ✅ Configured")
                st.write(f"**Model:** {self.settings.OPENAI_MODEL}")
            else:
                st.write("**OpenAI API:** ❌ Not configured")
    
    def display_debug_info(self):
        """Display debug information if enabled."""
        if st.sidebar.checkbox("🐛 Debug Mode", value=False):
            with st.sidebar:
                st.subheader("🔍 Debug Info")
                
                # Conversation state
                if hasattr(self.core_agent, 'conversation_state'):
                    state = self.core_agent.conversation_state
                    st.write(f"**Messages:** {len(state.messages)}")
                    st.write(f"**Candidate Info:** {len([k for k, v in state.candidate_info.items() if v])}/5")
                
                # Session state
                st.write("**Session State Keys:**")
                for key in st.session_state.keys():
                    st.write(f"• {key}")
                
                # Settings
                with st.expander("⚙️ Settings"):
                    st.write(f"**Model:** {self.settings.OPENAI_MODEL}")
                    st.write(f"**Temperature:** {self.settings.OPENAI_TEMPERATURE}")
                    st.write(f"**Max Tokens:** {self.settings.OPENAI_MAX_TOKENS}")
    
    def run(self):
        """Run the main Streamlit application."""
        
        # Configure Streamlit page
        st.set_page_config(
            page_title="Python Developer Recruitment Assistant",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Display system status
        self.display_system_status()
        
        # Display debug info if enabled
        self.display_debug_info()
        
        # Render chat interface
        user_input = self.chat_interface.render()
        
        # Process user input if provided
        if user_input:
            # Check if this is a slot selection
            if (st.session_state.scheduling_context.get('selected_slot') and 
                not st.session_state.scheduling_context.get('appointment_confirmed')):
                
                # Handle slot selection
                selected_slot = st.session_state.scheduling_context['selected_slot']
                booking_result = self.handle_slot_selection(selected_slot)
                
                # Add confirmation message
                if booking_result.get('appointment_confirmed'):
                    confirmation_msg = booking_result.get('confirmation_message', 
                                                        'Your interview has been scheduled successfully!')
                    self.chat_interface.add_assistant_message(
                        confirmation_msg,
                        booking_result
                    )
                else:
                    error_msg = f"Sorry, there was an error booking your appointment: {booking_result.get('appointment_error', 'Unknown error')}"
                    self.chat_interface.add_assistant_message(error_msg)
                
                # Clear the selected slot
                st.session_state.scheduling_context['selected_slot'] = None
                st.rerun()
            
            else:
                # Process regular user message
                with st.spinner("🤖 Thinking..."):
                    result = self.process_user_message(user_input)
                
                # Add assistant response
                self.chat_interface.add_assistant_message(
                    result['response'],
                    result['metadata']
                )
                
                # Update conversation stage based on decision
                if result['metadata'].get('decision') == 'SCHEDULE':
                    self.chat_interface.update_conversation_stage('scheduling')
                elif result['metadata'].get('appointment_confirmed'):
                    self.chat_interface.update_conversation_stage('completed')
                elif result['metadata'].get('decision') == 'EXIT':
                    self.chat_interface.update_conversation_stage('ended')
                
                # Rerun to display new message
                st.rerun()


def main():
    """Main entry point for the Streamlit application."""
    try:
        # Create and run the chatbot
        chatbot = RecruitmentChatbot()
        chatbot.run()
        
    except Exception as e:
        st.error(f"❌ Application Error: {e}")
        st.write("Please check your configuration and try again.")
        
        # Display error details in debug mode
        if st.checkbox("Show Error Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main() 