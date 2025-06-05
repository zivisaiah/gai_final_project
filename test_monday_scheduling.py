#!/usr/bin/env python3
"""Test Monday scheduling flow end-to-end."""

import sys
sys.path.append('.')

from streamlit_app.streamlit_main import RecruitmentChatbot
from app.modules.utils.datetime_parser import parse_scheduling_intent
from datetime import datetime

def test_monday_scheduling_flow():
    """Test the complete Monday scheduling flow."""
    print("🔄 Testing complete Monday scheduling flow...\n")
    
    # Test 1: DateTime parsing
    print("1️⃣ Testing datetime parsing...")
    user_message = "I can do Mondays only"
    parsing_result = parse_scheduling_intent(user_message)
    
    print(f"   Message: '{user_message}'")
    print(f"   Has scheduling intent: {parsing_result['has_scheduling_intent']}")
    print(f"   Confidence: {parsing_result['confidence']}")
    print(f"   Parsed datetimes: {len(parsing_result['parsed_datetimes'])}")
    
    for i, dt in enumerate(parsing_result['parsed_datetimes'], 1):
        dt_obj = dt['datetime']
        weekday = dt_obj.strftime('%A')
        print(f"     {i}. {dt_obj.strftime('%Y-%m-%d %H:%M')} ({weekday}) - {dt['interpretation']}")
    
    if parsing_result['has_scheduling_intent']:
        print("   ✅ Datetime parsing works!")
    else:
        print("   ❌ Datetime parsing failed!")
        return False
    
    # Test 2: Chatbot scheduling decision
    print("\n2️⃣ Testing chatbot scheduling decision...")
    chatbot = RecruitmentChatbot()
    
    # CRITICAL: Set up the core agent's conversation state FIRST
    conversation_state = chatbot.core_agent.get_or_create_conversation("streamlit_session")
    conversation_state.candidate_info = {
        'name': 'Ziv',
        'experience': 'mentioned',
        'interest_level': 'high',
        'availability_mentioned': True,
        'email': 'ziv@example.com',
        'phone': '+1234567890'
    }
    
    # Also update the Streamlit session state for consistency
    chatbot.chat_interface.update_candidate_info({
        'name': 'Ziv',
        'experience': 'mentioned',
        'interest_level': 'high',
        'email': 'ziv@example.com',
        'phone': '+1234567890'
    })
    
    print(f"   Candidate info set: {conversation_state.candidate_info}")
    
    # Verify the conversation state is preserved
    print(f"   Conversation ID: {conversation_state.conversation_id}")
    print(f"   Conversations in core agent: {list(chatbot.core_agent.conversations.keys())}")
    
    # Test the scheduling advisor's time preference parsing
    print(f"\n🔍 Testing scheduling advisor time preference parsing...")
    time_prefs = chatbot.scheduling_advisor.parse_candidate_time_preference(user_message)
    print(f"   Time preferences: {time_prefs}")
    
    # Process the Monday message
    result = chatbot.process_user_message(user_message)
    
    # Check conversation state after processing
    post_conversation_state = chatbot.core_agent.get_or_create_conversation("streamlit_session")
    print(f"   Post-processing candidate info: {post_conversation_state.candidate_info}")
    print(f"   Same conversation object? {conversation_state is post_conversation_state}")
    
    print(f"   Response success: {result['success']}")
    print(f"   Decision: {result['metadata'].get('decision')}")
    print(f"   Agent type: {result['metadata'].get('agent_type')}")
    
    # Check if scheduling was triggered
    has_slots = 'suggested_slots' in result['metadata'] and result['metadata']['suggested_slots']
    print(f"   Has suggested slots: {has_slots}")
    
    if has_slots:
        slots = result['metadata']['suggested_slots']
        print(f"   Number of slots: {len(slots)}")
        
        # Check if slots are Monday slots
        monday_slots = 0
        for slot in slots:
            if hasattr(slot, 'slot_date'):
                slot_date = slot.slot_date
                weekday = slot_date.strftime('%A')
                print(f"     Slot: {slot_date} {slot.start_time} ({weekday}) - {slot.recruiter.name}")
                if weekday == 'Monday':
                    monday_slots += 1
            else:
                # Handle dict format
                dt = datetime.fromisoformat(slot['datetime'].replace('Z', '+00:00'))
                weekday = dt.strftime('%A')
                print(f"     Slot: {dt.strftime('%Y-%m-%d %H:%M')} ({weekday}) - {slot.get('recruiter', 'N/A')}")
                if weekday == 'Monday':
                    monday_slots += 1
        
        print(f"   Monday slots offered: {monday_slots}/{len(slots)}")
        
        if monday_slots > 0:
            print("   ✅ Monday slots are being offered!")
            return True
        else:
            print("   ❌ No Monday slots offered - still showing wrong days!")
            return False
    else:
        print("   ❌ No slots suggested - scheduling decision failed!")
        return False

if __name__ == "__main__":
    success = test_monday_scheduling_flow()
    print(f"\n🎯 Overall test result: {'✅ PASS' if success else '❌ FAIL'}")
    if success:
        print("The Monday scheduling issue has been fixed!")
    else:
        print("The Monday scheduling issue still exists.") 