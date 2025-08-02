"""
Phase 3: Topic Switching Test Runner
Advanced testing for conversation topic switching and context management
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
from simulation_testing.scenarios.phase3_topic_switching import (
    phase3_topic_switching, TopicSwitchingScenario, validate_topic_switching_scenario
)
from simulation_testing.simulation_engine import SimulatedUser
import logging


class TopicSwitchingSimulator:
    """Simulates topic switching conversations to test agent adaptability"""
    
    def __init__(self, persona_id: str, scenario: TopicSwitchingScenario):
        self.persona_id = persona_id
        self.scenario = scenario
        self.persona_data = persona_loader.get_persona(persona_id)
        self.current_topic_index = 0
        self.switches_completed = 0
        
    def should_switch_topic(self, conversation_log: List[Dict]) -> Tuple[bool, Optional[str]]:
        """
        Determine if it's time to switch topics based on scenario progression
        
        Returns:
            Tuple of (should_switch, switch_message)
        """
        user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
        
        # Check if we should trigger the next topic switch
        if self.current_topic_index < len(self.scenario.topic_switches):
            current_switch = self.scenario.topic_switches[self.current_topic_index]
            
            # Trigger switch after a minimum number of messages on current topic
            messages_since_start = len(user_messages)
            min_messages_before_switch = 1 + self.current_topic_index  # Progressive delay
            
            if messages_since_start >= min_messages_before_switch:
                return True, current_switch.trigger_message
        
        return False, None
    
    def generate_topic_switch_response(self, agent_message: str, conversation_context: Dict) -> str:
        """Generate a response that includes topic switching"""
        conversation_log = conversation_context.get('conversation_log', [])
        
        # Check if we should switch topics
        should_switch, switch_message = self.should_switch_topic(conversation_log)
        
        if should_switch and switch_message:
            self.current_topic_index += 1
            self.switches_completed += 1
            return switch_message
        
        # Otherwise, generate normal persona-based response
        base_user = SimulatedUser(self.persona_id)
        return base_user.generate_response(agent_message, conversation_context)
    
    def get_switching_progress(self) -> Dict[str, any]:
        """Get progress information about topic switching"""
        return {
            "total_switches_planned": len(self.scenario.topic_switches),
            "switches_completed": self.switches_completed,
            "current_topic_index": self.current_topic_index,
            "progress_percentage": (self.switches_completed / len(self.scenario.topic_switches)) * 100 
                if self.scenario.topic_switches else 100
        }


class Phase3TopicSwitchingRunner:
    """Advanced test runner for Phase 3 topic switching scenarios"""
    
    def __init__(self):
        self.setup_logging()
        self.smart_agent = SmartMockAgent("TopicSwitchingAgent")
        self.test_results = {}
        self.topic_analysis = defaultdict(list)
        
    def setup_logging(self):
        """Set up enhanced logging for Phase 3 topic switching tests"""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.SIMULATION_ROOT / "results" / "phase3_topic_switching.log"),
                logging.StreamHandler() if config.CONSOLE_OUTPUT else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_topic_switching_test(self, scenario: TopicSwitchingScenario, persona_id: str) -> Dict:
        """Run a single topic switching test"""
        conversation_id = f"phase3_topic_{scenario.id}_{persona_id}_{int(time.time())}"
        
        # Start metrics collection
        persona_data = persona_loader.get_persona(persona_id)
        persona_type = persona_data.get('type', 'Unknown') if persona_data else 'Unknown'
        
        conv_metrics = metrics_collector.start_conversation(
            conversation_id, persona_id, persona_type
        )
        
        self.logger.info(f">> Testing topic switching: {scenario.name}")
        self.logger.info(f"   Persona: {persona_data.get('name', persona_id)} ({persona_type})")
        self.logger.info(f"   Initial topic: {scenario.initial_topic.value}")
        self.logger.info(f"   Planned switches: {len(scenario.topic_switches)}")
        
        if config.CONSOLE_OUTPUT:
            print(f"\n{'='*70}")
            print(f">> TOPIC SWITCHING TEST: {scenario.name}")
            print(f"   Persona: {persona_data.get('name', persona_id)}")
            print(f"   Difficulty: {scenario.difficulty_level}")
            print(f"   Switches: {len(scenario.topic_switches)}")
            print(f"{'='*70}")
        
        # Initialize topic switching simulator
        try:
            topic_simulator = TopicSwitchingSimulator(persona_id, scenario)
        except ValueError as e:
            metrics_collector.record_error(conversation_id, str(e))
            return {"error": str(e), "scenario_id": scenario.id, "persona_id": persona_id}
        
        # Run conversation with topic switching
        success = False
        conversation_log = []
        decisions_made = []
        topic_switches_executed = []
        context_retention_events = []
        
        try:
            # Initial greeting - start with initial topic context
            initial_context = self._get_topic_opening(scenario.initial_topic)
            agent_message = f"Hello! Thank you for your interest in our Python developer position. {initial_context}"
            
            if config.CONSOLE_OUTPUT:
                print(f"\nAGENT: {agent_message}")
            
            conversation_log.append({
                'type': 'agent',
                'message': agent_message,
                'timestamp': time.time(),
                'topic_context': scenario.initial_topic.value
            })
            
            max_turns = scenario.success_criteria.get('max_messages', 8)
            
            for turn in range(max_turns):
                metrics_collector.increment_message_count(conversation_id)
                
                # Generate user response with potential topic switching
                user_message = topic_simulator.generate_topic_switch_response(
                    agent_message, {'conversation_log': conversation_log}
                )
                
                if config.CONSOLE_OUTPUT:
                    print(f"\nUSER ({persona_data.get('name', 'User')}): {user_message}")
                
                # Check if this was a topic switch
                switching_progress = topic_simulator.get_switching_progress()
                was_topic_switch = (switching_progress['switches_completed'] > len(topic_switches_executed))
                
                if was_topic_switch:
                    current_switch = scenario.topic_switches[len(topic_switches_executed)]
                    topic_switches_executed.append({
                        'switch_index': len(topic_switches_executed),
                        'from_topic': current_switch.from_topic.value,
                        'to_topic': current_switch.to_topic.value,
                        'trigger_message': user_message,
                        'turn_number': turn,
                        'timestamp': time.time()
                    })
                    
                    if config.CONSOLE_OUTPUT:
                        print(f"   >> TOPIC SWITCH: {current_switch.from_topic.value} -> {current_switch.to_topic.value}")
                
                conversation_log.append({
                    'type': 'user',
                    'message': user_message,
                    'timestamp': time.time(),
                    'topic_switch': was_topic_switch,
                    'switching_progress': switching_progress
                })
                
                # Smart agent processing
                agent_start_time = time.time()
                agent_response, decision, reasoning = self.smart_agent.process_message(
                    user_message, conversation_id
                )
                agent_response_time = time.time() - agent_start_time
                
                decisions_made.append(decision)
                
                # Analyze agent's topic handling
                topic_handling_score = self._analyze_topic_handling(
                    user_message, agent_response, was_topic_switch, 
                    current_switch if was_topic_switch else None
                )
                
                # Check for context retention indicators
                context_indicators = self._detect_context_retention(agent_response, conversation_log)
                if context_indicators:
                    context_retention_events.append({
                        'turn': turn,
                        'indicators': context_indicators,
                        'message': agent_response
                    })
                
                # Record metrics
                metrics_collector.record_agent_decision(
                    conversation_id, decision, reasoning, agent_response_time
                )
                
                if config.CONSOLE_OUTPUT:
                    print(f"\nAGENT: {agent_response}")
                    print(f"   [Decision: {decision}, Time: {agent_response_time:.2f}s]")
                    print(f"   [Topic Handling Score: {topic_handling_score:.2f}]")
                    if context_indicators:
                        print(f"   [Context Retention: {', '.join(context_indicators)}]")
                
                conversation_log.append({
                    'type': 'agent',
                    'message': agent_response,
                    'decision': decision,
                    'reasoning': reasoning,
                    'response_time': agent_response_time,
                    'topic_handling_score': topic_handling_score,
                    'context_indicators': context_indicators,
                    'timestamp': time.time()
                })
                
                # Check scenario-specific exit conditions
                if decision == 'SCHEDULE':
                    # For topic switching tests, scheduling can be success if it happens naturally
                    success = True
                    if config.CONSOLE_OUTPUT:
                        print(f"\n>> SCHEDULING DECISION REACHED")
                    break
                elif decision == 'END':
                    break
                
                # Check if all topic switches have been completed
                if switching_progress['switches_completed'] >= len(scenario.topic_switches):
                    # All switches completed, conversation can continue briefly then succeed
                    if turn >= len(scenario.topic_switches) + 2:  # Allow a few more turns
                        success = True
                        break
                
                agent_message = agent_response
                time.sleep(1)  # Brief delay
            
            # Validate scenario-specific results
            validation_results = validate_topic_switching_scenario(
                scenario, conversation_log, decisions_made
            )
            
            # Update success based on validation
            if not success:
                success = validation_results.get('overall_success', False)
                
        except Exception as e:
            self.logger.error(f"Error in topic switching test: {e}")
            metrics_collector.record_error(conversation_id, str(e))
            validation_results = {"error": str(e), "overall_success": False}
        
        # Complete metrics
        completion_stage = "completed" if success else "ended"
        metrics_collector.complete_conversation(conversation_id, success, completion_stage)
        
        # Generate comprehensive results
        scenario_result = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "persona_id": persona_id,
            "persona_type": persona_type,
            "success": success,
            "difficulty_level": scenario.difficulty_level,
            "decisions_made": decisions_made,
            "expected_decisions": scenario.expected_decisions,
            "topic_switches": {
                "planned": len(scenario.topic_switches),
                "executed": len(topic_switches_executed),
                "success_rate": len(topic_switches_executed) / len(scenario.topic_switches) if scenario.topic_switches else 1.0,
                "details": topic_switches_executed
            },
            "context_retention": {
                "events_detected": len(context_retention_events),
                "retention_score": validation_results.get('context_retention_score', 0.0),
                "details": context_retention_events
            },
            "agent_adaptability": {
                "score": validation_results.get('agent_adaptability_score', 0.0),
                "topic_handling_average": sum(msg.get('topic_handling_score', 0) 
                    for msg in conversation_log if msg.get('type') == 'agent') / 
                    max(1, len([msg for msg in conversation_log if msg.get('type') == 'agent']))
            },
            "validation_results": validation_results,
            "conversation_length": len([msg for msg in conversation_log if msg['type'] == 'user']),
            "total_response_time": sum(msg.get('response_time', 0) for msg in conversation_log if 'response_time' in msg),
            "conversation_log": conversation_log if config.SAVE_CONVERSATION_TRANSCRIPTS else None
        }
        
        if config.CONSOLE_OUTPUT:
            print(f"\n>> Topic Switching Test Result: {'PASSED' if success else 'FAILED'}")
            print(f"   Switches Executed: {len(topic_switches_executed)}/{len(scenario.topic_switches)}")
            print(f"   Context Retention Events: {len(context_retention_events)}")
            print(f"   Agent Adaptability Score: {scenario_result['agent_adaptability']['score']:.2f}")
            print(f"   Overall Validation: {'PASSED' if validation_results.get('overall_success') else 'FAILED'}")
            print(f"{'='*70}\n")
        
        return scenario_result
    
    def _get_topic_opening(self, topic) -> str:
        """Get appropriate opening based on initial topic"""
        topic_openings = {
            "experience": "Could you tell me about your experience with Python development?",
            "availability": "What's your availability for starting a new position?",
            "technical_questions": "I'd love to learn about your technical background.",
            "job_requirements": "Let me know if you have any questions about the role requirements.",
            "company_culture": "What would you like to know about our company culture?",
            "salary": "What are your salary expectations for this role?",
            "benefits": "Are you interested in learning about our benefits package?",
            "work_environment": "What kind of work environment are you looking for?",
            "career_growth": "What are your career growth aspirations?",
            "team_structure": "Would you like to know about our team structure?"
        }
        return topic_openings.get(topic.value, "What would you like to discuss about this role?")
    
    def _analyze_topic_handling(self, user_message: str, agent_response: str, 
                               was_topic_switch: bool, topic_switch = None) -> float:
        """Analyze how well the agent handled the topic switch"""
        if not was_topic_switch:
            return 1.0  # No topic switch to handle
        
        score = 0.0
        user_lower = user_message.lower()
        agent_lower = agent_response.lower()
        
        # Check if agent acknowledged the topic change
        acknowledgment_phrases = [
            "that's a great question", "let me tell you about", "regarding",
            "about", "concerning", "as for", "when it comes to"
        ]
        if any(phrase in agent_lower for phrase in acknowledgment_phrases):
            score += 0.3
        
        # Check if agent addressed the new topic appropriately
        if topic_switch:
            topic_keywords = {
                "salary": ["salary", "compensation", "pay", "range", "benefits"],
                "availability": ["schedule", "start", "available", "time", "interview"],
                "technical_questions": ["technical", "technology", "programming", "language", "framework"],
                "company_culture": ["culture", "environment", "team", "values", "work"],
                "work_environment": ["remote", "office", "hybrid", "location", "workplace"],
                "benefits": ["benefits", "health", "insurance", "vacation", "perks"],
                "career_growth": ["growth", "advancement", "career", "development", "opportunity"]
            }
            
            target_topic = topic_switch.to_topic.value
            relevant_keywords = topic_keywords.get(target_topic, [])
            
            if any(keyword in agent_lower for keyword in relevant_keywords):
                score += 0.5
        
        # Check response length (adequate engagement)
        if len(agent_response) > 50:
            score += 0.2
        
        return min(score, 1.0)
    
    def _detect_context_retention(self, agent_response: str, conversation_log: List[Dict]) -> List[str]:
        """Detect indicators of context retention in agent response"""
        indicators = []
        agent_lower = agent_response.lower()
        
        # Direct context references
        context_phrases = [
            "you mentioned", "as you said", "earlier you", "previously",
            "going back to", "returning to", "as we discussed"
        ]
        
        for phrase in context_phrases:
            if phrase in agent_lower:
                indicators.append(f"direct_reference: {phrase}")
        
        # Information integration
        if len(conversation_log) > 2:  # Need some history to integrate
            user_messages = [msg['message'] for msg in conversation_log if msg.get('type') == 'user']
            
            # Check if agent response integrates information from multiple user messages
            integration_words = ["both", "also", "additionally", "furthermore", "combined with"]
            for word in integration_words:
                if word in agent_lower:
                    indicators.append(f"information_integration: {word}")
        
        return indicators
    
    def run_all_topic_switching_scenarios(self, difficulty_filter: str = None) -> Dict:
        """Run all topic switching scenarios or filter by difficulty"""
        print("\n>> PHASE 3: TOPIC SWITCHING EDGE CASE TESTING")
        print("=" * 70)
        
        all_scenarios = phase3_topic_switching.get_all_scenarios()
        
        if difficulty_filter:
            scenarios_to_run = phase3_topic_switching.get_scenarios_by_difficulty(difficulty_filter)
            print(f"Running {len(scenarios_to_run)} scenarios (difficulty: {difficulty_filter})")
        else:
            scenarios_to_run = all_scenarios
            print(f"Running all {len(scenarios_to_run)} topic switching scenarios")
        
        print()
        
        all_results = []
        scenario_summary = defaultdict(list)
        persona_summary = defaultdict(list)
        difficulty_summary = defaultdict(list)
        
        for scenario in scenarios_to_run:
            print(f">> Running scenario: {scenario.name} ({scenario.difficulty_level})")
            
            # Run scenario with each target persona
            for persona_id in scenario.target_personas:
                result = self.run_topic_switching_test(scenario, persona_id)
                all_results.append(result)
                
                # Collect data for analysis
                scenario_summary[scenario.id].append(result)
                persona_summary[persona_id].append(result)
                difficulty_summary[scenario.difficulty_level].append(result)
                
                time.sleep(2)  # Brief pause between tests
        
        # Generate comprehensive analysis
        comprehensive_analysis = self._generate_topic_switching_analysis(
            scenario_summary, persona_summary, difficulty_summary
        )
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = config.SIMULATION_ROOT / "results" / f"phase3_topic_switching_{timestamp}.json"
        
        complete_results = {
            "phase": "Phase 3 - Topic Switching Edge Cases",
            "timestamp": datetime.now().isoformat(),
            "difficulty_filter": difficulty_filter,
            "summary": {
                "total_scenarios": len(scenarios_to_run),
                "total_tests": len(all_results),
                "successful_tests": sum(1 for r in all_results if r.get('success', False)),
                "success_rate": sum(1 for r in all_results if r.get('success', False)) / len(all_results) * 100 if all_results else 0
            },
            "individual_results": all_results,
            "comprehensive_analysis": comprehensive_analysis
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(complete_results, f, indent=2, default=str)
        
        self.print_topic_switching_summary(complete_results)
        
        return complete_results
    
    def _generate_topic_switching_analysis(self, scenario_summary: Dict, 
                                          persona_summary: Dict, 
                                          difficulty_summary: Dict) -> Dict:
        """Generate comprehensive topic switching analysis"""
        analysis = {
            "scenario_performance": {},
            "persona_adaptability": {},
            "difficulty_analysis": {},
            "topic_switching_insights": [],
            "context_retention_analysis": {},
            "agent_adaptability_metrics": {}
        }
        
        # Scenario-specific analysis
        for scenario_id, results in scenario_summary.items():
            successful = sum(1 for r in results if r.get('success', False))
            total = len(results)
            
            # Topic switching metrics
            switch_success_rates = [r['topic_switches']['success_rate'] for r in results]
            context_scores = [r['context_retention']['retention_score'] for r in results]
            adaptability_scores = [r['agent_adaptability']['score'] for r in results]
            
            analysis["scenario_performance"][scenario_id] = {
                "success_rate": successful / total * 100 if total > 0 else 0,
                "total_tests": total,
                "avg_switch_success": sum(switch_success_rates) / len(switch_success_rates) if switch_success_rates else 0,
                "avg_context_retention": sum(context_scores) / len(context_scores) if context_scores else 0,
                "avg_adaptability": sum(adaptability_scores) / len(adaptability_scores) if adaptability_scores else 0
            }
        
        # Persona adaptability analysis  
        for persona_id, results in persona_summary.items():
            successful = sum(1 for r in results if r.get('success', False))
            total = len(results)
            
            # Calculate adaptability metrics
            adaptability_scores = [r['agent_adaptability']['score'] for r in results]
            context_events = [r['context_retention']['events_detected'] for r in results]
            
            analysis["persona_adaptability"][persona_id] = {
                "success_rate": successful / total * 100 if total > 0 else 0,
                "total_scenarios": total,
                "avg_adaptability_score": sum(adaptability_scores) / len(adaptability_scores) if adaptability_scores else 0,
                "avg_context_events": sum(context_events) / len(context_events) if context_events else 0,
                "strengths": self._identify_persona_topic_strengths(results),
                "challenges": self._identify_persona_topic_challenges(results)
            }
        
        # Difficulty-based analysis
        for difficulty, results in difficulty_summary.items():
            successful = sum(1 for r in results if r.get('success', False))
            total = len(results)
            
            analysis["difficulty_analysis"][difficulty] = {
                "success_rate": successful / total * 100 if total > 0 else 0,
                "total_tests": total,
                "avg_response_time": sum(r.get('total_response_time', 0) for r in results) / total if total > 0 else 0,
                "complexity_indicators": self._analyze_difficulty_complexity(results)
            }
        
        # Generate insights
        analysis["topic_switching_insights"] = self._generate_topic_insights(
            scenario_summary, persona_summary, difficulty_summary
        )
        
        return analysis
    
    def _identify_persona_topic_strengths(self, results: List[Dict]) -> List[str]:
        """Identify persona strengths in topic switching scenarios"""
        strengths = []
        
        avg_success = sum(1 for r in results if r.get('success', False)) / len(results) if results else 0
        avg_adaptability = sum(r['agent_adaptability']['score'] for r in results) / len(results) if results else 0
        avg_switches = sum(r['topic_switches']['success_rate'] for r in results) / len(results) if results else 0
        
        if avg_success > 0.7:
            strengths.append("High success rate with topic switching")
        if avg_adaptability > 0.8:
            strengths.append("Excellent agent adaptability")
        if avg_switches > 0.8:
            strengths.append("Smooth topic transitions")
        
        return strengths or ["Consistent performance"]
    
    def _identify_persona_topic_challenges(self, results: List[Dict]) -> List[str]:
        """Identify persona challenges in topic switching scenarios"""
        challenges = []
        
        avg_success = sum(1 for r in results if r.get('success', False)) / len(results) if results else 0
        avg_context = sum(r['context_retention']['retention_score'] for r in results) / len(results) if results else 0
        
        if avg_success < 0.3:
            challenges.append("Low success rate with complex topic switches")
        if avg_context < 0.2:
            challenges.append("Difficulty maintaining context across topics")
        
        return challenges or ["No significant challenges identified"]
    
    def _analyze_difficulty_complexity(self, results: List[Dict]) -> Dict:
        """Analyze complexity indicators by difficulty level"""
        return {
            "avg_switches_per_scenario": sum(r['topic_switches']['planned'] for r in results) / len(results) if results else 0,
            "avg_conversation_length": sum(r.get('conversation_length', 0) for r in results) / len(results) if results else 0,
            "context_retention_events": sum(r['context_retention']['events_detected'] for r in results)
        }
    
    def _generate_topic_insights(self, scenario_summary: Dict, 
                                persona_summary: Dict, 
                                difficulty_summary: Dict) -> List[str]:
        """Generate actionable insights about topic switching performance"""
        insights = []
        
        # Overall performance insights
        all_results = [r for results in scenario_summary.values() for r in results]
        total_success_rate = sum(1 for r in all_results if r.get('success', False)) / len(all_results) if all_results else 0
        
        if total_success_rate < 0.5:
            insights.append(f"Topic switching success rate ({total_success_rate:.1%}) needs improvement")
        else:
            insights.append(f"Good topic switching handling ({total_success_rate:.1%})")
        
        # Difficulty analysis
        for difficulty, results in difficulty_summary.items():
            success_rate = sum(1 for r in results if r.get('success', False)) / len(results) if results else 0
            if success_rate < 0.3 and difficulty in ['hard', 'extreme']:
                insights.append(f"{difficulty.capitalize()} scenarios showing expected challenges ({success_rate:.1%})")
            elif success_rate > 0.7 and difficulty in ['easy', 'medium']:
                insights.append(f"{difficulty.capitalize()} scenarios performing well ({success_rate:.1%})")
        
        # Context retention insights
        context_scores = [r['context_retention']['retention_score'] for r in all_results]
        avg_context = sum(context_scores) / len(context_scores) if context_scores else 0
        
        if avg_context < 0.3:
            insights.append("Context retention needs significant improvement")
        elif avg_context > 0.6:
            insights.append("Good context retention across topic switches")
        
        return insights
    
    def print_topic_switching_summary(self, results: Dict):
        """Print comprehensive topic switching test summary"""
        print("\n" + "="*80)
        print(">> PHASE 3: TOPIC SWITCHING EDGE CASE TESTING RESULTS")
        print("="*80)
        
        summary = results["summary"]
        print(f"\n>> Overall Performance:")
        print(f"   Total Scenarios: {summary['total_scenarios']}")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        # Analysis results
        analysis = results["comprehensive_analysis"]
        
        print(f"\n>> Scenario Performance:")
        for scenario_id, perf in analysis["scenario_performance"].items():
            print(f"   {scenario_id}: {perf['success_rate']:.1f}% success")
            print(f"      Switch Success: {perf['avg_switch_success']:.2f}, Context: {perf['avg_context_retention']:.2f}")
        
        print(f"\n>> Persona Adaptability:")
        for persona_id, perf in analysis["persona_adaptability"].items():
            print(f"   {persona_id}: {perf['success_rate']:.1f}% success")
            print(f"      Adaptability Score: {perf['avg_adaptability_score']:.2f}")
        
        print(f"\n>> Difficulty Analysis:")
        for difficulty, perf in analysis["difficulty_analysis"].items():
            print(f"   {difficulty.capitalize()}: {perf['success_rate']:.1f}% success")
            print(f"      Avg Response Time: {perf['avg_response_time']:.2f}s")
        
        print(f"\n>> Key Insights:")
        for insight in analysis["topic_switching_insights"]:
            print(f"   - {insight}")
        
        print("\n" + "="*80 + "\n")


def main():
    """Main topic switching testing entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3 Topic Switching Edge Case Testing")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard", "extreme"], 
                       help="Filter scenarios by difficulty level")
    parser.add_argument("--scenario-id", help="Run specific scenario by ID")
    
    args = parser.parse_args()
    
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        print("X Configuration issues found:")
        for issue in config_issues:
            print(f"   - {issue}")
        return
    
    print(">> Phase 3: Topic Switching Edge Case Testing")
    config.print_config_summary()
    
    # Run tests
    runner = Phase3TopicSwitchingRunner()
    
    if args.scenario_id:
        # Run specific scenario
        scenario = phase3_topic_switching.get_scenario_by_id(args.scenario_id)
        if scenario:
            print(f"\n>> Running specific scenario: {scenario.name}")
            for persona_id in scenario.target_personas:
                result = runner.run_topic_switching_test(scenario, persona_id)
                print(f"\nResult for {persona_id}: {'PASSED' if result.get('success') else 'FAILED'}")
        else:
            print(f"X Scenario '{args.scenario_id}' not found")
    else:
        # Run all scenarios (with optional difficulty filter)
        results = runner.run_all_topic_switching_scenarios(args.difficulty)
        
        print(f"\n>> Topic Switching Testing Completed!")
        print(f"   Results saved to: simulation_testing/results/phase3_topic_switching_*.json")


if __name__ == "__main__":
    main()