"""
Validation Test: Enhanced Conversation Flow vs Original
Compares the performance of enhanced conversation flow against original
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from simulation_testing.config.test_config import config
from simulation_testing.personas.persona_loader import persona_loader
from simulation_testing.metrics.metrics_collector import metrics_collector
from simulation_testing.agents.smart_mock_agent import SmartMockAgent
from simulation_testing.simulation_engine import SimulatedUser
from simulation_testing.enhanced_simulation_engine import EnhancedSimulatedUser, EnhancedSmartMockAgent
import logging


class ConversationFlowValidator:
    """Validates the improvements in enhanced conversation flow"""
    
    def __init__(self):
        self.setup_logging()
        self.validation_results = {}
        
    def setup_logging(self):
        """Set up validation logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.SIMULATION_ROOT / "results" / "validation_test.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_conversation_test(self, persona_id: str, use_enhanced: bool = True, max_turns: int = 8) -> Dict[str, Any]:
        """Run a single conversation test with specified engine"""
        
        conversation_id = f"validation_{'enhanced' if use_enhanced else 'original'}_{persona_id}_{int(time.time())}"
        
        try:
            # Initialize components based on engine type
            if use_enhanced:
                user = EnhancedSimulatedUser(persona_id)
                agent = EnhancedSmartMockAgent("ValidationAgent")
                initial_greeting = agent.get_personalized_greeting(persona_id)
            else:
                user = SimulatedUser(persona_id)
                agent = SmartMockAgent("ValidationAgent")
                initial_greeting = "Hello! Thank you for your interest in our Python developer position. Could you tell me a bit about yourself and your experience?"
            
            # Start metrics
            persona_data = persona_loader.get_persona(persona_id)
            persona_type = persona_data.get('type', 'Unknown') if persona_data else 'Unknown'
            
            conv_metrics = metrics_collector.start_conversation(
                conversation_id, persona_id, persona_type
            )
            
            # Run conversation
            conversation_log = []
            decisions_made = []
            success = False
            dropout_reason = None
            
            # Initial greeting
            conversation_log.append({
                'type': 'agent',
                'message': initial_greeting,
                'timestamp': time.time()
            })
            
            agent_message = initial_greeting
            
            for turn in range(max_turns):
                # User response
                user_start_time = time.time()
                user_message = user.generate_response(agent_message, {'conversation_log': conversation_log})
                user_response_time = time.time() - user_start_time
                
                conversation_log.append({
                    'type': 'user',
                    'message': user_message,
                    'timestamp': time.time(),
                    'response_time': user_response_time
                })
                
                # Check if user message indicates dropout
                if len(user_message) < 10:
                    dropout_reason = "extremely_short_response"
                    break
                
                # Agent processing
                agent_start_time = time.time()
                if use_enhanced:
                    agent_response, decision, reasoning = agent.process_message(
                        user_message, conversation_id, conversation_length=turn+1, persona_id=persona_id
                    )
                else:
                    agent_response, decision, reasoning = agent.process_message(user_message, conversation_id)
                
                agent_response_time = time.time() - agent_start_time
                
                decisions_made.append(decision)
                
                conversation_log.append({
                    'type': 'agent',
                    'message': agent_response,
                    'decision': decision,
                    'reasoning': reasoning,
                    'response_time': agent_response_time,
                    'timestamp': time.time()
                })
                
                # Check termination conditions
                if decision == 'SCHEDULE':
                    if user.should_accept_scheduling({'conversation_log': conversation_log}):
                        success = True
                        break
                elif decision == 'END':
                    dropout_reason = "agent_ended_conversation"
                    break
                
                # Check if user wants to continue
                if not user.should_continue_conversation({'conversation_log': conversation_log}):
                    dropout_reason = "user_ended_conversation"
                    break
                
                agent_message = agent_response
                time.sleep(0.1)  # Brief delay
            
            # Complete metrics
            completion_stage = "completed" if success else "ended"
            metrics_collector.complete_conversation(conversation_id, success, completion_stage)
            
            # Calculate metrics
            user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
            agent_messages = [msg for msg in conversation_log if msg.get('type') == 'agent']
            
            response_times = [msg.get('response_time', 0) for msg in conversation_log if msg.get('response_time')]
            
            result = {
                "conversation_id": conversation_id,
                "persona_id": persona_id,
                "engine_type": "enhanced" if use_enhanced else "original",
                "success": success,
                "dropout_reason": dropout_reason,
                "conversation_length": len(user_messages),
                "total_duration": conversation_log[-1]['timestamp'] - conversation_log[0]['timestamp'] if conversation_log else 0,
                "decisions_made": decisions_made,
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "first_user_response_length": len(user_messages[0]['message']) if user_messages else 0,
                "engagement_indicators": self._analyze_engagement(conversation_log),
                "conversation_log": conversation_log if config.SAVE_CONVERSATION_TRANSCRIPTS else None
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in conversation test: {e}")
            return {
                "conversation_id": conversation_id,
                "persona_id": persona_id,
                "engine_type": "enhanced" if use_enhanced else "original",
                "error": str(e),
                "success": False
            }
    
    def _analyze_engagement(self, conversation_log: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement indicators in the conversation"""
        user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
        agent_messages = [msg for msg in conversation_log if msg.get('type') == 'agent']
        
        if not user_messages:
            return {"engagement_score": 0.0, "indicators": []}
        
        indicators = []
        score = 0.5  # Base score
        
        # Message length analysis
        avg_user_length = sum(len(msg['message']) for msg in user_messages) / len(user_messages)
        if avg_user_length > 50:
            score += 0.2
            indicators.append("detailed_responses")
        elif avg_user_length < 20:
            score -= 0.2
            indicators.append("brief_responses")
        
        # Engagement keywords
        all_user_text = " ".join(msg['message'].lower() for msg in user_messages)
        
        positive_words = ['interested', 'excited', 'great', 'wonderful', 'perfect', 'yes', 'absolutely']
        negative_words = ['not interested', 'no thanks', 'boring', 'not right', 'pass']
        
        positive_count = sum(1 for word in positive_words if word in all_user_text)
        negative_count = sum(1 for word in negative_words if word in all_user_text)
        
        if positive_count > negative_count:
            score += 0.1 * positive_count
            indicators.append("positive_language")
        elif negative_count > positive_count:
            score -= 0.1 * negative_count
            indicators.append("negative_language")
        
        # Question asking (shows engagement)
        question_count = sum(1 for msg in user_messages if '?' in msg['message'])
        if question_count > 0:
            score += 0.1 * question_count
            indicators.append("asks_questions")
        
        # Conversation progression
        if len(user_messages) >= 5:
            score += 0.1
            indicators.append("sustained_conversation")
        elif len(user_messages) <= 2:
            score -= 0.2
            indicators.append("short_conversation")
        
        return {
            "engagement_score": max(0.0, min(1.0, score)),
            "indicators": indicators,
            "avg_message_length": avg_user_length,
            "positive_word_count": positive_count,
            "negative_word_count": negative_count,
            "question_count": question_count
        }
    
    def run_comparative_validation(self, test_rounds: int = 5) -> Dict[str, Any]:
        """Run comparative validation between original and enhanced flows"""
        
        self.logger.info(f">> Starting Comparative Validation Test")
        self.logger.info(f"   Test Rounds: {test_rounds} per persona per engine")
        
        personas_to_test = ["eager_junior", "experienced_senior", "career_changer", "passive_candidate", "difficult_candidate"]
        
        all_results = []
        original_results = []
        enhanced_results = []
        
        print(f"\n>> Running Comparative Validation Test")
        print(f"   Testing {len(personas_to_test)} personas with {test_rounds} rounds each")
        print(f"   Total tests: {len(personas_to_test) * test_rounds * 2}")
        
        for persona_id in personas_to_test:
            print(f"\n   Testing {persona_id}:")
            
            # Run original engine tests
            print(f"     Original engine: ", end="")
            for round_num in range(test_rounds):
                result = self.run_conversation_test(persona_id, use_enhanced=False)
                all_results.append(result)
                original_results.append(result)
                print("." if result.get('success') else "X", end="")
            
            # Run enhanced engine tests
            print(f" | Enhanced engine: ", end="")
            for round_num in range(test_rounds):
                result = self.run_conversation_test(persona_id, use_enhanced=True)
                all_results.append(result)
                enhanced_results.append(result)
                print("." if result.get('success') else "X", end="")
            
            print("")  # New line after each persona
        
        # Analyze results
        analysis = self._analyze_comparative_results(original_results, enhanced_results)
        
        # Generate report
        validation_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "test_configuration": {
                "personas_tested": personas_to_test,
                "rounds_per_persona": test_rounds,
                "total_tests": len(all_results)
            },
            "original_engine_results": self._summarize_results(original_results),
            "enhanced_engine_results": self._summarize_results(enhanced_results),
            "comparative_analysis": analysis,
            "individual_results": all_results,
            "recommendations": self._generate_recommendations(analysis)
        }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = config.SIMULATION_ROOT / "results" / f"validation_enhanced_flow_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(validation_report, f, indent=2, default=str)
        
        self._print_validation_summary(validation_report)
        
        return validation_report
    
    def _summarize_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize a set of test results"""
        if not results:
            return {"error": "No results to summarize"}
        
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        # Calculate metrics
        success_rate = len(successful) / len(results) * 100
        
        avg_conversation_length = sum(r.get('conversation_length', 0) for r in results) / len(results)
        avg_response_time = sum(r.get('avg_response_time', 0) for r in results) / len(results)
        avg_first_response_length = sum(r.get('first_user_response_length', 0) for r in results) / len(results)
        
        # Analyze dropout reasons
        dropout_reasons = [r.get('dropout_reason') for r in failed if r.get('dropout_reason')]
        dropout_counts = {}
        for reason in dropout_reasons:
            dropout_counts[reason] = dropout_counts.get(reason, 0) + 1
        
        # Analyze engagement
        engagement_scores = [r.get('engagement_indicators', {}).get('engagement_score', 0) for r in results]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        
        return {
            "total_tests": len(results),
            "successful_tests": len(successful),
            "failed_tests": len(failed),
            "success_rate": success_rate,
            "avg_conversation_length": avg_conversation_length,
            "avg_response_time": avg_response_time,
            "avg_first_response_length": avg_first_response_length,
            "avg_engagement_score": avg_engagement,
            "dropout_reasons": dropout_counts
        }
    
    def _analyze_comparative_results(self, original: List[Dict], enhanced: List[Dict]) -> Dict[str, Any]:
        """Analyze comparative performance between engines"""
        
        original_summary = self._summarize_results(original)
        enhanced_summary = self._summarize_results(enhanced)
        
        # Calculate improvements
        success_rate_improvement = enhanced_summary['success_rate'] - original_summary['success_rate']
        conversation_length_improvement = enhanced_summary['avg_conversation_length'] - original_summary['avg_conversation_length']
        engagement_improvement = enhanced_summary['avg_engagement_score'] - original_summary['avg_engagement_score']
        first_response_improvement = enhanced_summary['avg_first_response_length'] - original_summary['avg_first_response_length']
        
        # Analyze persona-specific improvements
        persona_analysis = {}
        for persona_id in ["eager_junior", "experienced_senior", "career_changer", "passive_candidate", "difficult_candidate"]:
            orig_persona = [r for r in original if r.get('persona_id') == persona_id]
            enh_persona = [r for r in enhanced if r.get('persona_id') == persona_id]
            
            if orig_persona and enh_persona:
                orig_success_rate = sum(1 for r in orig_persona if r.get('success', False)) / len(orig_persona) * 100
                enh_success_rate = sum(1 for r in enh_persona if r.get('success', False)) / len(enh_persona) * 100
                
                persona_analysis[persona_id] = {
                    "original_success_rate": orig_success_rate,
                    "enhanced_success_rate": enh_success_rate,
                    "improvement": enh_success_rate - orig_success_rate
                }
        
        return {
            "success_rate_improvement": success_rate_improvement,
            "conversation_length_improvement": conversation_length_improvement,
            "engagement_score_improvement": engagement_improvement,
            "first_response_improvement": first_response_improvement,
            "persona_specific_analysis": persona_analysis,
            "statistical_significance": self._calculate_significance(original_summary, enhanced_summary)
        }
    
    def _calculate_significance(self, original: Dict, enhanced: Dict) -> str:
        """Calculate statistical significance of improvements"""
        success_improvement = enhanced['success_rate'] - original['success_rate']
        engagement_improvement = enhanced['avg_engagement_score'] - original['avg_engagement_score']
        
        if success_improvement > 20 and engagement_improvement > 0.2:
            return "highly_significant"
        elif success_improvement > 10 and engagement_improvement > 0.1:
            return "significant"
        elif success_improvement > 5:
            return "moderate"
        else:
            return "minimal"
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        success_improvement = analysis.get('success_rate_improvement', 0)
        engagement_improvement = analysis.get('engagement_score_improvement', 0)
        
        if success_improvement > 15:
            recommendations.append("Deploy enhanced conversation flow - significant success rate improvement detected")
        elif success_improvement > 5:
            recommendations.append("Consider deploying enhanced flow after additional testing")
        else:
            recommendations.append("Continue refining enhanced flow - improvement is marginal")
        
        if engagement_improvement > 0.2:
            recommendations.append("Enhanced engagement strategies are working well")
        elif engagement_improvement < 0:
            recommendations.append("Review engagement strategies - showing negative impact")
        
        # Persona-specific recommendations
        persona_analysis = analysis.get('persona_specific_analysis', {})
        for persona_id, data in persona_analysis.items():
            improvement = data.get('improvement', 0)
            if improvement < -10:
                recommendations.append(f"Enhanced flow performing poorly for {persona_id} - needs specific attention")
            elif improvement > 20:
                recommendations.append(f"Enhanced flow working excellently for {persona_id}")
        
        return recommendations
    
    def _print_validation_summary(self, report: Dict):
        """Print comprehensive validation summary"""
        print("\n" + "="*80)
        print(">> CONVERSATION FLOW VALIDATION RESULTS")
        print("="*80)
        
        config_info = report["test_configuration"]
        print(f"\n>> Test Configuration:")
        print(f"   Personas Tested: {len(config_info['personas_tested'])}")
        print(f"   Rounds per Persona: {config_info['rounds_per_persona']}")
        print(f"   Total Tests: {config_info['total_tests']}")
        
        original = report["original_engine_results"]
        enhanced = report["enhanced_engine_results"]
        analysis = report["comparative_analysis"]
        
        print(f"\n>> Performance Comparison:")
        print(f"   Original Success Rate: {original['success_rate']:.1f}%")
        print(f"   Enhanced Success Rate: {enhanced['success_rate']:.1f}%")
        print(f"   Success Rate Improvement: {analysis['success_rate_improvement']:+.1f}%")
        
        print(f"\n   Original Avg Conversation Length: {original['avg_conversation_length']:.1f}")
        print(f"   Enhanced Avg Conversation Length: {enhanced['avg_conversation_length']:.1f}")
        print(f"   Conversation Length Improvement: {analysis['conversation_length_improvement']:+.1f}")
        
        print(f"\n   Original Avg Engagement Score: {original['avg_engagement_score']:.2f}")
        print(f"   Enhanced Avg Engagement Score: {enhanced['avg_engagement_score']:.2f}")
        print(f"   Engagement Improvement: {analysis['engagement_score_improvement']:+.2f}")
        
        print(f"\n>> Persona-Specific Analysis:")
        persona_analysis = analysis['persona_specific_analysis']
        for persona_id, data in persona_analysis.items():
            print(f"   {persona_id}: {data['original_success_rate']:.1f}% → {data['enhanced_success_rate']:.1f}% ({data['improvement']:+.1f}%)")
        
        print(f"\n>> Statistical Significance: {analysis['statistical_significance'].upper()}")
        
        print(f"\n>> Recommendations:")
        for rec in report["recommendations"]:
            print(f"   - {rec}")
        
        print("\n" + "="*80 + "\n")


def main():
    """Main validation entry point"""
    validator = ConversationFlowValidator()
    
    # Run comparative validation
    results = validator.run_comparative_validation(test_rounds=3)  # 3 rounds per persona
    
    print(f"\n>> Validation completed!")
    print(f"   Results saved to: simulation_testing/results/validation_enhanced_flow_*.json")
    
    # Check if improvements are significant
    analysis = results["comparative_analysis"]
    success_improvement = analysis["success_rate_improvement"]
    significance = analysis["statistical_significance"]
    
    if significance == "highly_significant":
        print(f"   >> EXCELLENT: Highly significant improvements detected!")
        print(f"   >> Recommend immediate deployment of enhanced flow")
    elif significance == "significant":
        print(f"   >> GOOD: Significant improvements detected")
        print(f"   >> Enhanced flow ready for broader testing")
    elif significance == "moderate":
        print(f"   >> MODERATE: Some improvements detected")
        print(f"   >> Continue refinement before deployment")
    else:
        print(f"   >> LIMITED: Minimal improvements detected")
        print(f"   >> Additional fixes needed before deployment")


if __name__ == "__main__":
    main()