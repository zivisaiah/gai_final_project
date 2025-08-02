"""
Simple Validation Test - No Unicode Characters
Tests the enhanced conversation flow without Unicode symbols
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation_testing.enhanced_simulation_engine import EnhancedSimulatedUser, EnhancedSmartMockAgent

def test_single_conversation(persona_id: str) -> Dict[str, Any]:
    """Test a single conversation with enhanced flow"""
    
    try:
        # Initialize enhanced components
        user = EnhancedSimulatedUser(persona_id)
        agent = EnhancedSmartMockAgent("TestAgent")
        
        # Get personalized greeting
        greeting = agent.get_personalized_greeting(persona_id)
        
        # First user response
        response1 = user.generate_response(greeting, {'conversation_log': []})
        
        # Agent processes first response
        agent_resp1, decision1, reasoning1 = agent.process_message(
            response1, "test_conv", conversation_length=1, persona_id=persona_id
        )
        
        # Check if conversation would continue
        conversation_log = [
            {'type': 'agent', 'message': greeting},
            {'type': 'user', 'message': response1},
            {'type': 'agent', 'message': agent_resp1, 'decision': decision1}
        ]
        
        would_continue = user.should_continue_conversation({'conversation_log': conversation_log})
        
        return {
            "persona_id": persona_id,
            "success": True,
            "greeting_length": len(greeting),
            "first_response_length": len(response1),
            "agent_decision": decision1,
            "would_continue": would_continue,
            "conversation_viable": decision1 != "END" and would_continue,
            "greeting_personalized": len(greeting) > 80
        }
        
    except Exception as e:
        return {
            "persona_id": persona_id,
            "success": False,
            "error": str(e)
        }

def main():
    """Run simple validation test"""
    
    print(">> Simple Enhanced Flow Validation")
    print("=" * 50)
    
    personas = ["eager_junior", "experienced_senior", "career_changer", "passive_candidate", "difficult_candidate"]
    
    results = []
    successful_tests = 0
    viable_conversations = 0
    
    for persona_id in personas:
        print(f"Testing {persona_id}...")
        
        result = test_single_conversation(persona_id)
        results.append(result)
        
        if result["success"]:
            successful_tests += 1
            print(f"  Greeting: {result['greeting_length']} chars (personalized: {result['greeting_personalized']})")
            print(f"  First response: {result['first_response_length']} chars")
            print(f"  Agent decision: {result['agent_decision']}")
            print(f"  Would continue: {result['would_continue']}")
            print(f"  Conversation viable: {result['conversation_viable']}")
            
            if result["conversation_viable"]:
                viable_conversations += 1
        else:
            print(f"  ERROR: {result['error']}")
        
        print()
    
    # Summary
    print("=" * 50)
    print(">> VALIDATION SUMMARY")
    print("=" * 50)
    
    print(f"Total personas tested: {len(personas)}")
    print(f"Successful tests: {successful_tests}")
    print(f"Viable conversations: {viable_conversations}")
    print(f"Success rate: {(successful_tests / len(personas)) * 100:.1f}%")
    print(f"Viability rate: {(viable_conversations / len(personas)) * 100:.1f}%")
    
    # Detailed analysis
    if successful_tests > 0:
        avg_greeting_length = sum(r.get('greeting_length', 0) for r in results if r['success']) / successful_tests
        avg_response_length = sum(r.get('first_response_length', 0) for r in results if r['success']) / successful_tests
        personalized_greetings = sum(1 for r in results if r.get('greeting_personalized', False))
        
        print(f"\nQuality Metrics:")
        print(f"  Average greeting length: {avg_greeting_length:.1f} chars")
        print(f"  Average first response length: {avg_response_length:.1f} chars")
        print(f"  Personalized greetings: {personalized_greetings}/{len(personas)}")
        
        # Decision analysis
        decisions = [r.get('agent_decision') for r in results if r['success']]
        decision_counts = {}
        for decision in decisions:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
        
        print(f"\nAgent Decisions:")
        for decision, count in decision_counts.items():
            print(f"  {decision}: {count}")
    
    # Assessment
    print(f"\n>> ASSESSMENT:")
    
    if viable_conversations >= 4:
        print("EXCELLENT: Enhanced flow working very well!")
        print("- Most personas have viable conversation starts")
        print("- Ready for broader testing")
    elif viable_conversations >= 3:
        print("GOOD: Enhanced flow shows significant improvement")
        print("- Most conversations are viable")
        print("- Consider deployment with monitoring")
    elif viable_conversations >= 2:
        print("MODERATE: Some improvement detected")
        print("- About half of conversations are viable")
        print("- Continue refinement")
    else:
        print("POOR: Enhanced flow needs more work")
        print("- Most conversations not viable")
        print("- Additional fixes required")
    
    # Specific recommendations
    print(f"\n>> NEXT STEPS:")
    
    if viable_conversations >= 3:
        print("1. Enhanced conversation flow fixes are working")
        print("2. Mark Phase 3A tasks as completed")
        print("3. Consider implementing enhanced flow as default")
    else:
        print("1. Continue debugging agent decision logic")
        print("2. Review persona behavior patterns")
        print("3. Investigate remaining conversation flow issues")
    
    return results

if __name__ == "__main__":
    main()