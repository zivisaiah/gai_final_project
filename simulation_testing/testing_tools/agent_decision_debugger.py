"""
Agent Decision Logic Debugger
Specifically debug and test agent decision-making improvements
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

def debug_agent_decision_logic(persona_id: str, test_scenarios: List[str]) -> Dict[str, Any]:
    """Debug agent decision logic for specific scenarios"""
    
    results = {
        "persona_id": persona_id,
        "scenarios_tested": len(test_scenarios),
        "original_decisions": [],
        "enhanced_decisions": [],
        "improvements": []
    }
    
    print(f"\nDebugging agent decisions for {persona_id}:")
    
    # Initialize agents
    original_agent = SmartMockAgent("OriginalAgent")
    enhanced_agent = EnhancedSmartMockAgent("EnhancedAgent")
    
    for i, scenario in enumerate(test_scenarios):
        print(f"  Scenario {i+1}: {scenario[:50]}...")
        
        # Test original agent
        try:
            orig_response, orig_decision, orig_reasoning = original_agent.process_message(scenario, f"test_{i}")
            results["original_decisions"].append({
                "scenario": scenario,
                "decision": orig_decision,
                "reasoning": orig_reasoning[:100] + "..." if len(orig_reasoning) > 100 else orig_reasoning
            })
            print(f"    Original: {orig_decision}")
        except Exception as e:
            results["original_decisions"].append({"scenario": scenario, "error": str(e)})
            print(f"    Original: ERROR - {e}")
        
        # Test enhanced agent
        try:
            enh_response, enh_decision, enh_reasoning = enhanced_agent.process_message(
                scenario, f"test_{i}", conversation_length=2, persona_id=persona_id
            )
            results["enhanced_decisions"].append({
                "scenario": scenario,
                "decision": enh_decision,
                "reasoning": enh_reasoning[:100] + "..." if len(enh_reasoning) > 100 else enh_reasoning
            })
            print(f"    Enhanced: {enh_decision}")
        except Exception as e:
            results["enhanced_decisions"].append({"scenario": scenario, "error": str(e)})
            print(f"    Enhanced: ERROR - {e}")
        
        # Analyze improvement
        if (len(results["original_decisions"]) > i and len(results["enhanced_decisions"]) > i and
            "error" not in results["original_decisions"][i] and "error" not in results["enhanced_decisions"][i]):
            
            orig_decision = results["original_decisions"][i]["decision"]
            enh_decision = results["enhanced_decisions"][i]["decision"]
            
            improvement = "none"
            if orig_decision == "END" and enh_decision in ["CONTINUE", "INFO", "SCHEDULE"]:
                improvement = "prevented_premature_end"
            elif orig_decision != "SCHEDULE" and enh_decision == "SCHEDULE":
                improvement = "better_scheduling"
            elif orig_decision == enh_decision:
                improvement = "consistent"
            
            results["improvements"].append({
                "scenario_index": i,
                "improvement_type": improvement,
                "original": orig_decision,
                "enhanced": enh_decision
            })
            
            print(f"    Improvement: {improvement}")
    
    return results

def test_premature_end_scenarios() -> List[Dict[str, Any]]:
    """Test scenarios where agents might make premature END decisions"""
    
    # Test scenarios that should NOT result in END decisions
    scenarios = [
        "Hi! I'm really excited about this Python developer position. I have about 2 years of experience and I'm eager to learn more!",
        "Hello, I'm interested in this role. I have experience with Django and FastAPI. Could you tell me more about the team?",
        "Hi there! I've been programming in Python for 18 months and I'm looking to transition into a developer role. This sounds perfect!",
        "Good day. I have 8 years of Python experience in fintech. What are the technical challenges in this position?",
        "I'm currently employed but this opportunity caught my attention. What makes this role unique?",
        "Hi! I'm a bootcamp graduate with several Python projects. I'm excited about joining a professional team!",
        "Hello. I specialize in data science with Python but I'm interested in web development opportunities."
    ]
    
    personas_to_test = ["eager_junior", "experienced_senior", "career_changer", "passive_candidate"]
    
    all_results = []
    
    for persona_id in personas_to_test:
        result = debug_agent_decision_logic(persona_id, scenarios)
        all_results.append(result)
    
    return all_results

def analyze_decision_improvements(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the decision improvements across all tests"""
    
    analysis = {
        "total_scenarios_tested": 0,
        "premature_ends_prevented": 0,
        "better_scheduling_decisions": 0,
        "consistent_decisions": 0,
        "personas_analyzed": len(all_results),
        "overall_improvement_rate": 0.0
    }
    
    for result in all_results:
        analysis["total_scenarios_tested"] += result["scenarios_tested"]
        
        for improvement in result["improvements"]:
            if improvement["improvement_type"] == "prevented_premature_end":
                analysis["premature_ends_prevented"] += 1
            elif improvement["improvement_type"] == "better_scheduling":
                analysis["better_scheduling_decisions"] += 1
            elif improvement["improvement_type"] == "consistent":
                analysis["consistent_decisions"] += 1
    
    total_improvements = (analysis["premature_ends_prevented"] + 
                         analysis["better_scheduling_decisions"])
    
    if analysis["total_scenarios_tested"] > 0:
        analysis["overall_improvement_rate"] = (total_improvements / analysis["total_scenarios_tested"]) * 100
    
    return analysis

def main():
    """Main agent decision debugging entry point"""
    print(">> Agent Decision Logic Debugger")
    print("=" * 60)
    
    # Test premature END decision scenarios
    print("\n>> Testing scenarios that should NOT result in END decisions...")
    
    all_results = test_premature_end_scenarios()
    
    # Analyze improvements
    analysis = analyze_decision_improvements(all_results)
    
    print("\n" + "=" * 60)
    print(">> AGENT DECISION ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"Total scenarios tested: {analysis['total_scenarios_tested']}")
    print(f"Personas analyzed: {analysis['personas_analyzed']}")
    print(f"Premature ENDs prevented: {analysis['premature_ends_prevented']}")
    print(f"Better scheduling decisions: {analysis['better_scheduling_decisions']}")
    print(f"Consistent decisions: {analysis['consistent_decisions']}")
    print(f"Overall improvement rate: {analysis['overall_improvement_rate']:.1f}%")
    
    if analysis["overall_improvement_rate"] >= 50:
        print("\n>> EXCELLENT: Agent decision logic significantly improved!")
        print("   Enhanced agent is preventing premature conversation endings")
    elif analysis["overall_improvement_rate"] >= 25:
        print("\n>> GOOD: Moderate agent decision improvements detected")
        print("   Enhanced agent shows better decision patterns")
    elif analysis["overall_improvement_rate"] >= 10:
        print("\n>> MINIMAL: Some agent decision improvements")
        print("   Additional tuning may be needed")
    else:
        print("\n>> LIMITED: Minimal agent decision improvements")
        print("   Agent decision logic needs more work")
    
    # Detailed persona analysis
    print("\n>> Per-Persona Analysis:")
    for result in all_results:
        persona_id = result["persona_id"]
        improvements = result["improvements"]
        
        prevented_ends = sum(1 for imp in improvements if imp["improvement_type"] == "prevented_premature_end")
        total_scenarios = result["scenarios_tested"]
        
        print(f"   {persona_id}: {prevented_ends}/{total_scenarios} premature ENDs prevented")
    
    print(f"\n>> Fix Status:")
    if analysis["premature_ends_prevented"] >= 10:
        print("   ✓ Premature END decision issue: SIGNIFICANTLY IMPROVED")
    elif analysis["premature_ends_prevented"] >= 5:
        print("   ✓ Premature END decision issue: MODERATELY IMPROVED")
    else:
        print("   ⚠ Premature END decision issue: NEEDS MORE WORK")
    
    return analysis

if __name__ == "__main__":
    main()