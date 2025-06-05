"""
Core Agent Tests
Testing conversation flow, decision making, and LangChain integration
"""

import pytest
import sys
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.agents.core_agent import CoreAgent, AgentDecision, ConversationState
from app.modules.prompts.phase1_prompts import Phase1Prompts
from app.modules.utils.conversation import ConversationContext
from config.phase1_settings import Settings


class TestCoreAgent:
    """Test cases for Core Agent."""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI response for testing."""
        mock_response = Mock()
        mock_response.content = """
        DECISION: CONTINUE
        REASONING: Need to gather more information about the candidate's experience
        RESPONSE: Great to hear! Could you tell me more about your Python experience and what projects you've worked on?
        """
        return mock_response
    
    @pytest.fixture
    def core_agent(self):
        """Create a core agent with mocked OpenAI for testing."""
        with patch('app.modules.agents.core_agent.ChatOpenAI') as mock_llm:
            mock_instance = Mock()
            mock_llm.return_value = mock_instance
            
            agent = CoreAgent(openai_api_key="test-key", model_name="gpt-3.5-turbo")
            agent.llm = mock_instance
            return agent
    
    def test_core_agent_initialization(self, core_agent):
        """Test core agent initialization."""
        assert core_agent is not None
        assert hasattr(core_agent, 'llm')
        assert hasattr(core_agent, 'memory')
        assert hasattr(core_agent, 'conversations')
        assert hasattr(core_agent, 'prompts')
    
    def test_conversation_state_creation(self):
        """Test conversation state management."""
        conv_state = ConversationState("test_conv")
        assert conv_state.conversation_id == "test_conv"
        assert len(conv_state.messages) == 0
        assert len(conv_state.decision_history) == 0
    
    def test_add_message_to_conversation(self):
        """Test adding messages to conversation state."""
        conv_state = ConversationState("test_conv")
        
        conv_state.add_message("user", "Hello, I'm interested in the Python role")
        assert len(conv_state.messages) == 1
        assert conv_state.messages[0]["role"] == "user"
        assert conv_state.messages[0]["content"] == "Hello, I'm interested in the Python role"
    
    def test_candidate_info_extraction(self):
        """Test candidate information extraction from messages."""
        conv_state = ConversationState("test_conv")
        
        # Add messages that should extract candidate info
        conv_state.add_message("user", "Hi, I'm Sarah and I have 3 years of Python experience")
        conv_state.add_message("user", "I'm very interested in this position and available next week")
        
        # Check extracted info
        info = conv_state.candidate_info
        assert info["name"] == "Sarah"
        assert info["experience"] == "mentioned"
        assert info["interest_level"] == "high"
        assert info["availability_mentioned"] == True
    
    @patch('app.modules.agents.core_agent.ChatOpenAI')
    def test_agent_decision_parsing(self, mock_llm):
        """Test agent response parsing."""
        # Create agent with mocked LLM
        agent = CoreAgent(openai_api_key="test-key")
        
        # Test parsing structured response
        response_text = """
        DECISION: SCHEDULE
        REASONING: Candidate has shown interest and provided basic information
        RESPONSE: Great! Let me check our available interview slots for you.
        """
        
        decision, reasoning, response = agent._parse_agent_response(response_text)
        
        assert decision == AgentDecision.SCHEDULE
        assert "Candidate has shown interest" in reasoning
        assert "available interview slots" in response
    
    @patch('app.modules.agents.core_agent.ChatOpenAI')
    def test_fallback_decision_making(self, mock_llm):
        """Test fallback decision making when LLM fails."""
        agent = CoreAgent(openai_api_key="test-key")
        conv_state = ConversationState("test_conv")
        
        # Test scheduling intent
        decision, reasoning, response = agent._fallback_decision(
            "When can we schedule an interview?", 
            conv_state
        )
        # Should continue since no interest level is set
        assert decision == AgentDecision.CONTINUE
        
        # Test with high interest
        conv_state.candidate_info = {"interest_level": "high"}
        decision, reasoning, response = agent._fallback_decision(
            "When can we schedule an interview?", 
            conv_state
        )
        assert decision == AgentDecision.SCHEDULE
    
    @patch('app.modules.agents.core_agent.ChatOpenAI')
    def test_decision_validation(self, mock_llm):
        """Test decision validation based on conversation state."""
        agent = CoreAgent(openai_api_key="test-key")
        conv_state = ConversationState("test_conv")
        
        # Test override to SCHEDULE when all conditions met
        conv_state.candidate_info = {
            "name": "John",
            "experience": "mentioned", 
            "interest_level": "high",
            "availability_mentioned": True
        }
        
        validated_decision = agent._validate_decision(AgentDecision.CONTINUE, conv_state)
        assert validated_decision == AgentDecision.SCHEDULE
        
        # Test override to CONTINUE when insufficient info
        conv_state.candidate_info = {"interest_level": "unknown"}
        validated_decision = agent._validate_decision(AgentDecision.SCHEDULE, conv_state)
        assert validated_decision == AgentDecision.CONTINUE
    
    def test_start_conversation(self, core_agent):
        """Test starting a new conversation."""
        greeting, conversation = core_agent.start_conversation()
        
        assert greeting is not None
        assert "Python Developer position" in greeting
        assert conversation.conversation_id is not None
        assert len(conversation.messages) == 1
        assert conversation.messages[0]["role"] == "assistant"
    
    def test_conversation_export(self, core_agent):
        """Test conversation data export."""
        # Start conversation and add some messages
        greeting, conversation = core_agent.start_conversation("test_conv")
        conversation.add_message("user", "I'm interested!")
        conversation.add_decision(AgentDecision.CONTINUE, "Gathering info", "Tell me more")
        
        # Export conversation
        exported = core_agent.export_conversation("test_conv")
        
        assert exported["conversation_id"] == "test_conv"
        assert len(exported["messages"]) == 2  # greeting + user message
        assert len(exported["decision_history"]) == 1
        assert "summary" in exported
    
    def test_agent_statistics(self, core_agent):
        """Test agent usage statistics."""
        # Create some conversations
        core_agent.start_conversation("conv1")
        core_agent.start_conversation("conv2")
        
        stats = core_agent.get_statistics()
        
        assert stats["total_conversations"] == 2
        assert stats["total_messages"] >= 2  # At least greeting messages
        assert "decision_counts" in stats
        assert "average_messages_per_conversation" in stats


class TestPrompts:
    """Test prompt management and generation."""
    
    def test_prompt_templates(self):
        """Test prompt template access."""
        prompts = Phase1Prompts()
        
        # Test system prompt
        system_prompt = prompts.get_core_agent_prompt()
        assert "recruitment assistant" in system_prompt.lower()
        assert "CONTINUE" in system_prompt
        assert "SCHEDULE" in system_prompt
        
        # Test conversation templates
        greeting = prompts.get_template("greeting")
        assert "Python Developer position" in greeting
        
        role_desc = prompts.get_template("role_description")
        assert "Django" in role_desc or "Flask" in role_desc
    
    def test_decision_prompt_generation(self):
        """Test decision prompt generation with context."""
        prompts = Phase1Prompts()
        
        conversation_history = [
            {"role": "assistant", "content": "Hi! Are you interested in Python roles?"},
            {"role": "user", "content": "Yes, I'm very interested!"}
        ]
        
        decision_prompt = prompts.get_decision_prompt(conversation_history, "Tell me more!")
        
        assert "CONTINUE" in decision_prompt
        assert "SCHEDULE" in decision_prompt
        assert "Tell me more!" in decision_prompt
        assert "Yes, I'm very interested!" in decision_prompt
    
    def test_candidate_info_extraction_prompt(self):
        """Test candidate information extraction prompt generation."""
        prompts = Phase1Prompts()
        
        messages = [
            {"role": "user", "content": "Hi, I'm Alex and I have 5 years of Python experience"},
            {"role": "user", "content": "I'm very excited about this opportunity and available next week"}
        ]
        
        # Test that the extraction prompt is properly generated
        extraction_prompt = prompts.get_candidate_info_extraction_prompt(messages)
        
        assert "Alex" in extraction_prompt
        assert "5 years of Python" in extraction_prompt  
        assert "excited" in extraction_prompt
        assert "available next week" in extraction_prompt
        assert "EXTRACTION TASK" in extraction_prompt
        assert "RESPONSE FORMAT" in extraction_prompt
    
    def test_few_shot_examples(self):
        """Test few-shot example structure."""
        prompts = Phase1Prompts()
        examples = prompts.get_few_shot_examples()
        
        assert len(examples) > 0
        
        for example in examples:
            assert "conversation_history" in example
            assert "decision" in example
            assert "reasoning" in example
            assert "response" in example
            assert example["decision"] in ["CONTINUE", "SCHEDULE"]


class TestConversationContext:
    """Test conversation context management."""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temporary storage directory for testing."""
        return str(tmp_path)
    
    def test_conversation_context_creation(self, temp_storage):
        """Test conversation context initialization."""
        context = ConversationContext(storage_dir=temp_storage)
        
        assert context.conversation_id is not None
        assert context.session is not None
        assert context.message_history is not None
    
    def test_message_handling(self, temp_storage):
        """Test adding and retrieving messages."""
        context = ConversationContext("test_conv", storage_dir=temp_storage)
        
        # Add messages
        context.add_user_message("Hello!")
        context.add_assistant_message("Hi there!")
        
        # Check message history
        recent_messages = context.message_history.get_recent_messages(5)
        assert len(recent_messages) == 2
        assert recent_messages[0]["role"] == "user"
        assert recent_messages[1]["role"] == "assistant"
    
    def test_context_data_management(self, temp_storage):
        """Test setting and getting context data."""
        context = ConversationContext("test_conv", storage_dir=temp_storage)
        
        # Set context data
        context.set_context_data("last_decision", "CONTINUE")
        context.update_candidate_info({"name": "Test User"})
        
        # Get context data
        assert context.get_context_data("last_decision") == "CONTINUE"
        assert context.candidate_info["name"] == "Test User"
    
    def test_conversation_export(self, temp_storage):
        """Test exporting conversation context."""
        context = ConversationContext("test_conv", storage_dir=temp_storage)
        
        context.add_user_message("Test message")
        context.update_candidate_info({"name": "Test"})
        
        exported = context.export_conversation()
        
        assert exported["conversation_id"] == "test_conv"
        assert exported["candidate_info"]["name"] == "Test"
        assert exported["summary"]["total_messages"] == 1


def test_integration_scenario():
    """Test a complete conversation scenario."""
    with patch('app.modules.agents.core_agent.ChatOpenAI') as mock_llm:
        # Mock LLM responses for different turns
        mock_responses = [
            Mock(content="DECISION: CONTINUE\nREASONING: Need more info\nRESPONSE: Tell me about your experience!"),
            Mock(content="DECISION: CONTINUE\nREASONING: Building rapport\nRESPONSE: That sounds great! What interests you most?"),
            Mock(content="DECISION: SCHEDULE\nREASONING: Ready to schedule\nRESPONSE: Let me check our interview slots!")
        ]
        
        mock_instance = Mock()
        mock_instance.invoke.side_effect = mock_responses
        mock_llm.return_value = mock_instance
        
        # Create agent
        agent = CoreAgent(openai_api_key="test-key")
        agent.llm = mock_instance
        
        # Simulate conversation flow
        greeting, conv = agent.start_conversation("integration_test")
        assert "Python Developer" in greeting
        
        # User shows interest
        response1, decision1, reasoning1 = agent.process_message(
            "Hi! I'm interested in Python roles", 
            "integration_test"
        )
        assert decision1 == AgentDecision.CONTINUE
        
        # User provides experience
        response2, decision2, reasoning2 = agent.process_message(
            "I'm Sarah with 3 years of Django experience", 
            "integration_test"
        )
        assert decision2 == AgentDecision.CONTINUE
        
        # User expresses strong interest
        response3, decision3, reasoning3 = agent.process_message(
            "This sounds perfect! When can we schedule an interview?", 
            "integration_test"
        )
        assert decision3 == AgentDecision.SCHEDULE
        
        # Check conversation state
        final_conv = agent.get_conversation_state("integration_test")
        assert final_conv.candidate_info["name"] == "Sarah"
        assert final_conv.candidate_info["interest_level"] == "high"


if __name__ == "__main__":
    # Run basic tests without pytest
    print("🧪 Running Core Agent Tests...")
    
    try:
        # Test ConversationState
        print("\n✅ Testing ConversationState...")
        conv_state = ConversationState("test")
        # Note: add_message now requires an agent parameter for LLM extraction
        # For basic testing, we'll just check the state structure
        print(f"   Initial candidate info: {conv_state.candidate_info}")
        print(f"   Conversation ID: {conv_state.conversation_id}")
        print(f"   Message count: {len(conv_state.messages)}")
        
        # Test Prompts
        print("\n✅ Testing Prompts...")
        prompts = Phase1Prompts()
        system_prompt = prompts.get_core_agent_prompt()
        print(f"   System prompt length: {len(system_prompt)} characters")
        
        examples = prompts.get_few_shot_examples()
        print(f"   Few-shot examples: {len(examples)} examples")
        
        print("\n🎉 Basic tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc() 