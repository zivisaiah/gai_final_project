"""
Final Fix Validation Test
Complete conversation testing with enhanced fixes
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation_testing.config.test_config import config
from simulation_testing.personas.persona_loader import persona_loader
from simulation_testing.metrics.metrics_collector import metrics_collector
from simulation_testing.enhanced_simulation_engine import EnhancedSimulatedUser, EnhancedSmartMockAgent

def run_complete_conversation_test(persona_id: str, max_turns: int = 6) -> Dict[str, Any]:
    """Run a complete conversation test with enhanced flow"""
    
    conversation_id = f"final_validation_{persona_id}_{int(time.time())}"
    
    try:
        # Initialize enhanced components
        user = EnhancedSimulatedUser(persona_id)
        agent = EnhancedSmartMockAgent("FinalValidationAgent")
        
        # Start metrics
        persona_data = persona_loader.get_persona(persona_id)
        persona_type = persona_data.get('type', 'Unknown') if persona_data else 'Unknown'
        
        conv_metrics = metrics_collector.start_conversation(
            conversation_id, persona_id, persona_type
        )
        
        # Run complete conversation
        conversation_log = []
        success = False
        failure_reason = None
        
        # Initial personalized greeting
        initial_greeting = agent.get_personalized_greeting(persona_id)
        conversation_log.append({
            'type': 'agent',
            'message': initial_greeting,
            'timestamp': time.time()
        })
        
        agent_message = initial_greeting
        
        for turn in range(max_turns):
            # User response
            user_response = user.generate_response(agent_message, {'conversation_log': conversation_log})
            
            conversation_log.append({
                'type': 'user',
                'message': user_response,
                'timestamp': time.time()
            })
            
            # Check for extremely short response (potential dropout)
            if len(user_response) < 5:
                failure_reason = "user_extremely_short_response"
                break
            
            # Agent processing with enhanced logic
            agent_response, decision, reasoning = agent.process_message(
                user_response, conversation_id, conversation_length=turn+1, persona_id=persona_id
            )
            
            conversation_log.append({
                'type': 'agent',
                'message': agent_response,
                'decision': decision,
                'reasoning': reasoning,
                'timestamp': time.time()
            })
            
            # Check termination conditions
            if decision == 'SCHEDULE':
                if user.should_accept_scheduling({'conversation_log': conversation_log}):
                    success = True
                    break
                else:
                    # User declined scheduling - continue conversation
                    agent_message = "I understand. What other aspects of the role would you like to discuss?"
                    continue
            elif decision == 'END':
                failure_reason = "agent_ended_conversation"
                break
            
            # Check if user wants to continue
            if not user.should_continue_conversation({'conversation_log': conversation_log}):
                failure_reason = "user_ended_conversation"
                break
            
            agent_message = agent_response
            time.sleep(0.1)  # Brief delay
        
        # Complete metrics
        completion_stage = "completed" if success else "failed"
        metrics_collector.complete_conversation(conversation_id, success, completion_stage)
        
        # Calculate conversation quality metrics
        user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
        agent_messages = [msg for msg in conversation_log if msg.get('type') == 'agent']
        
        avg_user_response_length = sum(len(msg['message']) for msg in user_messages) / len(user_messages) if user_messages else 0
        
        decisions_made = [msg.get('decision') for msg in conversation_log if msg.get('decision')]
        
        result = {
            "conversation_id": conversation_id,
            "persona_id": persona_id,
            "success": success,
            "failure_reason": failure_reason,
            "conversation_length": len(user_messages),
            "total_duration": conversation_log[-1]['timestamp'] - conversation_log[0]['timestamp'] if len(conversation_log) > 1 else 0,
            "avg_user_response_length": avg_user_response_length,
            "decisions_made": decisions_made,
            "used_personalized_greeting": len(initial_greeting) > 80,
            "conversation_transcript": conversation_log[:6] if config.SAVE_CONVERSATION_TRANSCRIPTS else None  # First 3 exchanges
        }
        
        return result
        
    except Exception as e:
        return {
            "conversation_id": conversation_id,
            "persona_id": persona_id,
            "error": str(e),
            "success": False
        }

def run_final_validation_suite() -> Dict[str, Any]:
    """Run comprehensive final validation"""
    
    print(">> Final Fix Validation Test")
    print("=" * 50)
    
    personas_to_test = ["eager_junior", "experienced_senior", "career_changer", "passive_candidate", "difficult_candidate"]
    test_rounds = 3  # 3 conversations per persona
    
    all_results = []
    
    print(f"Testing {len(personas_to_test)} personas with {test_rounds} rounds each")
    print(f"Total conversations: {len(personas_to_test) * test_rounds}\n")
    
    for persona_id in personas_to_test:
        print(f"Testing {persona_id}: ", end="")
        
        persona_results = []
        for round_num in range(test_rounds):
            result = run_complete_conversation_test(persona_id)
            all_results.append(result)
            persona_results.append(result)
            
            # Print result indicator
            if result.get('success'):
                print("✓", end="")
            elif result.get('error'):
                print("E", end="")
            else:
                print("X", end="")
        
        # Print persona summary
        successes = sum(1 for r in persona_results if r.get('success', False))
        print(f" ({successes}/{test_rounds})")
    
    # Analyze results
    validation_report = analyze_validation_results(all_results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = config.SIMULATION_ROOT / "results" / f"final_validation_enhanced_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2, default=str)
    
    return validation_report

def analyze_validation_results(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the validation results"""
    
    successful = [r for r in all_results if r.get('success', False) and 'error' not in r]
    failed = [r for r in all_results if not r.get('success', False) and 'error' not in r]
    errors = [r for r in all_results if 'error' in r]
    
    success_rate = len(successful) / len(all_results) * 100 if all_results else 0
    
    # Analyze failure reasons
    failure_reasons = {}
    for result in failed:
        reason = result.get('failure_reason', 'unknown')
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    
    # Analyze conversation quality
    avg_conversation_length = sum(r.get('conversation_length', 0) for r in all_results) / len(all_results) if all_results else 0
    avg_response_length = sum(r.get('avg_user_response_length', 0) for r in all_results) / len(all_results) if all_results else 0
    
    # Persona performance
    persona_performance = {}
    for result in all_results:
        persona_id = result.get('persona_id', 'unknown')
        if persona_id not in persona_performance:
            persona_performance[persona_id] = {'total': 0, 'successful': 0}
        
        persona_performance[persona_id]['total'] += 1
        if result.get('success', False):
            persona_performance[persona_id]['successful'] += 1
    
    # Calculate persona success rates
    for persona_id in persona_performance:
        total = persona_performance[persona_id]['total']
        successful = persona_performance[persona_id]['successful']
        persona_performance[persona_id]['success_rate'] = (successful / total * 100) if total > 0 else 0
    
    return {
        "validation_timestamp": datetime.now().isoformat(),
        "test_summary": {
            "total_conversations": len(all_results),
            "successful_conversations": len(successful),
            "failed_conversations": len(failed),
            "error_conversations": len(errors),
            "success_rate": success_rate
        },
        "conversation_quality": {
            "avg_conversation_length": avg_conversation_length,
            "avg_user_response_length": avg_response_length
        },
        "failure_analysis": {
            "failure_reasons": failure_reasons,
            "most_common_failure": max(failure_reasons.items(), key=lambda x: x[1])[0] if failure_reasons else None
        },
        "persona_performance": persona_performance,
        "improvements_validated": {
            "personalized_greetings": sum(1 for r in all_results if r.get('used_personalized_greeting', False)),
            "longer_conversations": sum(1 for r in all_results if r.get('conversation_length', 0) >= 3),
            "detailed_responses": sum(1 for r in all_results if r.get('avg_user_response_length', 0) >= 50)
        },
        "all_results": all_results
    }

def print_validation_summary(report: Dict[str, Any]):
    """Print comprehensive validation summary"""
    
    print("\n" + "=" * 60)
    print(">> FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    summary = report["test_summary"]
    quality = report["conversation_quality"]
    
    print(f"Total conversations tested: {summary['total_conversations']}")
    print(f"Successful conversations: {summary['successful_conversations']}")
    print(f"Failed conversations: {summary['failed_conversations']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    
    print(f"\nConversation Quality:")
    print(f"  Average conversation length: {quality['avg_conversation_length']:.1f} exchanges")
    print(f"  Average user response length: {quality['avg_user_response_length']:.1f} characters")
    
    print(f"\nPersona Performance:")
    for persona_id, perf in report["persona_performance"].items():
        print(f"  {persona_id}: {perf['successful']}/{perf['total']} ({perf['success_rate']:.1f}%)")
    
    print(f"\nImprovements Validated:")
    improvements = report["improvements_validated"]
    print(f"  Personalized greetings used: {improvements['personalized_greetings']}")
    print(f"  Conversations >= 3 exchanges: {improvements['longer_conversations']}")
    print(f"  Detailed responses (>=50 chars): {improvements['detailed_responses']}")
    
    if report["failure_analysis"]["failure_reasons"]:
        print(f"\nFailure Analysis:")
        for reason, count in report["failure_analysis"]["failure_reasons"].items():
            print(f"  {reason}: {count} cases")
    
    # Overall assessment
    success_rate = summary['success_rate']
    avg_length = quality['avg_conversation_length']
    
    print(f"\n" + "=" * 60)
    print(">> OVERALL ASSESSMENT")
    print("=" * 60)
    
    if success_rate >= 70 and avg_length >= 3:
        print("✓ EXCELLENT: Enhanced conversation flow is working very well!")
        print("  Recommendation: Deploy enhanced flow to production")
    elif success_rate >= 50 and avg_length >= 2.5:
        print("✓ GOOD: Enhanced conversation flow shows significant improvement")
        print("  Recommendation: Consider deployment with monitoring")
    elif success_rate >= 40:
        print("~ MODERATE: Some improvement but needs more work")
        print("  Recommendation: Continue refinement")
    else:
        print("✗ POOR: Enhanced flow needs significant additional work")
        print("  Recommendation: Major fixes required")

def main():
    """Main final validation entry point"""
    
    validation_report = run_final_validation_suite()
    print_validation_summary(validation_report)
    
    return validation_report

if __name__ == "__main__":
    main()