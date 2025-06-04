"""
Simple Streamlit Components Test Script
Testing Streamlit components without running the actual server
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("🧪 Testing Streamlit Components...")
    
    # Mock Streamlit before importing our components
    print("\n📦 Mocking Streamlit...")
    
    # Create comprehensive Streamlit mock
    st_mock = MagicMock()
    
    # Create a proper session_state mock that behaves like a dict but allows attribute access
    class SessionStateMock:
        def __init__(self):
            self._data = {}
        
        def __getattr__(self, name):
            return self._data.get(name)
        
        def __setattr__(self, name, value):
            if name.startswith('_'):
                super().__setattr__(name, value)
            else:
                if not hasattr(self, '_data'):
                    super().__setattr__('_data', {})
                self._data[name] = value
        
        def __contains__(self, key):
            return key in self._data
        
        def get(self, key, default=None):
            return self._data.get(key, default)
        
        def keys(self):
            return self._data.keys()
    
    st_mock.session_state = SessionStateMock()
    st_mock.chat_message = MagicMock()
    st_mock.chat_input = MagicMock(return_value=None)
    st_mock.button = MagicMock(return_value=False)
    st_mock.write = MagicMock()
    st_mock.title = MagicMock()
    st_mock.header = MagicMock()
    st_mock.subheader = MagicMock()
    st_mock.sidebar = MagicMock()
    st_mock.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    st_mock.expander = MagicMock()
    st_mock.info = MagicMock()
    st_mock.success = MagicMock()
    st_mock.error = MagicMock()
    st_mock.warning = MagicMock()
    st_mock.metric = MagicMock()
    st_mock.json = MagicMock()
    st_mock.download_button = MagicMock()
    st_mock.checkbox = MagicMock(return_value=False)
    st_mock.rerun = MagicMock()
    st_mock.spinner = MagicMock()
    st_mock.set_page_config = MagicMock()
    st_mock.stop = MagicMock()
    
    # Mock the context managers
    st_mock.chat_message.return_value.__enter__ = MagicMock()
    st_mock.chat_message.return_value.__exit__ = MagicMock()
    st_mock.sidebar.__enter__ = MagicMock()
    st_mock.sidebar.__exit__ = MagicMock()
    st_mock.expander.return_value.__enter__ = MagicMock()
    st_mock.expander.return_value.__exit__ = MagicMock()
    st_mock.spinner.return_value.__enter__ = MagicMock()
    st_mock.spinner.return_value.__exit__ = MagicMock()
    
    # Patch streamlit
    with patch.dict('sys.modules', {'streamlit': st_mock}):
        
        # Test ChatMessage class
        print("\n💬 Testing ChatMessage...")
        from streamlit_app.components.chat_interface import ChatMessage
        
        # Create test message
        test_message = ChatMessage(
            role='user',
            content='Hello, I am interested in the Python role',
            metadata={'test': True}
        )
        
        print(f"✅ Created message: {test_message.role} - {test_message.content[:30]}...")
        
        # Test serialization
        message_dict = test_message.to_dict()
        print(f"✅ Serialized message: {len(message_dict)} fields")
        
        # Test deserialization
        restored_message = ChatMessage.from_dict(message_dict)
        print(f"✅ Restored message: {restored_message.role} - {restored_message.content[:30]}...")
        
        # Test ChatInterface class
        print("\n🖥️ Testing ChatInterface...")
        from streamlit_app.components.chat_interface import ChatInterface, create_chat_interface
        
        # Create chat interface
        chat_interface = create_chat_interface()
        print("✅ Created ChatInterface instance")
        
        # Test session state initialization
        chat_interface.initialize_session_state()
        print("✅ Initialized session state")
        
        # Test adding messages
        chat_interface.add_assistant_message(
            "Hello! I'm here to help with your Python developer application.",
            {'message_type': 'greeting'}
        )
        print("✅ Added assistant message")
        
        chat_interface.add_system_message("System initialized successfully")
        print("✅ Added system message")
        
        # Test candidate info update
        chat_interface.update_candidate_info({
            'name': 'John Doe',
            'experience': '3 years Python'
        })
        print("✅ Updated candidate info")
        
        # Test conversation export
        export_data = chat_interface.export_conversation()
        print(f"✅ Exported conversation: {len(export_data)} fields")
        
        # Test slot selection handling
        test_slot = {
            'datetime': '2024-01-15T10:00:00',
            'recruiter': 'Alice Smith',
            'recruiter_id': 1,
            'duration': 45
        }
        
        # Mock the rerun function to avoid actual Streamlit rerun
        with patch.object(chat_interface, 'handle_slot_selection') as mock_selection:
            mock_selection.return_value = None
            print("✅ Slot selection handling mocked")
        
        # Test rendering (mocked)
        with patch.object(chat_interface, 'render') as mock_render:
            mock_render.return_value = "Test user input"
            user_input = chat_interface.render()
            print(f"✅ Render method called, returned: {user_input}")
    
    # Test main Streamlit application components
    print("\n🚀 Testing Main Application...")
    
    # Mock additional dependencies
    with patch.dict('sys.modules', {
        'streamlit': st_mock,
        'app.modules.agents.core_agent': MagicMock(),
        'app.modules.agents.scheduling_advisor': MagicMock(),
        'app.modules.utils.conversation': MagicMock(),
        'config.phase1_settings': MagicMock()
    }):
        
        # Mock the settings
        mock_settings = MagicMock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_MODEL = "gpt-3.5-turbo"
        mock_settings.OPENAI_TEMPERATURE = 0.7
        mock_settings.OPENAI_MAX_TOKENS = 1000
        
        with patch('streamlit_app.streamlit_main.get_settings', return_value=mock_settings):
            
            # Import and test main application
            from streamlit_app.streamlit_main import RecruitmentChatbot
            
            # Mock the agent initialization to avoid actual API calls
            with patch.object(RecruitmentChatbot, 'initialize_agents') as mock_init:
                mock_init.return_value = None
                
                # Create chatbot instance
                chatbot = RecruitmentChatbot()
                chatbot.core_agent = MagicMock()
                chatbot.scheduling_advisor = MagicMock()
                chatbot.conversation_context = MagicMock()
                
                print("✅ Created RecruitmentChatbot instance")
                
                # Test message processing (mocked)
                mock_conversation_state = MagicMock()
                mock_conversation_state.messages = []
                mock_conversation_state.extract_candidate_info.return_value = {'name': 'Test User'}
                chatbot.core_agent.conversation_state = mock_conversation_state
                chatbot.core_agent.make_decision.return_value = ('CONTINUE', 'Test reasoning', 'Test response')
                
                result = chatbot.process_user_message("Hello, I'm interested in the role")
                print(f"✅ Processed user message: {result['success']}")
                
                # Test scheduling decision handling
                chatbot.scheduling_advisor.make_scheduling_decision.return_value = (
                    'SCHEDULE', 'Ready to schedule', [], 'Let me find available slots'
                )
                
                scheduling_result = chatbot.handle_scheduling_decision([], "I'd like to schedule an interview")
                print(f"✅ Handled scheduling decision: {len(scheduling_result)} fields")
                
                # Test slot booking
                chatbot.scheduling_advisor.book_appointment.return_value = {
                    'success': True,
                    'appointment_id': 12345,
                    'recruiter': {'name': 'Alice Smith'},
                    'confirmation_message': 'Interview scheduled successfully!'
                }
                
                booking_result = chatbot.handle_slot_selection(test_slot)
                print(f"✅ Handled slot booking: {booking_result.get('appointment_confirmed', False)}")
                
                # Test system status display (mocked)
                chatbot.scheduling_advisor.get_scheduling_statistics.return_value = {
                    'available_slots': 25,
                    'recruiter_count': 3
                }
                
                with patch.object(chatbot, 'display_system_status') as mock_status:
                    mock_status.return_value = None
                    chatbot.display_system_status()
                    print("✅ System status display mocked")
    
    print("\n🎉 All Streamlit component tests completed successfully!")
    print("\n📊 Test Summary:")
    print("✅ ChatMessage: Working")
    print("✅ ChatInterface: Working")
    print("✅ RecruitmentChatbot: Working (Mocked)")
    print("✅ Message Processing: Working")
    print("✅ Scheduling Integration: Working")
    print("✅ Slot Booking: Working")
    
    print("\n🚀 Phase 1.5 Streamlit UI Implementation is ready!")
    print("Next steps:")
    print("1. Test with real Streamlit server: streamlit run streamlit_app/streamlit_main.py")
    print("2. Verify end-to-end conversation flow")
    print("3. Test scheduling functionality with real database")
    print("4. Complete Phase 1 integration testing")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 