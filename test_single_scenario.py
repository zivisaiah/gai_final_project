#!/usr/bin/env python3
"""
Debug single scenario to see LLM response format.
"""

import sys
sys.path.append('.')

from app.modules.agents.scheduling_advisor import SchedulingAdvisor, SchedulingDecision
from datetime import datetime

def test_single_scenario():
    """Test a single scenario to debug the response format."""
    print("🔍 Testing Single Scenario for Debugging\n")
    
    advisor = SchedulingAdvisor()
    
    candidate_info = {"name": "Alice", "experience": "5 years Python", "interest_level": "high"}
    conversation_messages = [
        {"role": "user", "content": "Hi, I'm interested in the Python developer position"},
        {"role": "assistant", "content": "Great! Tell me about your experience"},
        {"role": "user", "content": "I have 5 years of Python experience"}
    ]
    latest_message = "I can do Mondays only"
    
    try:
        # Get all available slots first
        reference_dt = datetime.now()
        available_slots = advisor._get_all_available_slots(reference_dt, 14)
        
        print(f"Found {len(available_slots)} available slots")
        
        # Generate the decision prompt
        decision_prompt = advisor.prompts.get_decision_prompt(
            candidate_info=candidate_info,
            latest_message=latest_message,
            message_count=len(conversation_messages),
            available_slots=available_slots,
            current_datetime=reference_dt
        )
        
        print("\n📝 Generated Prompt:")
        print("=" * 60)
        print(decision_prompt[:800] + "...")
        print("=" * 60)
        
        # Get LLM response
        response = advisor.scheduling_chain.invoke({"scheduling_input": decision_prompt})
        response_text = response.content
        
        print("\n🤖 Raw LLM Response:")
        print("=" * 60)
        print(response_text)
        print("=" * 60)
        
        # Try to parse it
        decision, reasoning, suggested_slots, response_message = advisor._parse_unified_response(
            response_text, available_slots
        )
        
        print("\n✅ Parsed Result:")
        print(f"Decision: {decision.value}")
        print(f"Reasoning: {reasoning}")
        print(f"Suggested Slots: {len(suggested_slots)}")
        print(f"Response: {response_message}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_scenario() 