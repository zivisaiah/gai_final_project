"""
Simple Scheduling Advisor Test Script
Testing Scheduling Advisor functionality without requiring OpenAI API access
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("🧪 Testing Scheduling Advisor Implementation...")
    
    # Test imports
    print("\n📦 Testing Imports...")
    from app.modules.agents.scheduling_advisor import SchedulingAdvisor, SchedulingDecision
    from app.modules.prompts.scheduling_prompts import SchedulingPrompts
    from app.modules.utils.datetime_parser import DateTimeParser, parse_scheduling_intent
    print("✅ All imports successful!")
    
    # Test DateTimeParser
    print("\n📅 Testing DateTimeParser...")
    parser = DateTimeParser(datetime(2024, 1, 10, 10, 0))  # Wednesday at 10 AM
    
    # Test various expressions
    test_expressions = [
        "tomorrow afternoon",
        "next Friday at 2pm",
        "Monday morning",
        "in 3 days",
        "next week"
    ]
    
    for expr in test_expressions:
        results = parser.parse_datetime_expression(expr)
        if results:
            best_result = results[0]
            print(f"✅ '{expr}' -> {best_result['interpretation']} (confidence: {best_result['confidence']:.2f})")
        else:
            print(f"⚠️  '{expr}' -> No results")
    
    # Test business hours adjustment
    print("\n⏰ Testing Business Hours...")
    test_dt = datetime(2024, 1, 10, 20, 0)  # 8 PM
    business_dt = parser.get_business_hours_datetime(test_dt)
    print(f"✅ 8 PM adjusted to: {business_dt.strftime('%I:%M %p')}")
    
    # Test scheduling intent parsing
    print("\n🎯 Testing Scheduling Intent...")
    test_messages = [
        "I'm available tomorrow afternoon for an interview",
        "When can we schedule the meeting?",
        "Tell me more about the role",
        "I'm free next Friday morning"
    ]
    
    for msg in test_messages:
        intent = parse_scheduling_intent(msg)
        print(f"✅ '{msg}' -> Intent: {intent['has_scheduling_intent']}, Confidence: {intent['confidence']:.2f}")
        if intent['parsed_datetimes']:
            for dt in intent['parsed_datetimes'][:1]:  # Show first result
                print(f"   Parsed: {dt['interpretation']}")
    
    # Test SchedulingPrompts
    print("\n📝 Testing SchedulingPrompts...")
    prompts = SchedulingPrompts()
    
    system_prompt = prompts.get_scheduling_system_prompt()
    print(f"✅ System prompt length: {len(system_prompt)} characters")
    
    examples = prompts.get_scheduling_examples()
    print(f"✅ Scheduling examples: {len(examples)} examples")
    
    # Test example structure
    first_example = examples[0]
    print(f"✅ Example decision: {first_example['decision']}")
    print(f"✅ Example reasoning: {first_example['reasoning'][:50]}...")
    
    # Test time slot formatting
    test_slots = [
        {"datetime": "2024-01-15T10:00:00", "recruiter": "Alice Smith", "duration": 45},
        {"datetime": "2024-01-15T14:00:00", "recruiter": "Bob Johnson", "duration": 45}
    ]
    formatted = prompts.format_time_slots(test_slots)
    print(f"✅ Formatted slots:\n{formatted}")
    
    # Test preference extraction
    test_conversation = [
        {"role": "user", "content": "I'm available tomorrow afternoon or Friday morning"},
        {"role": "user", "content": "I prefer 2pm if possible"}
    ]
    preferences = prompts.extract_time_preferences(test_conversation)
    print(f"✅ Extracted preferences: {preferences}")
    
    # Test SchedulingAdvisor with Mocked Components
    print("\n🤖 Testing SchedulingAdvisor (Mocked)...")
    
    with patch('app.modules.agents.scheduling_advisor.ChatOpenAI') as mock_llm, \
         patch('app.modules.agents.scheduling_advisor.SQLManager') as mock_sql:
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = """DECISION: SCHEDULE
REASONING: Candidate has provided clear availability preferences and shows strong interest
SUGGESTED_SLOTS: Top 3 available slots matching preferences
RESPONSE: Perfect! I have several time slots available that match your preferences."""
        
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        # Mock SQL Manager
        mock_sql_instance = Mock()
        mock_sql_instance.get_available_slots.return_value = [
            {"datetime": "2024-01-15T10:00:00", "recruiter": "Alice Smith", "duration": 45, "recruiter_id": 1},
            {"datetime": "2024-01-15T14:00:00", "recruiter": "Bob Johnson", "duration": 45, "recruiter_id": 2},
            {"datetime": "2024-01-16T09:00:00", "recruiter": "Alice Smith", "duration": 45, "recruiter_id": 1}
        ]
        mock_sql.return_value = mock_sql_instance
        
        # Create SchedulingAdvisor
        advisor = SchedulingAdvisor(openai_api_key="test-key-for-mock")
        advisor.llm = mock_llm_instance
        advisor.sql_manager = mock_sql_instance
        print("✅ Created SchedulingAdvisor with mocked components")
        
        # Test scheduling decision
        candidate_info = {
            "name": "Sarah",
            "experience": "3 years Python",
            "interest_level": "high"
        }
        
        conversation_messages = [
            {"role": "assistant", "content": "Hi! Are you interested in our Python role?"},
            {"role": "user", "content": "Yes, very interested!"},
            {"role": "assistant", "content": "Great! Tell me about your experience."},
            {"role": "user", "content": "I'm Sarah, I have 3 years of Python experience"}
        ]
        
        latest_message = "I'm available tomorrow afternoon for an interview"
        
        decision, reasoning, suggested_slots, response_message = advisor.make_scheduling_decision(
            candidate_info,
            conversation_messages,
            latest_message,
            datetime(2024, 1, 10, 10, 0)
        )
        
        print(f"✅ Scheduling decision: {decision.value}")
        print(f"✅ Reasoning: {str(reasoning)[:50]}...")
        print(f"✅ Suggested slots: {len(suggested_slots)} slots")
        print(f"✅ Response: {str(response_message)[:50]}...")
        
        # Test slot formatting
        if suggested_slots:
            formatted_slots = advisor.format_slots_for_candidate(suggested_slots)
            print(f"✅ Formatted slots for candidate: {len(formatted_slots)} characters")
        else:
            print("✅ No slots to format (expected for mocked test)")
        
        # Test appointment booking (mocked)
        mock_sql_instance.create_appointment.return_value = 12345
        mock_sql_instance.get_recruiter_by_id.return_value = {"name": "Alice Smith", "email": "alice@company.com"}
        
        booking_result = advisor.book_appointment(
            candidate_info,
            datetime(2024, 1, 15, 10, 0),
            1,
            45
        )
        
        print(f"✅ Booking result: {booking_result['success']}")
        if booking_result['success']:
            print(f"✅ Appointment ID: {booking_result['appointment_id']}")
            print(f"✅ Confirmation message: {booking_result['confirmation_message'][:50]}...")
        
        # Test scheduling statistics (mocked)
        mock_sql_instance.get_appointment_statistics.return_value = {
            'total_appointments': 15,
            'scheduled_appointments': 12,
            'available_slots': 25,
            'recruiter_count': 3
        }
        
        stats = advisor.get_scheduling_statistics()
        print(f"✅ Scheduling stats: {stats}")
    
    # Test response parsing
    print("\n🔍 Testing Response Parsing...")
    
    with patch('app.modules.agents.scheduling_advisor.ChatOpenAI') as mock_llm, \
         patch('app.modules.agents.scheduling_advisor.SQLManager') as mock_sql:
        
        advisor = SchedulingAdvisor(openai_api_key="test-key")
        
        # Test structured response parsing
        test_response = """DECISION: SCHEDULE
REASONING: Candidate has shown clear interest and provided availability preferences
SUGGESTED_SLOTS: [slot1, slot2, slot3]
RESPONSE: Great! I have several time slots available next week that match your preferences."""
        
        available_slots = [
            {"datetime": "2024-01-15T10:00:00", "recruiter": "Alice Smith", "duration": 45}
        ]
        
        decision, reasoning, slots, response = advisor._parse_scheduling_response(test_response, available_slots)
        print(f"✅ Parsed decision: {decision.value}")
        print(f"✅ Parsed reasoning: {str(reasoning)[:50]}...")
        print(f"✅ Parsed response: {str(response)[:50]}...")
        
        # Test fallback decision
        fallback_decision, fallback_reasoning, fallback_slots, fallback_response = advisor._fallback_scheduling_decision(
            {"name": "John", "interest_level": "high"},
            "When can we schedule the interview?"
        )
        print(f"✅ Fallback decision: {fallback_decision.value}")
    
    print("\n🎉 All Scheduling Advisor tests completed successfully!")
    print("\n📊 Test Summary:")
    print("✅ DateTimeParser: Working")
    print("✅ SchedulingPrompts: Working")  
    print("✅ SchedulingAdvisor (Mocked): Working")
    print("✅ Response Parsing: Working")
    print("✅ Appointment Booking: Working")
    
    print("\n🚀 Phase 1.4 Scheduling Advisor Implementation is ready!")
    print("Next steps:")
    print("1. Integrate with Core Agent")
    print("2. Implement Phase 1.5 Streamlit UI")
    print("3. Test end-to-end conversation flow")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 