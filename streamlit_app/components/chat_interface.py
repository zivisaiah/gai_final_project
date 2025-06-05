"""
Chat Interface Components for Streamlit
Handles chat UI, message display, and user interactions
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


class ChatMessage:
    """Represents a single chat message."""
    
    def __init__(self, role: str, content: str, timestamp: datetime = None, metadata: Dict = None):
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary for storage."""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        """Create message from dictionary."""
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


class ChatInterface:
    """Main chat interface component for Streamlit."""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state for chat."""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'conversation_id' not in st.session_state:
            st.session_state.conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if 'candidate_info' not in st.session_state:
            st.session_state.candidate_info = {
                'name': None,
                'experience': None,
                'interest_level': None,
                'email': None,
                'phone': None
            }
        
        if 'conversation_stage' not in st.session_state:
            st.session_state.conversation_stage = 'greeting'
        
        if 'scheduling_context' not in st.session_state:
            st.session_state.scheduling_context = {
                'slots_offered': [],
                'selected_slot': None,
                'appointment_confirmed': False
            }
    
    def display_chat_header(self):
        """Display the chat header with title and info."""
        st.title("🤖 Python Developer Recruitment Assistant")
        
        # Display conversation info in sidebar
        with st.sidebar:
            st.header("📊 Conversation Info")
            st.write(f"**Conversation ID:** {st.session_state.conversation_id}")
            st.write(f"**Messages:** {len(st.session_state.messages)}")
            st.write(f"**Stage:** {st.session_state.conversation_stage.title()}")
            
            # Display candidate info if available
            if any(st.session_state.candidate_info.values()):
                st.subheader("👤 Candidate Info")
                for key, value in st.session_state.candidate_info.items():
                    if value:
                        st.write(f"**{key.title()}:** {value}")
            
            # Display scheduling context if relevant
            if st.session_state.scheduling_context['slots_offered']:
                st.subheader("📅 Scheduling")
                st.write(f"**Slots Offered:** {len(st.session_state.scheduling_context['slots_offered'])}")
                if st.session_state.scheduling_context['selected_slot']:
                    st.write(f"**Selected:** {st.session_state.scheduling_context['selected_slot']}")
                if st.session_state.scheduling_context['appointment_confirmed']:
                    st.success("✅ Appointment Confirmed!")
            
            # Clear conversation button
            if st.button("🗑️ Clear Conversation", type="secondary"):
                self.clear_conversation()
                st.rerun()
    
    def display_messages(self):
        """Display all chat messages."""
        for message in st.session_state.messages:
            self.display_single_message(message)
    
    def display_single_message(self, message: ChatMessage):
        """Display a single chat message with appropriate styling."""
        
        if message.role == 'user':
            with st.chat_message("user", avatar="👤"):
                st.write(message.content)
                if message.metadata:
                    with st.expander("📋 Message Details", expanded=False):
                        st.json(message.metadata)
        
        elif message.role == 'assistant':
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message.content)
                
                # Display any special metadata
                if message.metadata:
                    metadata = message.metadata
                    
                    # Show decision reasoning if available
                    if 'decision' in metadata:
                        st.info(f"**Decision:** {metadata['decision']}")
                    
                    if 'reasoning' in metadata:
                        with st.expander("🧠 AI Reasoning", expanded=False):
                            st.write(metadata['reasoning'])
                    
                    # Show scheduling slots if available
                    if 'suggested_slots' in metadata and metadata['suggested_slots']:
                        st.subheader("📅 Available Time Slots")
                        for i, slot in enumerate(metadata['suggested_slots'], 1):
                            slot_dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                            formatted_time = slot_dt.strftime("%A, %B %d at %I:%M %p")
                            recruiter = slot.get('recruiter', 'Our team')
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{i}.** {formatted_time} with {recruiter}")
                            with col2:
                                if st.button(f"Select", key=f"slot_{i}_{slot_dt.timestamp()}"):
                                    self.handle_slot_selection(slot)
                    
                    # Show appointment confirmation if available
                    if 'appointment_confirmed' in metadata and metadata['appointment_confirmed']:
                        st.success("🎉 **Interview Scheduled Successfully!**")
                        if 'appointment_details' in metadata:
                            details = metadata['appointment_details']
                            st.write(f"📅 **Date & Time:** {details.get('datetime', 'TBD')}")
                            st.write(f"👤 **Interviewer:** {details.get('recruiter', 'TBD')}")
                            st.write(f"⏱️ **Duration:** {details.get('duration', 45)} minutes")
        
        elif message.role == 'system':
            with st.chat_message("assistant", avatar="ℹ️"):
                st.info(message.content)
    
    def handle_user_input(self) -> Optional[str]:
        """Handle user input and return the message if submitted."""
        
        # If conversation ended, do not show input
        if st.session_state.conversation_stage == 'ended':
            return None
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message to session state
            user_message = ChatMessage(
                role='user',
                content=user_input,
                metadata={'input_method': 'chat_input'}
            )
            st.session_state.messages.append(user_message)
            
            return user_input
        
        return None
    
    def add_assistant_message(self, content: str, metadata: Dict = None):
        """Add an assistant message to the conversation."""
        assistant_message = ChatMessage(
            role='assistant',
            content=content,
            metadata=metadata or {}
        )
        st.session_state.messages.append(assistant_message)
    
    def add_system_message(self, content: str):
        """Add a system message to the conversation."""
        system_message = ChatMessage(
            role='system',
            content=content
        )
        st.session_state.messages.append(system_message)
    
    def handle_slot_selection(self, selected_slot: Dict):
        """Handle when user selects a time slot."""
        st.session_state.scheduling_context['selected_slot'] = selected_slot
        
        # Add user message indicating slot selection
        slot_dt = datetime.fromisoformat(selected_slot['datetime'].replace('Z', '+00:00'))
        formatted_time = slot_dt.strftime("%A, %B %d at %I:%M %p")
        
        selection_message = ChatMessage(
            role='user',
            content=f"I'd like to book the {formatted_time} slot with {selected_slot.get('recruiter', 'the interviewer')}.",
            metadata={'slot_selection': selected_slot}
        )
        st.session_state.messages.append(selection_message)
        
        # Trigger rerun to process the selection
        st.rerun()
    
    def update_candidate_info(self, info_updates: Dict):
        """Update candidate information in session state."""
        st.session_state.candidate_info.update(info_updates)
    
    def update_conversation_stage(self, stage: str):
        """Update the conversation stage."""
        st.session_state.conversation_stage = stage
    
    def update_scheduling_context(self, context_updates: Dict):
        """Update scheduling context."""
        st.session_state.scheduling_context.update(context_updates)
    
    def clear_conversation(self):
        """Clear the entire conversation."""
        st.session_state.messages = []
        st.session_state.conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.candidate_info = {
            'name': None,
            'experience': None,
            'interest_level': None,
            'email': None,
            'phone': None
        }
        st.session_state.conversation_stage = 'greeting'
        st.session_state.scheduling_context = {
            'slots_offered': [],
            'selected_slot': None,
            'appointment_confirmed': False
        }
    
    def export_conversation(self) -> Dict:
        """Export the conversation for analysis or storage."""
        return {
            'conversation_id': st.session_state.conversation_id,
            'messages': [msg.to_dict() for msg in st.session_state.messages],
            'candidate_info': st.session_state.candidate_info,
            'conversation_stage': st.session_state.conversation_stage,
            'scheduling_context': st.session_state.scheduling_context,
            'exported_at': datetime.now().isoformat()
        }
    
    def display_conversation_stats(self):
        """Display conversation statistics in the sidebar."""
        with st.sidebar:
            st.subheader("📈 Conversation Stats")
            
            total_messages = len(st.session_state.messages)
            user_messages = len([m for m in st.session_state.messages if m.role == 'user'])
            assistant_messages = len([m for m in st.session_state.messages if m.role == 'assistant'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total", total_messages)
                st.metric("User", user_messages)
            with col2:
                st.metric("Assistant", assistant_messages)
                st.metric("Ratio", f"{assistant_messages/max(user_messages, 1):.1f}")
            
            # Export conversation button
            if st.button("📥 Export Conversation"):
                conversation_data = self.export_conversation()
                st.download_button(
                    label="💾 Download JSON",
                    data=json.dumps(conversation_data, indent=2),
                    file_name=f"conversation_{st.session_state.conversation_id}.json",
                    mime="application/json"
                )
    
    def display_quick_actions(self):
        """Display quick action buttons."""
        st.subheader("⚡ Quick Actions")
        
        # If conversation ended, only show Start Over
        if st.session_state.conversation_stage == 'ended':
            if st.button("👋 Start Over"):
                self.add_user_quick_message("Hi, I'd like to start over.")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👋 Start Over"):
                self.add_user_quick_message("Hi, I'd like to start over.")
        
        with col2:
            if st.button("📅 Schedule Interview"):
                self.add_user_quick_message("I'd like to schedule an interview.")
        
        with col3:
            if st.button("❓ Ask Question"):
                self.add_user_quick_message("I have a question about the role.")
    
    def add_user_quick_message(self, content: str):
        """Add a quick user message and trigger rerun."""
        quick_message = ChatMessage(
            role='user',
            content=content,
            metadata={'input_method': 'quick_action'}
        )
        st.session_state.messages.append(quick_message)
        st.rerun()
    
    def display_welcome_message(self):
        """Display welcome message if conversation is empty."""
        if not st.session_state.messages:
            welcome_message = ChatMessage(
                role='assistant',
                content="""👋 **Welcome to our Python Developer Recruitment Assistant!**

I'm here to help you learn about our Python developer position and potentially schedule an interview.

I can help you with:
• 📋 Information about the role and requirements
• 💼 Understanding our company and team
• 📅 Scheduling an interview at your convenience
• ❓ Answering any questions you might have

Feel free to ask me anything or let me know if you're interested in scheduling an interview!""",
                metadata={'message_type': 'welcome'}
            )
            st.session_state.messages.append(welcome_message)
    
    def render(self) -> Optional[str]:
        """Render the complete chat interface and return user input if any."""
        
        # Display header and sidebar info
        self.display_chat_header()
        
        # Display welcome message if needed
        self.display_welcome_message()
        
        # Display conversation stats
        self.display_conversation_stats()
        
        # Display all messages
        self.display_messages()
        
        # Display quick actions
        with st.sidebar:
            self.display_quick_actions()
        
        # If conversation ended, show farewell and do not accept input
        if st.session_state.conversation_stage == 'ended':
            st.info("\n\n**השיחה הסתיימה. תודה ובהצלחה!**\n\nניתן להתחיל שיחה חדשה בלחיצה על 'Start Over'.")
            return None
        
        # Handle user input
        return self.handle_user_input()


def create_chat_interface() -> ChatInterface:
    """Factory function to create a chat interface."""
    return ChatInterface() 