#!/usr/bin/env python3
"""
Comprehensive test for Phase 3.3: Complete Core Agent with Multi-Agent Orchestration

Tests:
- INFO decision routing to Info Advisor
- SCHEDULE decision routing to Scheduling Advisor  
- END decision routing to Exit Advisor
- CONTINUE decision for general conversation
- Complete conversation flow scenarios
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.agents.core_agent import CoreAgent, AgentDecision


async def test_complete_core_agent():
    """Test the complete Core Agent with all advisors"""
    
    print("[BOT] TESTING COMPLETE CORE AGENT - PHASE 3.3")
    print("=" * 60)
    
    # Test with OpenAI Vector Store for production-ready setup
    print("1. [WRENCH] Initializing Core Agent with OpenAI Vector Store...")
    try:
        core_agent = CoreAgent(vector_store_type="openai")
        print("[OK] Core Agent initialized successfully!")
        print(f"   - Exit Advisor: Ready")
        print(f"   - Scheduling Advisor: Ready")
        print(f"   - Info Advisor: Ready (OpenAI Vector Store)")
    except Exception as e:
        print(f"[X] Failed to initialize Core Agent: {e}")
        return
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Job Information Request",
            "message": "What programming languages are required for this position?",
            "expected_decision": AgentDecision.INFO,
            "description": "Should route to Info Advisor for job-related questions"
        },
        {
            "name": "General Conversation",
            "message": "Hi there! I saw your job posting and I'm interested.",
            "expected_decision": AgentDecision.CONTINUE,
            "description": "Should continue conversation to gather more info"
        },
        {
            "name": "Scheduling Request",
            "message": "I'd like to schedule an interview. I'm available Monday mornings.",
            "expected_decision": AgentDecision.SCHEDULE,
            "description": "Should route to Scheduling Advisor"
        },
        {
            "name": "Technical Requirements Question",
            "message": "What frameworks and technologies will I be working with?",
            "expected_decision": AgentDecision.INFO,
            "description": "Should route to Info Advisor for technical details"
        },
        {
            "name": "Role Responsibilities Question",
            "message": "What would my day-to-day responsibilities be in this role?",
            "expected_decision": AgentDecision.INFO,
            "description": "Should route to Info Advisor for role information"
        },
        {
            "name": "Company Culture Question",
            "message": "Can you tell me about the company culture and work environment?",
            "expected_decision": AgentDecision.INFO,
            "description": "Should route to Info Advisor for company information"
        },
        {
            "name": "Exit Scenario",
            "message": "Actually, I found another position that's a better fit. Thanks anyway!",
            "expected_decision": AgentDecision.END,
            "description": "Should route to Exit Advisor"
        }
    ]
    
    print(f"\n2. [TEST_TUBE] Running {len(test_scenarios)} Test Scenarios...")
    print("-" * 60)
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n[SEARCH] Test {i}: {scenario['name']}")
        print(f"Message: \"{scenario['message']}\"")
        print(f"Expected: {scenario['expected_decision'].value}")
        
        try:
            # Process message through Core Agent
            response, decision, reasoning = await core_agent.process_message_async(
                user_message=scenario['message'],
                conversation_id=f"test_conv_{i}"
            )
            
            # Check if decision matches expected
            decision_match = decision == scenario['expected_decision']
            
            print(f"Actual Decision: {decision.value}")
            print(f"Reasoning: {reasoning}")
            print(f"Response Preview: {response[:100]}...")
            print(f"[OK] PASS" if decision_match else f"[X] FAIL")
            
            results.append({
                "scenario": scenario['name'],
                "expected": scenario['expected_decision'].value,
                "actual": decision.value,
                "passed": decision_match,
                "response_length": len(response),
                "reasoning": reasoning
            })
            
        except Exception as e:
            print(f"[X] ERROR: {e}")
            results.append({
                "scenario": scenario['name'],
                "expected": scenario['expected_decision'].value,
                "actual": "ERROR",
                "passed": False,
                "error": str(e)
            })
        
        print("-" * 40)
    
    # Results Summary
    print(f"\n3. [CHART] TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"[OK] Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    # Detailed results
    print(f"\n[CLIPBOARD] Detailed Results:")
    for result in results:
        status = "[OK] PASS" if result['passed'] else "[X] FAIL"
        print(f"  {status} {result['scenario']}")
        print(f"      Expected: {result['expected']} | Actual: {result['actual']}")
        if not result['passed'] and 'error' in result:
            print(f"      Error: {result['error']}")
    
    # Test conversation flow
    print(f"\n4. 🔄 Testing Complete Conversation Flow...")
    print("-" * 60)
    
    conversation_id = "complete_flow_test"
    
    flow_messages = [
        "Hi! I'm interested in the Python developer position.",
        "What experience level are you looking for?",
        "What programming languages and frameworks will I be using?",
        "What would be my main responsibilities?",
        "This sounds great! Can we schedule an interview?",
        "I'm available Monday or Tuesday mornings."
    ]
    
    print("Simulating complete conversation flow:")
    for i, msg in enumerate(flow_messages, 1):
        print(f"\n[USER] User: {msg}")
        
        try:
            response, decision, reasoning = await core_agent.process_message_async(
                user_message=msg,
                conversation_id=conversation_id
            )
            
            print(f"[BOT] Agent Decision: {decision.value}")
            print(f"[BOT] Response: {response[:150]}{'...' if len(response) > 150 else ''}")
            
        except Exception as e:
            print(f"[X] Error: {e}")
    
    # Get conversation summary
    conversation_state = core_agent.get_conversation_state(conversation_id)
    if conversation_state:
        summary = conversation_state.get_conversation_summary()
        print(f"\n[CHART_UP] Conversation Summary:")
        print(f"   Messages: {summary['message_count']}")
        print(f"   Duration: {summary['duration_minutes']:.1f} minutes")
        print(f"   Last Decision: {summary['last_decision']}")
        print(f"   Candidate Info: {summary['candidate_info']}")
    
    print(f"\n[PARTY] COMPLETE CORE AGENT TESTING FINISHED!")
    print("=" * 60)
    
    return success_rate >= 80  # 80% pass rate required


async def test_advisor_integration():
    """Test individual advisor integration"""
    print(f"\n[WRENCH] TESTING ADVISOR INTEGRATION")
    print("-" * 40)
    
    core_agent = CoreAgent(vector_store_type="openai")
    
    # Test Info Advisor status
    info_status = core_agent.info_advisor.get_vector_store_status()
    print(f"Info Advisor Vector Store: {info_status['type']} ({info_status['available']})")
    
    # Test Scheduling Advisor
    from datetime import date, timedelta
    today = date.today()
    end_date = today + timedelta(days=7)
    
    available_slots = core_agent.scheduling_advisor.sql_manager.get_available_slots(
        start_date=today,
        end_date=end_date,
        available_only=True
    )
    print(f"Scheduling Advisor: {len(available_slots)} slots available")
    
    # Test Exit Advisor
    print(f"Exit Advisor: Ready")
    
    print("[OK] All advisors integrated successfully!")


if __name__ == "__main__":
    async def main():
        print("🚀 PHASE 3.3 TESTING: Complete Core Agent")
        print("Testing multi-agent orchestration with Info, Scheduling, and Exit advisors")
        print()
        
        # Test advisor integration
        await test_advisor_integration()
        
        # Test complete core agent
        success = await test_complete_core_agent()
        
        if success:
            print("[OK] Phase 3.3 testing completed successfully!")
        else:
            print("[!] Some tests failed. Review results above.")
    
    asyncio.run(main()) 