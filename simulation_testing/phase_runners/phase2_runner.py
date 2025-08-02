"""
Phase 2: Enhanced Simulation Runner
Comprehensive basic scenario testing with smart mock agents
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import components
from simulation_testing.config.test_config import config
from simulation_testing.personas.persona_loader import persona_loader
from simulation_testing.metrics.metrics_collector import metrics_collector
from simulation_testing.agents.smart_mock_agent import SmartMockAgent
from simulation_testing.scenarios.phase2_test_scenarios import phase2_scenarios, TestScenario
from simulation_testing.simulation_engine import SimulatedUser
import logging

class Phase2TestRunner:
    """Enhanced test runner for Phase 2 comprehensive basic testing"""
    
    def __init__(self):
        self.setup_logging()
        self.smart_agent = SmartMockAgent("SmartCoreAgent")
        self.test_results = {}
        self.comparative_data = defaultdict(list)
        
    def setup_logging(self):
        """Set up enhanced logging for Phase 2"""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.SIMULATION_ROOT / "results" / "phase2.log"),
                logging.StreamHandler() if config.CONSOLE_OUTPUT else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_scenario_test(self, scenario: TestScenario, persona_id: str) -> Dict:
        """Run a single scenario test with specific persona"""
        conversation_id = f"phase2_{scenario.id}_{persona_id}_{int(time.time())}"
        
        # Start metrics collection
        persona_data = persona_loader.get_persona(persona_id)
        persona_type = persona_data.get('type', 'Unknown') if persona_data else 'Unknown'
        
        conv_metrics = metrics_collector.start_conversation(
            conversation_id, persona_id, persona_type
        )
        
        self.logger.info(f">> Running scenario: {scenario.name}")
        self.logger.info(f"   Persona: {persona_data.get('name', persona_id)} ({persona_type})")
        
        if config.CONSOLE_OUTPUT:
            print(f"\n{'='*60}")
            print(f">> SCENARIO TEST: {scenario.name}")
            print(f"   Persona: {persona_data.get('name', persona_id)}")
            print(f"   Expected: {' -> '.join(scenario.expected_decisions)}")
            print(f"{'='*60}")
        
        # Initialize simulated user
        try:
            user = SimulatedUser(persona_id)
        except ValueError as e:
            metrics_collector.record_error(conversation_id, str(e))
            return {"error": str(e), "scenario_id": scenario.id, "persona_id": persona_id}
        
        # Run conversation with scenario expectations
        success = False
        conversation_log = []
        decisions_made = []
        validation_results = []
        
        try:
            # Initial greeting
            agent_message = "Hello! Thank you for your interest in our Python developer position. Could you tell me a bit about yourself and your experience?"
            
            if config.CONSOLE_OUTPUT:
                print(f"\nAGENT: {agent_message}")
            
            conversation_log.append({
                'type': 'agent',
                'message': agent_message,
                'timestamp': time.time()
            })
            
            max_turns = scenario.success_criteria.get('max_messages', 10)
            
            for turn in range(max_turns):
                metrics_collector.increment_message_count(conversation_id)
                
                # User response
                user_message = user.generate_response(agent_message, {'conversation_log': conversation_log})
                
                if config.CONSOLE_OUTPUT:
                    print(f"\nUSER ({persona_data.get('name', 'User')}): {user_message}")
                
                conversation_log.append({
                    'type': 'user',
                    'message': user_message,
                    'timestamp': time.time()
                })
                
                # Smart agent processing
                agent_start_time = time.time()
                agent_response, decision, reasoning = self.smart_agent.process_message(
                    user_message, conversation_id
                )
                agent_response_time = time.time() - agent_start_time
                
                decisions_made.append(decision)
                
                # Record metrics
                metrics_collector.record_agent_decision(
                    conversation_id, decision, reasoning, agent_response_time
                )
                
                if config.CONSOLE_OUTPUT:
                    print(f"\nAGENT: {agent_response}")
                    print(f"   [Decision: {decision}, Time: {agent_response_time:.2f}s]")
                    print(f"   [Reasoning: {reasoning}]")
                
                conversation_log.append({
                    'type': 'agent',
                    'message': agent_response,
                    'decision': decision,
                    'reasoning': reasoning,
                    'response_time': agent_response_time,
                    'timestamp': time.time()
                })
                
                # Check scenario-specific exit conditions
                if decision == 'SCHEDULE':
                    if user.should_accept_scheduling({'conversation_log': conversation_log}):
                        success = True
                        if config.CONSOLE_OUTPUT:
                            print(f"\nOK {persona_data.get('name')}: Yes, I'd like to schedule an interview!")
                        break
                    else:
                        if config.CONSOLE_OUTPUT:
                            print(f"\nX {persona_data.get('name')}: I need to think about it more.")
                
                elif decision == 'END':
                    break
                
                # Check if user wants to continue
                if not user.should_continue_conversation({'conversation_log': conversation_log}):
                    break
                
                agent_message = agent_response
                time.sleep(1)  # Brief delay
            
            # Validate scenario success criteria
            validation_results = self.validate_scenario_results(
                scenario, decisions_made, conversation_log, success
            )
            
        except Exception as e:
            self.logger.error(f"Error in scenario test: {e}")
            metrics_collector.record_error(conversation_id, str(e))
            validation_results = [{"validation": "error", "passed": False, "details": str(e)}]
        
        # Complete metrics
        completion_stage = "completed" if success else "ended"
        metrics_collector.complete_conversation(conversation_id, success, completion_stage)
        
        # Generate results
        scenario_result = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "persona_id": persona_id,
            "persona_type": persona_type,
            "success": success,
            "decisions_made": decisions_made,
            "expected_decisions": scenario.expected_decisions,
            "validation_results": validation_results,
            "conversation_length": len([msg for msg in conversation_log if msg['type'] == 'user']),
            "total_response_time": sum(msg.get('response_time', 0) for msg in conversation_log if 'response_time' in msg),
            "conversation_log": conversation_log if config.SAVE_CONVERSATION_TRANSCRIPTS else None
        }
        
        if config.CONSOLE_OUTPUT:
            print(f"\n>> Scenario Result: {'PASSED' if success else 'FAILED'}")
            print(f"   Decisions: {' -> '.join(decisions_made)}")
            print(f"   Expected: {' -> '.join(scenario.expected_decisions)}")
            print(f"   Length: {scenario_result['conversation_length']} messages")
            
            # Show validation results
            passed_validations = sum(1 for v in validation_results if v.get('passed', False))
            total_validations = len(validation_results)
            print(f"   Validations: {passed_validations}/{total_validations} passed")
            print(f"{'='*60}\n")
        
        return scenario_result
    
    def validate_scenario_results(self, scenario: TestScenario, decisions_made: List[str], 
                                conversation_log: List[Dict], success: bool) -> List[Dict]:
        """Validate scenario results against success criteria"""
        validations = []
        criteria = scenario.success_criteria
        
        # Message count validation
        user_messages = len([msg for msg in conversation_log if msg['type'] == 'user'])
        if 'min_messages' in criteria:
            validations.append({
                'validation': 'min_messages',
                'passed': user_messages >= criteria['min_messages'],
                'expected': criteria['min_messages'],
                'actual': user_messages
            })
        
        if 'max_messages' in criteria:
            validations.append({
                'validation': 'max_messages', 
                'passed': user_messages <= criteria['max_messages'],
                'expected': criteria['max_messages'],
                'actual': user_messages
            })
        
        # Decision validation
        if 'must_schedule' in criteria and criteria['must_schedule']:
            has_schedule = 'SCHEDULE' in decisions_made
            validations.append({
                'validation': 'must_schedule',
                'passed': has_schedule,
                'expected': True,
                'actual': has_schedule
            })
        
        # Expected decisions validation
        expected_decisions = scenario.expected_decisions
        decision_match_score = 0
        for expected in expected_decisions:
            if expected in decisions_made:
                decision_match_score += 1
        
        decision_match_ratio = decision_match_score / len(expected_decisions) if expected_decisions else 0
        validations.append({
            'validation': 'decision_alignment',
            'passed': decision_match_ratio >= 0.5,  # At least 50% of expected decisions
            'expected': expected_decisions,
            'actual': decisions_made,
            'score': decision_match_ratio
        })
        
        # Continue/End appropriateness
        if 'continue_count' in criteria:
            continue_count = decisions_made.count('CONTINUE')
            min_continues = criteria['continue_count'].get('min', 0)
            max_continues = criteria['continue_count'].get('max', 10)
            
            validations.append({
                'validation': 'continue_count',
                'passed': min_continues <= continue_count <= max_continues,
                'expected': f"{min_continues}-{max_continues}",
                'actual': continue_count
            })
        
        return validations
    
    def run_all_scenarios(self) -> Dict:
        """Run all Phase 2 scenarios across all personas"""
        print("\n>> PHASE 2: COMPREHENSIVE BASIC TESTING")
        print("=" * 60)
        print("Running 10 scenarios across 5 personas...")
        print()
        
        all_results = []
        scenario_summary = defaultdict(list)
        persona_summary = defaultdict(list)
        
        scenarios = phase2_scenarios.get_all_scenarios()
        
        for scenario in scenarios:
            print(f">> Running scenario: {scenario.name}")
            
            # Run scenario with each target persona
            for persona_id in scenario.target_personas:
                result = self.run_scenario_test(scenario, persona_id)
                all_results.append(result)
                
                # Collect data for comparative analysis
                scenario_summary[scenario.id].append(result)
                persona_summary[persona_id].append(result)
                
                time.sleep(2)  # Brief pause between tests
        
        # Generate comparative analysis
        comparative_analysis = self.generate_comparative_analysis(
            scenario_summary, persona_summary
        )
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = config.SIMULATION_ROOT / "results" / f"phase2_results_{timestamp}.json"
        
        complete_results = {
            "phase": "Phase 2 - Basic Scenarios",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_scenarios": len(scenarios),
                "total_tests": len(all_results),
                "successful_tests": sum(1 for r in all_results if r.get('success', False)),
                "success_rate": sum(1 for r in all_results if r.get('success', False)) / len(all_results) * 100
            },
            "individual_results": all_results,
            "comparative_analysis": comparative_analysis
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(complete_results, f, indent=2)
        
        self.print_phase2_summary(complete_results)
        
        return complete_results
    
    def generate_comparative_analysis(self, scenario_summary: Dict, persona_summary: Dict) -> Dict:
        """Generate detailed comparative analysis"""
        analysis = {
            "scenario_performance": {},
            "persona_performance": {},
            "decision_accuracy": {},
            "performance_insights": []
        }
        
        # Scenario performance analysis
        for scenario_id, results in scenario_summary.items():
            successful = sum(1 for r in results if r.get('success', False))
            total = len(results)
            avg_length = sum(r.get('conversation_length', 0) for r in results) / total if total > 0 else 0
            
            analysis["scenario_performance"][scenario_id] = {
                "success_rate": successful / total * 100 if total > 0 else 0,
                "total_tests": total,
                "avg_conversation_length": round(avg_length, 1),
                "common_decisions": self._get_common_decisions(results)
            }
        
        # Persona performance analysis
        for persona_id, results in persona_summary.items():
            successful = sum(1 for r in results if r.get('success', False))
            total = len(results)
            avg_response_time = sum(r.get('total_response_time', 0) for r in results) / total if total > 0 else 0
            
            analysis["persona_performance"][persona_id] = {
                "success_rate": successful / total * 100 if total > 0 else 0,
                "total_scenarios": total,
                "avg_response_time": round(avg_response_time, 2),
                "strengths": self._identify_persona_strengths(results),
                "challenges": self._identify_persona_challenges(results)
            }
        
        # Decision accuracy analysis
        all_results = [r for results in scenario_summary.values() for r in results]
        decision_counts = defaultdict(int)
        for result in all_results:
            for decision in result.get('decisions_made', []):
                decision_counts[decision] += 1
        
        analysis["decision_accuracy"] = dict(decision_counts)
        
        # Generate insights
        analysis["performance_insights"] = self._generate_insights(scenario_summary, persona_summary)
        
        return analysis
    
    def _get_common_decisions(self, results: List[Dict]) -> List[str]:
        """Get most common decision patterns for a scenario"""
        decision_patterns = []
        for result in results:
            decisions = result.get('decisions_made', [])
            if decisions:
                decision_patterns.append(' -> '.join(decisions))
        
        # Return most common pattern
        from collections import Counter
        if decision_patterns:
            return Counter(decision_patterns).most_common(1)[0][0].split(' -> ')
        return []
    
    def _identify_persona_strengths(self, results: List[Dict]) -> List[str]:
        """Identify strengths of a persona in testing"""
        strengths = []
        
        success_rate = sum(1 for r in results if r.get('success', False)) / len(results) if results else 0
        avg_length = sum(r.get('conversation_length', 0) for r in results) / len(results) if results else 0
        
        if success_rate > 0.7:
            strengths.append("High success rate")
        if avg_length > 4:
            strengths.append("Engages in detailed conversations")
        
        # Check for consistent decision patterns
        all_decisions = []
        for result in results:
            all_decisions.extend(result.get('decisions_made', []))
        
        if all_decisions.count('SCHEDULE') / len(all_decisions) > 0.3:
            strengths.append("Frequently reaches scheduling")
        
        return strengths or ["Consistent performance"]
    
    def _identify_persona_challenges(self, results: List[Dict]) -> List[str]:
        """Identify challenges of a persona in testing"""
        challenges = []
        
        success_rate = sum(1 for r in results if r.get('success', False)) / len(results) if results else 0
        
        if success_rate < 0.3:
            challenges.append("Low success rate")
        
        # Check for early terminations
        early_ends = sum(1 for r in results if r.get('conversation_length', 0) < 3)
        if early_ends > len(results) * 0.5:
            challenges.append("Conversations end too early")
        
        return challenges or ["No significant challenges identified"]
    
    def _generate_insights(self, scenario_summary: Dict, persona_summary: Dict) -> List[str]:
        """Generate actionable insights from test results"""
        insights = []
        
        # Overall success rates
        total_tests = sum(len(results) for results in scenario_summary.values())
        total_successes = sum(sum(1 for r in results if r.get('success', False)) 
                            for results in scenario_summary.values())
        overall_success_rate = total_successes / total_tests if total_tests > 0 else 0
        
        if overall_success_rate < 0.5:
            insights.append(f"Overall success rate ({overall_success_rate:.1%}) needs improvement")
        else:
            insights.append(f"Good overall success rate ({overall_success_rate:.1%})")
        
        # Best and worst performing scenarios
        scenario_rates = {}
        for scenario_id, results in scenario_summary.items():
            success_rate = sum(1 for r in results if r.get('success', False)) / len(results)
            scenario_rates[scenario_id] = success_rate
        
        if scenario_rates:
            best_scenario = max(scenario_rates, key=scenario_rates.get)
            worst_scenario = min(scenario_rates, key=scenario_rates.get)
            
            insights.append(f"Best performing scenario: {best_scenario} ({scenario_rates[best_scenario]:.1%})")
            insights.append(f"Needs attention: {worst_scenario} ({scenario_rates[worst_scenario]:.1%})")
        
        # Persona insights
        persona_rates = {}
        for persona_id, results in persona_summary.items():
            success_rate = sum(1 for r in results if r.get('success', False)) / len(results)
            persona_rates[persona_id] = success_rate
        
        if persona_rates:
            best_persona = max(persona_rates, key=persona_rates.get)
            challenging_persona = min(persona_rates, key=persona_rates.get)
            
            insights.append(f"Most successful persona: {best_persona} ({persona_rates[best_persona]:.1%})")
            insights.append(f"Most challenging persona: {challenging_persona} ({persona_rates[challenging_persona]:.1%})")
        
        return insights
    
    def print_phase2_summary(self, results: Dict):
        """Print comprehensive Phase 2 summary"""
        print("\n" + "="*80)
        print(">> PHASE 2: COMPREHENSIVE BASIC TESTING RESULTS")
        print("="*80)
        
        summary = results["summary"]
        print(f"\n>> Overall Performance:")
        print(f"   Total Scenarios: {summary['total_scenarios']}")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        # Comparative analysis
        comp_analysis = results["comparative_analysis"]
        
        print(f"\n>> Scenario Performance:")
        for scenario_id, perf in comp_analysis["scenario_performance"].items():
            print(f"   {scenario_id}: {perf['success_rate']:.1f}% success, {perf['avg_conversation_length']} avg messages")
        
        print(f"\n>> Persona Performance:")
        for persona_id, perf in comp_analysis["persona_performance"].items():
            print(f"   {persona_id}: {perf['success_rate']:.1f}% success, {perf['avg_response_time']:.2f}s avg response")
        
        print(f"\n>> Decision Distribution:")
        for decision, count in comp_analysis["decision_accuracy"].items():
            print(f"   {decision}: {count}")
        
        print(f"\n>> Key Insights:")
        for insight in comp_analysis["performance_insights"]:
            print(f"   - {insight}")
        
        print("\n" + "="*80 + "\n")

def main():
    """Main Phase 2 testing entry point"""
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        print("X Configuration issues found:")
        for issue in config_issues:
            print(f"   - {issue}")
        return
    
    print(">> Phase 2: Comprehensive Basic Testing")
    config.print_config_summary()
    
    # Run Phase 2 tests
    runner = Phase2TestRunner()
    results = runner.run_all_scenarios()
    
    print(f"\n>> Phase 2 Testing Completed!")
    print(f"   Results saved to: simulation_testing/results/phase2_results_*.json")

if __name__ == "__main__":
    main()