"""
END Decision Tester
Test scenarios that might trigger inappropriate END decisions
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

def test_end_decision_scenarios() -> Dict[str, Any]:
    """Test scenarios that might trigger END decisions"""
    
    # Scenarios designed to potentially trigger END decisions
    test_cases = [
        {
            "category": "short_responses",
            "scenarios": [
                "Hi",
                "Yes",
                "Ok",
                "Sure",
                "Thanks"
            ]
        },
        {
            "category": "ambiguous_responses", 
            "scenarios": [
                "I'm not sure",
                "Maybe",
                "I'll think about it",
                "Hmm",
                "That's interesting"
            ]
        },
        {
            "category": "neutral_responses",
            "scenarios": [
                "Tell me more",
                "What else?", 
                "I see",
                "Okay, go on",
                "And?"
            ]
        },
        {
            "category": "legitimate_rejections",
            "scenarios": [
                "I'm not interested",
                "No thank you",
                "This isn't right for me",
                "I changed my mind",
                "I found another opportunity"
            ]
        }
    ]
    
    results = {
        "original_agent_results": {},
        "enhanced_agent_results": {},
        "improvements": {},
        "summary": {}
    }
    
    original_agent = SmartMockAgent("OriginalAgent")
    enhanced_agent = EnhancedSmartMockAgent("EnhancedAgent")
    
    print(">> Testing END Decision Scenarios")
    print("=" * 50)
    
    for test_case in test_cases:
        category = test_case["category"]
        scenarios = test_case["scenarios"]
        
        print(f"\n>> Testing {category}:")
        
        original_results = []
        enhanced_results = []
        
        for i, scenario in enumerate(scenarios):
            print(f"   Scenario: '{scenario}'")
            
            # Test original agent
            try:
                orig_response, orig_decision, orig_reasoning = original_agent.process_message(scenario, f"test_{i}")
                original_results.append({
                    "scenario": scenario,
                    "decision": orig_decision,
                    "reasoning": orig_reasoning
                })
                print(f"     Original: {orig_decision}")
            except Exception as e:
                original_results.append({"scenario": scenario, "error": str(e)})
                print(f"     Original: ERROR - {e}")
            
            # Test enhanced agent (early conversation)
            try:
                enh_response, enh_decision, enh_reasoning = enhanced_agent.process_message(
                    scenario, f"test_{i}", conversation_length=1, persona_id="eager_junior"
                )
                enhanced_results.append({
                    "scenario": scenario,
                    "decision": enh_decision,
                    "reasoning": enh_reasoning
                })
                print(f"     Enhanced: {enh_decision}")
            except Exception as e:
                enhanced_results.append({"scenario": scenario, "error": str(e)})
                print(f"     Enhanced: ERROR - {e}")
        
        results["original_agent_results"][category] = original_results
        results["enhanced_agent_results"][category] = enhanced_results
        
        # Analyze improvements for this category
        category_improvements = {
            "inappropriate_ends_prevented": 0,
            "appropriate_ends_maintained": 0,
            "decision_changes": 0
        }
        
        for i in range(len(scenarios)):
            if (i < len(original_results) and i < len(enhanced_results) and
                "error" not in original_results[i] and "error" not in enhanced_results[i]):
                
                orig_decision = original_results[i]["decision"]
                enh_decision = enhanced_results[i]["decision"]
                
                if orig_decision != enh_decision:
                    category_improvements["decision_changes"] += 1
                
                # For legitimate rejections, END is appropriate
                if category == "legitimate_rejections":
                    if orig_decision == "END" and enh_decision == "END":
                        category_improvements["appropriate_ends_maintained"] += 1
                else:
                    # For other categories, preventing END might be good
                    if orig_decision == "END" and enh_decision != "END":
                        category_improvements["inappropriate_ends_prevented"] += 1
        
        results["improvements"][category] = category_improvements
    
    # Generate summary
    total_inappropriate_ends_prevented = sum(
        results["improvements"][cat]["inappropriate_ends_prevented"] 
        for cat in results["improvements"] if cat != "legitimate_rejections"
    )
    
    total_appropriate_ends_maintained = results["improvements"].get("legitimate_rejections", {}).get("appropriate_ends_maintained", 0)
    
    total_decision_changes = sum(
        results["improvements"][cat]["decision_changes"] 
        for cat in results["improvements"]
    )
    
    results["summary"] = {
        "total_inappropriate_ends_prevented": total_inappropriate_ends_prevented,
        "total_appropriate_ends_maintained": total_appropriate_ends_maintained,
        "total_decision_changes": total_decision_changes,
        "categories_tested": len(test_cases)
    }
    
    return results

def print_summary(results: Dict[str, Any]):
    """Print comprehensive summary of results"""
    
    summary = results["summary"]
    
    print("\n" + "=" * 60)
    print(">> END DECISION ANALYSIS SUMMARY")
    print("=" * 60)
    
    print(f"Categories tested: {summary['categories_tested']}")
    print(f"Inappropriate ENDs prevented: {summary['total_inappropriate_ends_prevented']}")
    print(f"Appropriate ENDs maintained: {summary['total_appropriate_ends_maintained']}")
    print(f"Total decision changes: {summary['total_decision_changes']}")
    
    # Detailed category analysis
    print(f"\n>> Category Breakdown:")
    for category, improvements in results["improvements"].items():
        print(f"   {category}:")
        print(f"     - Decision changes: {improvements['decision_changes']}")
        if category == "legitimate_rejections":
            print(f"     - Appropriate ENDs maintained: {improvements['appropriate_ends_maintained']}")
        else:
            print(f"     - Inappropriate ENDs prevented: {improvements['inappropriate_ends_prevented']}")
    
    # Overall assessment
    print(f"\n>> Overall Assessment:")
    
    if summary["total_inappropriate_ends_prevented"] >= 3:
        print("   EXCELLENT: Enhanced agent preventing inappropriate END decisions")
    elif summary["total_inappropriate_ends_prevented"] >= 1:
        print("   GOOD: Some inappropriate END decisions prevented")
    else:
        print("   LIMITED: No inappropriate END decisions prevented")
    
    if summary["total_appropriate_ends_maintained"] >= 3:
        print("   EXCELLENT: Enhanced agent maintaining appropriate END decisions")
    elif summary["total_appropriate_ends_maintained"] >= 1:
        print("   GOOD: Some appropriate END decisions maintained") 
    else:
        print("   WARNING: May not be handling legitimate rejections properly")
    
    return summary

def main():
    """Main END decision testing entry point"""
    
    results = test_end_decision_scenarios()
    summary = print_summary(results)
    
    print(f"\n>> Fix Status Summary:")
    
    if (summary["total_inappropriate_ends_prevented"] >= 2 and 
        summary["total_appropriate_ends_maintained"] >= 2):
        print("   STATUS: Enhanced agent decision logic is working well")
        print("   RECOMMENDATION: Deploy enhanced agent")
    elif summary["total_inappropriate_ends_prevented"] >= 1:
        print("   STATUS: Enhanced agent shows some improvement")
        print("   RECOMMENDATION: Continue testing and refinement")
    else:
        print("   STATUS: Enhanced agent needs more work")
        print("   RECOMMENDATION: Additional decision logic fixes needed")

if __name__ == "__main__":
    main()