#!/usr/bin/env python3
"""Debug the validation logic to see what's happening."""

import sys
sys.path.append('.')

from streamlit_app.streamlit_main import RecruitmentChatbot
from app.modules.agents.core_agent import AgentDecision

def test_validation_debug():
    """Debug the validation logic step by step."""
    print("🔍 Debugging validation logic...")
    
    chatbot = RecruitmentChatbot()
    
    # Set up candidate info correctly
    conversation_state = chatbot.core_agent.get_or_create_conversation("test_session")
    conversation_state.candidate_info = {
        'name': 'Ziv',
        'experience': 'mentioned',
        'interest_level': 'high',
        'availability_mentioned': True
    }
    
    print(f"📊 Candidate info: {conversation_state.candidate_info}")
    
    # Manually test the validation conditions
    candidate_info = conversation_state.candidate_info
    
    # Test condition 1: Override to SCHEDULE
    condition1 = (
        candidate_info.get("name") and 
        candidate_info.get("experience") == "mentioned" and
        candidate_info.get("interest_level") == "high" and
        candidate_info.get("availability_mentioned")
    )
    print(f"✅ Override CONTINUE to SCHEDULE condition: {condition1}")
    print(f"   - name: {candidate_info.get('name')}")
    print(f"   - experience == 'mentioned': {candidate_info.get('experience') == 'mentioned'}")
    print(f"   - interest_level == 'high': {candidate_info.get('interest_level') == 'high'}")
    print(f"   - availability_mentioned: {candidate_info.get('availability_mentioned')}")
    
    # Test condition 2: Override to CONTINUE
    condition2 = (
        not candidate_info.get("name") and
        candidate_info.get("interest_level") != "high"
    )
    print(f"❌ Override SCHEDULE to CONTINUE condition: {condition2}")
    print(f"   - NOT name: {not candidate_info.get('name')}")
    print(f"   - interest_level != 'high': {candidate_info.get('interest_level') != 'high'}")
    
    # Test the validation function directly
    print(f"\n🧪 Testing validation function...")
    
    # Test with CONTINUE decision (should become SCHEDULE)
    decision_continue = chatbot.core_agent._validate_decision(AgentDecision.CONTINUE, conversation_state)
    print(f"   CONTINUE -> {decision_continue.value}")
    
    # Test with SCHEDULE decision (should stay SCHEDULE)
    decision_schedule = chatbot.core_agent._validate_decision(AgentDecision.SCHEDULE, conversation_state)
    print(f"   SCHEDULE -> {decision_schedule.value}")
    
    # Now test the complete flow
    print(f"\n🔄 Testing complete flow...")
    user_message = "I can do Mondays only"
    
    # Test the make_decision method directly
    decision, reasoning, response = chatbot.core_agent._make_decision(user_message, conversation_state)
    print(f"   Final decision: {decision.value}")
    print(f"   Reasoning: {reasoning}")

if __name__ == "__main__":
    test_validation_debug() 