"""
Quick Fix Validation Test
Tests that the enhanced conversation flow fixes are working
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation_testing.enhanced_simulation_engine import EnhancedSimulatedUser, EnhancedSmartMockAgent
from simulation_testing.simulation_engine import SimulatedUser
from simulation_testing.agents.smart_mock_agent import SmartMockAgent

def test_enhanced_vs_original_first_exchange(persona_id: str) -> Dict[str, Any]:
    """Test enhanced vs original flow for first exchange only"""
    
    results = {
        "persona_id": persona_id,
        "original": {},
        "enhanced": {},
        "improvement": {}
    }
    
    print(f"Testing {persona_id}:")
    
    # Test original flow
    try:
        original_user = SimulatedUser(persona_id)
        original_agent = SmartMockAgent("OriginalAgent")
        
        original_greeting = "Hello! Thank you for your interest in our Python developer position. Could you tell me a bit about yourself and your experience?"
        original_response = original_user.generate_response(original_greeting, {'conversation_log': []})
        
        agent_response, decision, reasoning = original_agent.process_message(original_response, f"test_{persona_id}")
        
        results["original"] = {
            "user_response_length": len(original_response),
            "agent_decision": decision,
            "conversation_continues": decision != "END",
            "first_response": original_response[:100] + "..." if len(original_response) > 100 else original_response
        }
        
        print(f"  Original: {len(original_response)} chars, decision: {decision}")
        
    except Exception as e:
        results["original"] = {"error": str(e)}
        print(f"  Original: ERROR - {e}")
    
    # Test enhanced flow
    try:
        enhanced_user = EnhancedSimulatedUser(persona_id)
        enhanced_agent = EnhancedSmartMockAgent("EnhancedAgent")
        
        enhanced_greeting = enhanced_agent.get_personalized_greeting(persona_id)
        enhanced_response = enhanced_user.generate_response(enhanced_greeting, {'conversation_log': []})
        
        agent_response, decision, reasoning = enhanced_agent.process_message(
            enhanced_response, f"test_{persona_id}", conversation_length=1, persona_id=persona_id
        )
        
        results["enhanced"] = {
            "user_response_length": len(enhanced_response),
            "agent_decision": decision,
            "conversation_continues": decision != "END",
            "personalized_greeting": len(enhanced_greeting) > 80,  # Check if greeting is personalized
            "first_response": enhanced_response[:100] + "..." if len(enhanced_response) > 100 else enhanced_response
        }
        
        print(f"  Enhanced: {len(enhanced_response)} chars, decision: {decision}")
        
    except Exception as e:
        results["enhanced"] = {"error": str(e)}
        print(f"  Enhanced: ERROR - {e}")
    
    # Calculate improvements
    if "error" not in results["original"] and "error" not in results["enhanced"]:
        results["improvement"] = {
            "response_length_increase": results["enhanced"]["user_response_length"] - results["original"]["user_response_length"],
            "better_decision": results["enhanced"]["conversation_continues"] and not results["original"]["conversation_continues"],
            "personalized_greeting": results["enhanced"]["personalized_greeting"]
        }
        
        improvement_score = 0
        if results["improvement"]["response_length_increase"] > 20:
            improvement_score += 1
        if results["improvement"]["better_decision"]:
            improvement_score += 2
        if results["improvement"]["personalized_greeting"]:
            improvement_score += 1
            
        results["improvement"]["score"] = improvement_score
        
        print(f"  Improvement: +{results['improvement']['response_length_increase']} chars, score: {improvement_score}/4")
    else:
        results["improvement"] = {"score": 0}
        print(f"  Improvement: Cannot calculate due to errors")
    
    return results

def main():
    """Run quick fix validation"""
    print(">> Quick Fix Validation Test")
    print("=" * 50)
    
    personas_to_test = ["eager_junior", "experienced_senior", "career_changer", "passive_candidate", "difficult_candidate"]
    
    all_results = []
    total_improvement_score = 0
    
    for persona_id in personas_to_test:
        result = test_enhanced_vs_original_first_exchange(persona_id)
        all_results.append(result)
        total_improvement_score += result["improvement"]["score"]
        print()
    
    # Summary
    print("=" * 50)
    print(">> VALIDATION SUMMARY")
    print(f"Total personas tested: {len(personas_to_test)}")
    print(f"Total improvement score: {total_improvement_score}/{len(personas_to_test) * 4}")
    
    avg_improvement = total_improvement_score / len(personas_to_test)
    
    if avg_improvement >= 3.0:
        print(">> EXCELLENT: Significant improvements detected!")
        print("   Enhanced flow is working well")
    elif avg_improvement >= 2.0:
        print(">> GOOD: Moderate improvements detected")
        print("   Enhanced flow shows promise")
    elif avg_improvement >= 1.0:
        print(">> MINIMAL: Some improvements detected")
        print("   Additional fixes may be needed")
    else:
        print(">> POOR: Limited or no improvements")
        print("   Enhanced flow needs more work")
    
    print("\n>> Key Improvements:")
    improvements_found = []
    
    for result in all_results:
        if "error" not in result["original"] and "error" not in result["enhanced"]:
            persona = result["persona_id"]
            score = result["improvement"]["score"]
            
            if score >= 3:
                improvements_found.append(f"   - {persona}: Excellent improvement (score {score}/4)")
            elif score >= 2:
                improvements_found.append(f"   - {persona}: Good improvement (score {score}/4)")
            elif score >= 1:
                improvements_found.append(f"   - {persona}: Some improvement (score {score}/4)")
    
    if improvements_found:
        for improvement in improvements_found:
            print(improvement)
    else:
        print("   - No significant improvements detected")
    
    print(f"\n>> Next Steps:")
    if avg_improvement >= 2.0:
        print("   1. Enhanced flow is ready for broader testing")
        print("   2. Consider implementing enhanced flow as default")
        print("   3. Monitor performance in full validation tests")
    else:
        print("   1. Continue debugging agent decision logic")
        print("   2. Review persona response generation")
        print("   3. Investigate remaining conversation flow issues")

if __name__ == "__main__":
    main()