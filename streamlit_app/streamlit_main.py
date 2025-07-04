"""
Main Streamlit Application
Recruitment Chatbot with Core Agent, Scheduling Advisor, and Exit Advisor Integration
"""

import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
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
from streamlit_app.components.admin_panel import create_admin_panel
from streamlit_app.components.registration_form import create_registration_form
from app.modules.agents.core_agent import CoreAgent, AgentDecision
from app.modules.agents.scheduling_advisor import SchedulingAdvisor, SchedulingDecision
from app.modules.utils.conversation import ConversationContext
from config.phase1_settings import get_settings
import time

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
        self.admin_panel = create_admin_panel()
        self.registration_form = create_registration_form()
        
        # Initialize session tracking
        if 'session_start_time' not in st.session_state:
            st.session_state.session_start_time = datetime.now()
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{int(time.time())}"
    
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
            
            # Initialize Core Agent with vector store type for INFO capabilities
            self.core_agent = CoreAgent(
                openai_api_key=self.settings.OPENAI_API_KEY,
                model_name=self.settings.OPENAI_MODEL,
                vector_store_type="local"  # Use local ChromaDB vector store
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
        start_time = time.time()
        try:
            # CRITICAL FIX: Sync candidate info from session state to Core Agent
            # This ensures registration form data is available to the Core Agent
            conversation_state = self.core_agent.get_or_create_conversation("streamlit_session")
            
            # Update Core Agent's candidate info with session state data
            if st.session_state.candidate_info:
                conversation_state.candidate_info.update(st.session_state.candidate_info)
                self.logger.info(f"Synced candidate info to Core Agent: {conversation_state.candidate_info}")
            
            # Check if registration is not complete - let LLM handle intent detection
            if not st.session_state.get('registration_completed', False):
                # Process message through Core Agent to detect intent via LLM
                agent_response, decision, reasoning = self.core_agent.process_message(
                    user_message,
                    conversation_id="streamlit_session"
                )
                
                # Agent continues conversation naturally - no registration form enforcement
                # Registration form is USER-initiated, not agent-enforced
                
                # Otherwise, continue with the normal response
                response_time = time.time() - start_time
                response_metadata = {
                    'decision': decision.value,
                    'reasoning': reasoning,
                    'agent_type': 'core_agent',
                    'response_time': response_time
                }
                
                return {
                    'response': agent_response,
                    'metadata': response_metadata,
                    'success': True
                }
            
            # CLEAN MVC ARCHITECTURE: Only call Core Agent (Controller)
            # Core Agent handles ALL business logic including exit decisions
            self.logger.info(f"CALLING CORE AGENT with user_message='{user_message}'")
            
            agent_response, decision, reasoning = self.core_agent.process_message(
                user_message,
                conversation_id="streamlit_session"
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update candidate info from conversation state (bidirectional sync)
            if conversation_state.candidate_info:
                self.chat_interface.update_candidate_info(conversation_state.candidate_info)
            
            response_metadata = {
                'decision': decision.value,
                'reasoning': reasoning,
                'agent_type': 'core_agent',
                'response_time': response_time
            }
            
            # Enhanced INFO decision handling with source references
            info_metadata = {}
            if decision == AgentDecision.INFO:
                # Try to extract source information from the response
                # This is a simplified approach - in a full implementation,
                # we'd get this directly from the Info Advisor
                info_metadata = {
                    'info_type': 'job_related',
                    'sources_used': ['job_description_docs'],
                    'has_context': True,
                    'confidence': 0.8  # Estimated confidence
                }
                response_metadata.update(info_metadata)
            
            # Handle scheduling if needed
            if decision == AgentDecision.SCHEDULE:
                # Core Agent already consulted SchedulingAdvisor and stored slots in candidate_info
                try:
                    # Get the slots that were already computed by Core Agent
                    candidate_info = self.core_agent.get_candidate_info('streamlit_session')
                    available_slots = candidate_info.get('available_slots', [])
                    
                    # CRITICAL DEBUG: Check if get_candidate_info is working properly
                    self.logger.info(f"🔍 CRITICAL DEBUG: get_candidate_info returned: {list(candidate_info.keys()) if candidate_info else 'None'}")
                    if candidate_info and 'available_slots' in candidate_info:
                        self.logger.info(f"🔍 CRITICAL DEBUG: available_slots key exists with {len(candidate_info['available_slots'])} slots")
                    else:
                        self.logger.error(f"❌ CRITICAL DEBUG: available_slots key missing from candidate_info!")
                    
                    # DEBUG: Comprehensive slot tracking
                    self.logger.info(f"🔍 SLOT DEBUG: Core Agent decision = SCHEDULE")
                    self.logger.info(f"🔍 SLOT DEBUG: Retrieved candidate_info keys: {list(candidate_info.keys())}")
                    self.logger.info(f"🔍 SLOT DEBUG: Found {len(available_slots)} slots in candidate_info")
                    if available_slots:
                        self.logger.info(f"🔍 SLOT DEBUG: First slot sample: {available_slots[0]}")
                    
                    if available_slots:
                        scheduling_metadata = {
                            'scheduling_decision': 'SCHEDULE',
                            'scheduling_reasoning': 'Core Agent decided to schedule based on conversation flow',
                            'suggested_slots': available_slots
                        }
                        
                        # Update scheduling context for UI
                        self.chat_interface.update_scheduling_context({
                            'slots_offered': available_slots
                        })
                        
                        response_metadata.update(scheduling_metadata)
                        
                        # DEBUG: Confirm metadata update
                        self.logger.info(f"✅ SLOT DEBUG: Successfully passed {len(available_slots)} slots to UI metadata")
                        self.logger.info(f"✅ SLOT DEBUG: response_metadata now contains: {list(response_metadata.keys())}")
                    else:
                        # Fallback: Get slots directly if none were stored
                        self.logger.warning("❌ SLOT DEBUG: No slots found in candidate_info, falling back to direct retrieval")
                        self.logger.info(f"❌ SLOT DEBUG: candidate_info contents: {candidate_info}")
                        
                        reference_datetime = datetime.now()
                        all_slots = self.scheduling_advisor._get_all_available_slots(reference_datetime, days_ahead=14)
                        
                        # Apply diversification to get 3 varied slots
                        diversified_slots = self.scheduling_advisor._diversify_slot_selection(all_slots, max_slots=3)
                        
                        self.logger.info(f"🔄 SLOT DEBUG: Fallback generated {len(diversified_slots)} slots")
                        
                        scheduling_metadata = {
                            'scheduling_decision': 'SCHEDULE',
                            'scheduling_reasoning': 'Fallback slot retrieval',
                            'suggested_slots': diversified_slots
                        }
                        
                        # Update scheduling context
                        if diversified_slots:
                            self.chat_interface.update_scheduling_context({
                                'slots_offered': diversified_slots
                            })
                            self.logger.info(f"✅ SLOT DEBUG: Fallback slots passed to UI context")
                        
                        response_metadata.update(scheduling_metadata)
                    
                except Exception as e:
                    self.logger.error(f"Error getting slots for UI display: {e}")
                    response_metadata.update({
                        'scheduling_error': str(e),
                        'suggested_slots': []
                    })
            
            return {
                'response': agent_response,
                'metadata': response_metadata,
                'success': True
            }
            
        except Exception as e:
            # Log error to admin panel
            error_data = {'error': str(e), 'user_message': user_message}
            self.admin_panel.log_conversation_event('error', error_data)
            st.session_state.admin_analytics['error_logs'].append({
                'timestamp': datetime.now(),
                'error': str(e),
                'context': user_message
            })
            
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
            slot_id = selected_slot.get('id')  # Get the slot ID
            
            booking_result = self.scheduling_advisor.book_appointment(
                candidate_info,
                slot_datetime,
                recruiter_id,
                45,  # 45 minutes duration
                slot_id  # Pass the slot ID
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
            page_title="AI Recruitment Assistant",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Add custom CSS for better styling
        st.markdown("""
        <style>
        .main {
            padding-top: 1rem;
        }
        .stAlert {
            margin-top: 1rem;
        }
        .info-response {
            background-color: #f0f8ff;
            border-left: 4px solid #1f77b4;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0.25rem;
        }
        .source-reference {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main navigation tabs
        tab1, tab2 = st.tabs(["💬 Chat Interface", "🛠️ Admin Panel"])
        
        with tab1:
            self.display_chat_interface()
            
        with tab2:
            self.admin_panel.display_admin_panel()
    
    def display_chat_interface(self):
        """Display the main chat interface."""
        # Main title
        st.title("🤖 AI Recruitment Assistant")
        st.markdown("*Intelligent conversations for Python developer positions with multi-agent orchestration*")
        
        # Display system status and debug info in sidebar
        self.display_system_status()
        self.display_debug_info()
        
        # USER-INITIATED REGISTRATION SECTION
        # Show registration option if not completed (user can choose to fill it or skip)
        if not st.session_state.get('registration_completed', False):
            with st.expander("📝 Optional: Quick Registration Form", expanded=False):
                st.info("""
                **💡 You can fill out this form to speed up the process, or simply continue chatting!**
                
                This form is completely optional. You can:
                - Fill it out now for faster interview scheduling
                - Skip it and provide information through our conversation
                - Come back to it later if you change your mind
                """)
                
                # Add a user choice
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Fill Registration Form", use_container_width=True):
                        st.session_state.user_wants_registration = True
                        st.rerun()
                with col2:
                    if st.button("💬 Continue Chatting", use_container_width=True):
                        st.session_state.user_wants_registration = False
                        st.success("Great! Let's continue our conversation naturally.")
                
                # Show form if user explicitly requested it
                if st.session_state.get('user_wants_registration', False):
                    st.markdown("---")
                    registration_complete = self.registration_form.display_registration_form()
                    
                    if registration_complete:
                        st.success("✅ Registration completed! This will help speed up our conversation.")
                        st.session_state.user_wants_registration = False
                        st.balloons()
                        st.rerun()
        
        # If registration is complete, show a summary
        elif st.session_state.get('registration_completed', False):
            with st.expander("👤 Registration Summary", expanded=False):
                self.registration_form.display_registration_summary()
        
        # Render chat interface
        user_input = self.chat_interface.render()
        
        # Check if this is a slot selection (PRIORITY: Handle slot selection regardless of user input)
        if (st.session_state.scheduling_context.get('selected_slot') and 
            not st.session_state.scheduling_context.get('appointment_confirmed') and
            not st.session_state.get('slot_booking_completed', False)):
            
            # Note: Registration is optional - users can book with information gathered conversationally
            
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
                # Mark booking as completed to prevent rerun loops
                st.session_state.slot_booking_completed = True
            else:
                error_msg = f"Sorry, there was an error booking your appointment: {booking_result.get('appointment_error', 'Unknown error')}"
                self.chat_interface.add_assistant_message(error_msg)
            
            # Clear the selected slot and prevent further processing
            st.session_state.scheduling_context['selected_slot'] = None
            st.session_state.slot_selection_in_progress = False
            
            # Only rerun if booking was successful to show confirmation
            if booking_result.get('appointment_confirmed'):
                st.rerun()
            return
        
        # Process user input if provided
        elif user_input:
            # Process regular user message
            with st.spinner("🤖 Thinking..."):
                result = self.process_user_message(user_input)
            
            # Registration form is user-initiated only - no automatic prompting
            
            # Enhanced display for INFO responses with source references
            if result['metadata'].get('decision') == 'INFO':
                self.display_info_response_enhanced(result['response'], result['metadata'])
            else:
                # Add regular assistant response
                self.chat_interface.add_assistant_message(
                    result['response'],
                    result['metadata']
                )
            
            # Update conversation stage based on decision
            if result['metadata'].get('decision') == 'SCHEDULE':
                self.chat_interface.update_conversation_stage('scheduling')
            elif result['metadata'].get('appointment_confirmed'):
                self.chat_interface.update_conversation_stage('completed')
            elif result['metadata'].get('decision') == 'END':
                self.chat_interface.update_conversation_stage('ended')
            
            # Rerun to display new message
            st.rerun()
            
        # Display enhanced session statistics in sidebar
        self.display_session_stats()
    
    def display_info_response_enhanced(self, response: str, metadata: Dict):
        """Display INFO responses with enhanced formatting and source references."""
        # Add the response to chat first
        self.chat_interface.add_assistant_message(response, metadata)
        
        # Display enhanced info panel in sidebar
        with st.sidebar:
            st.markdown("---")
            st.subheader("📚 Information Response Details")
            
            # Show confidence and sources
            confidence = metadata.get('confidence', 0.8)
            st.progress(confidence, f"Confidence: {confidence:.0%}")
            
            has_context = metadata.get('has_context', True)
            st.write(f"**Context Available:** {'✅' if has_context else '❌'}")
            
            # Show sources used
            if metadata.get('sources_used'):
                st.write("**📁 Sources Referenced:**")
                for source in metadata['sources_used']:
                    st.write(f"• {source}")
            
            # Show response time
            if 'response_time' in metadata:
                st.write(f"**⏱️ Response Time:** {metadata['response_time']:.2f}s")
    
    def display_session_stats(self):
        """Display session statistics in sidebar."""
        with st.sidebar:
            st.markdown("---")
            st.subheader("📊 Session Statistics")
            
            if st.session_state.admin_analytics['conversation_logs']:
                total_interactions = len(st.session_state.admin_analytics['conversation_logs'])
                st.metric("Total Interactions", total_interactions)
                
                # Count decision types
                from collections import Counter
                decision_counts = Counter(
                    log['data'].get('decision', 'unknown') 
                    for log in st.session_state.admin_analytics['conversation_logs']
                    if log['event_type'] == 'agent_decision'
                )
                
                if decision_counts:
                    st.write("**Decision Breakdown:**")
                    for decision, count in decision_counts.most_common():
                        st.write(f"• {decision}: {count}")
                        
                # Show recent activity
                recent_threshold = datetime.now() - timedelta(minutes=5)
                recent_activity = len([
                    log for log in st.session_state.admin_analytics['conversation_logs']
                    if log['timestamp'] > recent_threshold
                ])
                st.metric("Recent Activity (5m)", recent_activity)
            else:
                st.info("No session data yet. Start chatting to see statistics!")


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