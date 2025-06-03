"""
Simple Core Agent Test Script
Testing Core Agent functionality without requiring OpenAI API access
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("🧪 Testing Core Agent Implementation...")
    
    # Test imports
    print("\n📦 Testing Imports...")
    from app.modules.agents.core_agent import CoreAgent, AgentDecision, ConversationState
    from app.modules.prompts.phase1_prompts import Phase1Prompts
    from app.modules.utils.conversation import ConversationContext
    from config.phase1_settings import Settings
    print("✅ All imports successful!")
    
    # Test ConversationState
    print("\n🔄 Testing ConversationState...")
    conv_state = ConversationState("test_conversation")
    print(f"✅ Created conversation: {conv_state.conversation_id}")
    
    # Add test messages
    conv_state.add_message("assistant", "Hi! I'm reaching out about our Python Developer position. Are you currently open to new opportunities?")
    conv_state.add_message("user", "Hi! I'm Sarah, and I have 3 years of Python experience with Django. I'm very interested!")
    print(f"✅ Added {len(conv_state.messages)} messages")
    
    # Test candidate info extraction
    print(f"✅ Extracted candidate info: {conv_state.candidate_info}")
    
    # Test decision recording
    conv_state.add_decision(AgentDecision.CONTINUE, "Need more information", "Tell me more about your experience")
    print(f"✅ Recorded decision: {conv_state.last_decision.value}")
    
    # Test Prompts
    print("\n📝 Testing Prompts...")
    prompts = Phase1Prompts()
    
    system_prompt = prompts.get_core_agent_prompt()
    print(f"✅ System prompt length: {len(system_prompt)} characters")
    
    greeting = prompts.get_template("greeting")
    print(f"✅ Greeting: {greeting[:50]}...")
    
    examples = prompts.get_few_shot_examples()
    print(f"✅ Few-shot examples: {len(examples)} examples")
    
    # Test example structure
    first_example = examples[0]
    print(f"✅ Example decision: {first_example['decision']}")
    print(f"✅ Example reasoning: {first_example['reasoning'][:50]}...")
    
    # Test candidate info extraction
    test_messages = [
        {"role": "user", "content": "I'm Alex and I have 5 years of Python and Django experience"},
        {"role": "user", "content": "I'm very excited about this role and available next week"}
    ]
    extracted_info = prompts.extract_candidate_info(test_messages)
    print(f"✅ Info extraction test: {extracted_info}")
    
    # Test ConversationContext
    print("\n💬 Testing ConversationContext...")
    context = ConversationContext("test_context")
    print(f"✅ Created context: {context.conversation_id}")
    
    context.add_user_message("Hello, I'm interested in the Python role")
    context.add_assistant_message("Great! Tell me about your experience.")
    print(f"✅ Added messages to context")
    
    context.update_candidate_info({"name": "Test User", "interest": "high"})
    print(f"✅ Updated candidate info: {context.candidate_info}")
    
    conversation_context = context.get_conversation_context()
    print(f"✅ Context summary: {len(conversation_context['recent_messages'])} recent messages")
    
    # Test Core Agent with Mocked LLM
    print("\n🤖 Testing Core Agent (Mocked)...")
    
    with patch('app.modules.agents.core_agent.ChatOpenAI') as mock_llm:
        # Create mock response
        mock_response = Mock()
        mock_response.content = """
        DECISION: CONTINUE
        REASONING: User has shown interest but I need more information about their specific experience and availability
        RESPONSE: That's wonderful to hear! Could you tell me more about your Python experience and what kind of projects you've worked on recently?
        """
        
        mock_instance = Mock()
        mock_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_instance
        
        # Create agent
        agent = CoreAgent(openai_api_key="test-key-for-mock")
        agent.llm = mock_instance
        print("✅ Created Core Agent with mocked LLM")
        
        # Start conversation
        greeting, conversation = agent.start_conversation("mock_test")
        print(f"✅ Started conversation: {greeting[:50]}...")
        
        # Process a user message
        response, decision, reasoning = agent.process_message(
            "Hi! I'm interested in Python development roles", 
            "mock_test"
        )
        print(f"✅ Processed message - Decision: {decision.value}")
        print(f"✅ Agent response: {response[:50]}...")
        print(f"✅ Reasoning: {reasoning[:50]}...")
        
        # Get conversation state
        final_state = agent.get_conversation_state("mock_test")
        print(f"✅ Final conversation has {len(final_state.messages)} messages")
        
        # Test statistics
        stats = agent.get_statistics()
        print(f"✅ Agent stats: {stats}")
        
        # Test conversation export
        exported = agent.export_conversation("mock_test")
        print(f"✅ Exported conversation: {len(exported['messages'])} messages")
    
    # Test response parsing
    print("\n🔍 Testing Response Parsing...")
    
    with patch('app.modules.agents.core_agent.ChatOpenAI'):
        agent = CoreAgent(openai_api_key="test-key")
        
        # Test structured response
        test_response = """
        DECISION: SCHEDULE
        REASONING: Candidate has provided name, experience, and expressed strong interest with availability
        RESPONSE: Excellent! Let me check our available interview slots and find a time that works for you.
        """
        
        decision, reasoning, response = agent._parse_agent_response(test_response)
        print(f"✅ Parsed decision: {decision.value}")
        print(f"✅ Parsed reasoning: {reasoning[:50]}...")
        print(f"✅ Parsed response: {response[:50]}...")
        
        # Test fallback decision making
        conv_state = ConversationState("fallback_test")
        conv_state.candidate_info = {"interest_level": "high"}
        
        fallback_decision, fallback_reasoning, fallback_response = agent._fallback_decision(
            "When can we schedule an interview?", 
            conv_state
        )
        print(f"✅ Fallback decision: {fallback_decision.value}")
    
    # Test Settings
    print("\n⚙️ Testing Settings...")
    settings = Settings()
    print(f"✅ App name: {settings.APP_NAME}")
    print(f"✅ Environment: {settings.ENVIRONMENT}")
    print(f"✅ OpenAI model: {settings.OPENAI_MODEL}")
    
    if settings.OPENAI_API_KEY:
        print(f"✅ OpenAI API key: ...{settings.OPENAI_API_KEY[-4:]}")
    else:
        print("⚠️  OpenAI API key not set (OK for testing)")
    
    print("\n🎉 All Core Agent tests completed successfully!")
    print("\n📊 Test Summary:")
    print("✅ ConversationState: Working")
    print("✅ Phase1Prompts: Working")
    print("✅ ConversationContext: Working")
    print("✅ CoreAgent (Mocked): Working")
    print("✅ Response Parsing: Working")
    print("✅ Settings: Working")
    
    print("\n🚀 Phase 1.3 Core Agent Implementation is ready!")
    print("Next steps:")
    print("1. Set up OpenAI API key in .env for real testing")
    print("2. Implement Phase 1.4 Scheduling Advisor")
    print("3. Build Phase 1.5 Streamlit UI")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 