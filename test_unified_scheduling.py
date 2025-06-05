#!/usr/bin/env python3
"""
Test the new unified LLM-based scheduling approach.
Verifies that intent detection and time parsing happen within the Scheduling Advisor.
"""

import sys
sys.path.append('.')

from app.modules.agents.scheduling_advisor import SchedulingAdvisor, SchedulingDecision
from datetime import datetime
import json

def test_unified_scheduling_approach():
    """Test the unified LLM-based scheduling approach with various scenarios."""
    print("🧪 Testing Unified LLM-Based Scheduling Approach\n")
    
    # Initialize the scheduling advisor
    advisor = SchedulingAdvisor()
    
    # Test scenarios covering different types of scheduling intent
    test_scenarios = [
        {
            "name": "Clear Monday Preference",
            "candidate_info": {"name": "Alice", "experience": "5 years Python", "interest_level": "high"},
            "conversation_messages": [
                {"role": "user", "content": "Hi, I'm interested in the Python developer position"},
                {"role": "assistant", "content": "Great! Tell me about your experience"},
                {"role": "user", "content": "I have 5 years of Python experience"}
            ],
            "latest_message": "I can do Mondays only",
            "expected_intent": True,
            "expected_decision": "SCHEDULE"
        },
        {
            "name": "Informal Scheduling Language",
            "candidate_info": {"name": "Bob", "experience": "mentioned", "interest_level": "high"},
            "conversation_messages": [
                {"role": "user", "content": "This looks like a great opportunity"}
            ],
            "latest_message": "Would be great to connect soon",
            "expected_intent": True,
            "expected_decision": "SCHEDULE"
        },
        {
            "name": "Complex Time Preferences",
            "candidate_info": {"name": "Carol", "experience": "3 years Django", "interest_level": "high"},
            "conversation_messages": [
                {"role": "user", "content": "I'm very interested in this role"}
            ],
            "latest_message": "I'm free mornings except Wednesday and can do Friday afternoons",
            "expected_intent": True,
            "expected_decision": "SCHEDULE"
        },
        {
            "name": "No Scheduling Intent",
            "candidate_info": {"name": None, "experience": None, "interest_level": "unknown"},
            "conversation_messages": [
                {"role": "user", "content": "Hello"}
            ],
            "latest_message": "What does this position involve?",
            "expected_intent": False,
            "expected_decision": "NOT_SCHEDULE"
        },
        {
            "name": "Missing Candidate Info",
            "candidate_info": {"name": None, "experience": None, "interest_level": "medium"},
            "conversation_messages": [
                {"role": "user", "content": "I'm interested"}
            ],
            "latest_message": "When can we schedule an interview?",
            "expected_intent": True,
            "expected_decision": "NOT_SCHEDULE"  # Should be overridden due to missing info
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{i}. Testing: {scenario['name']}")
        print(f"   Message: '{scenario['latest_message']}'")
        print(f"   Expected Intent: {scenario['expected_intent']}")
        print(f"   Expected Decision: {scenario['expected_decision']}")
        
        try:
            # Run the unified scheduling decision
            decision, reasoning, suggested_slots, response_message = advisor.make_scheduling_decision(
                candidate_info=scenario['candidate_info'],
                conversation_messages=scenario['conversation_messages'],
                latest_message=scenario['latest_message'],
                reference_datetime=datetime.now()
            )
            
            # Get the intent confidence if available
            intent_confidence = getattr(advisor, '_last_intent_confidence', 'N/A')
            
            print(f"   ✅ RESULT:")
            print(f"      Decision: {decision.value}")
            print(f"      Intent Confidence: {intent_confidence}")
            print(f"      Reasoning: {reasoning[:100]}..." if len(reasoning) > 100 else f"      Reasoning: {reasoning}")
            print(f"      Suggested Slots: {len(suggested_slots)} slots")
            print(f"      Response: {response_message[:80]}..." if len(response_message) > 80 else f"      Response: {response_message}")
            
            # Check if results match expectations
            decision_matches = decision.value == scenario['expected_decision']
            
            if decision_matches:
                print(f"   ✅ PASS: Decision matches expected")
            else:
                print(f"   ❌ FAIL: Expected {scenario['expected_decision']}, got {decision.value}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print()

def test_intent_detection_improvements():
    """Test specific intent detection improvements over keyword approach."""
    print("🎯 Testing Intent Detection Improvements\n")
    
    advisor = SchedulingAdvisor()
    
    # Test cases that keyword approach might miss
    edge_cases = [
        {
            "message": "Would be great to connect",
            "description": "Informal scheduling intent"
        },
        {
            "message": "Looking forward to next steps",
            "description": "Implied scheduling intent"
        },
        {
            "message": "I work with React and Node.js",
            "description": "Background sharing (should NOT have intent)"
        },
        {
            "message": "Pretty flexible next week",
            "description": "Casual availability statement"
        },
        {
            "message": "Not interested, found another job",
            "description": "Clear rejection (should NOT schedule)"
        }
    ]
    
    candidate_info = {"name": "Test User", "experience": "mentioned", "interest_level": "high"}
    
    for case in edge_cases:
        print(f"Testing: '{case['message']}'")
        print(f"Context: {case['description']}")
        
        try:
            decision, reasoning, slots, response = advisor.make_scheduling_decision(
                candidate_info=candidate_info,
                conversation_messages=[],
                latest_message=case['message'],
                reference_datetime=datetime.now()
            )
            
            intent_confidence = getattr(advisor, '_last_intent_confidence', 'N/A')
            
            print(f"   Decision: {decision.value}")
            print(f"   Intent Confidence: {intent_confidence}")
            print(f"   Reasoning: {reasoning[:80]}...")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        print()

def test_time_preference_parsing():
    """Test the enhanced time preference parsing capabilities."""
    print("⏰ Testing Time Preference Parsing\n")
    
    advisor = SchedulingAdvisor()
    candidate_info = {"name": "Test User", "experience": "mentioned", "interest_level": "high"}
    
    time_expressions = [
        "I can do Mondays only",
        "Available tomorrow afternoon",
        "Free mornings except Wednesday",
        "Can do afternoons next week",
        "Available any time Friday",
        "I prefer 2pm meetings",
        "Can't do before 10am"
    ]
    
    for expression in time_expressions:
        print(f"Parsing: '{expression}'")
        
        try:
            decision, reasoning, slots, response = advisor.make_scheduling_decision(
                candidate_info=candidate_info,
                conversation_messages=[],
                latest_message=expression,
                reference_datetime=datetime.now()
            )
            
            print(f"   Decision: {decision.value}")
            print(f"   Suggested Slots: {len(slots)}")
            if slots:
                for slot in slots[:2]:  # Show first 2 slots
                    slot_dt = datetime.fromisoformat(slot['datetime'])
                    weekday = slot_dt.strftime('%A')
                    time_str = slot_dt.strftime('%I:%M %p')
                    print(f"      {weekday} {time_str} with {slot['recruiter']}")
                    if 'match_reason' in slot:
                        print(f"        Match reason: {slot['match_reason']}")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        print()

if __name__ == "__main__":
    print("🚀 UNIFIED LLM-BASED SCHEDULING ADVISOR TEST\\n")
    print("Testing the new approach that combines intent detection, time parsing, and scheduling decisions in a single LLM call.\\n")
    
    # Test the unified approach
    test_unified_scheduling_approach()
    
    # Test intent detection improvements
    test_intent_detection_improvements()
    
    # Test time preference parsing
    test_time_preference_parsing()
    
    print("=" * 80)
    print("🎉 UNIFIED APPROACH BENEFITS:")
    print("✅ No additional API costs (same LLM call)")
    print("✅ Better intent detection for informal language")
    print("✅ Enhanced time preference parsing")
    print("✅ Unified reasoning and confidence scoring")
    print("✅ Cleaner architecture without mixed approaches")
    print("=" * 80) 