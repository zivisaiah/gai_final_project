"""
Phase 3: Concurrent User Testing Runner
Advanced testing for multiple simultaneous users and conversations
"""

import sys
import time
import json
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import components
from simulation_testing.config.test_config import config
from simulation_testing.personas.persona_loader import persona_loader
from simulation_testing.metrics.metrics_collector import metrics_collector
from simulation_testing.agents.smart_mock_agent import SmartMockAgent
from simulation_testing.scenarios.phase3_concurrent_testing import (
    phase3_concurrent_testing, ConcurrentTestScenario, ConcurrentUser,
    ConcurrentResourceMonitor, validate_concurrent_test_scenario
)
from simulation_testing.simulation_engine import SimulatedUser
import logging


class ConcurrentConversationRunner:
    """Handles individual concurrent conversation execution"""
    
    def __init__(self, user: ConcurrentUser, agent: SmartMockAgent, monitor: ConcurrentResourceMonitor):
        self.user = user
        self.agent = agent
        self.monitor = monitor
        self.logger = logging.getLogger(f"{__name__}.{user.user_id}")
        
    def run_conversation(self) -> Dict[str, Any]:
        """Run a single conversation for this concurrent user"""
        start_time = time.time()
        conversation_id = f"concurrent_{self.user.user_id}_{int(start_time)}"
        
        # Apply start delay
        if self.user.start_delay > 0:
            time.sleep(self.user.start_delay)
        
        # Start metrics collection
        persona_data = persona_loader.get_persona(self.user.persona_id)
        persona_type = persona_data.get('type', 'Unknown') if persona_data else 'Unknown'
        
        try:
            conv_metrics = metrics_collector.start_conversation(
                conversation_id, self.user.persona_id, persona_type
            )
        except Exception as e:
            self.logger.error(f"Failed to start metrics for {conversation_id}: {e}")
            return {"error": f"Metrics initialization failed: {e}", "user_id": self.user.user_id}
        
        self.logger.info(f">> Starting concurrent conversation: {conversation_id}")
        self.logger.info(f"   User: {self.user.user_id}, Persona: {persona_type}")
        
        # Initialize simulated user
        try:
            simulated_user = SimulatedUser(self.user.persona_id)
        except ValueError as e:
            metrics_collector.record_error(conversation_id, str(e))
            return {"error": str(e), "user_id": self.user.user_id}
        
        # Run conversation
        success = False
        conversation_log = []
        decisions_made = []
        response_times = []
        errors = []
        
        try:
            # Record start time for monitoring
            actual_start_time = time.time()
            self.monitor.record_metric("active_connections", 1, actual_start_time)
            
            # Initial greeting
            agent_message = f"Hello! Thank you for your interest in our Python developer position. Could you tell me a bit about yourself and your experience?"
            
            conversation_log.append({
                'type': 'agent',
                'message': agent_message,
                'timestamp': time.time()
            })
            
            # Run conversation for specified length
            for turn in range(self.user.conversation_length):
                metrics_collector.increment_message_count(conversation_id)
                
                # Add behavioral variation to timing
                base_interval = self.user.message_interval
                variation = random.uniform(-self.user.behavior_variation, self.user.behavior_variation)
                actual_interval = max(0.1, base_interval + (base_interval * variation))
                
                if turn > 0:  # Skip delay for first message
                    time.sleep(actual_interval)
                
                # Generate user response
                user_message = simulated_user.generate_response(
                    agent_message, {'conversation_log': conversation_log}
                )
                
                conversation_log.append({
                    'type': 'user',
                    'message': user_message,
                    'timestamp': time.time()
                })
                
                # Agent processing with timing
                agent_start_time = time.time()
                try:
                    agent_response, decision, reasoning = self.agent.process_message(
                        user_message, conversation_id
                    )
                    agent_response_time = time.time() - agent_start_time
                    response_times.append(agent_response_time)
                    
                    # Record performance metrics
                    self.monitor.record_metric("response_times", agent_response_time)
                    
                except Exception as e:
                    agent_response_time = time.time() - agent_start_time
                    error_msg = f"Agent processing error: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(f"Agent error in {conversation_id}: {e}")
                    
                    # Provide fallback response
                    agent_response = "I apologize, but I'm experiencing some technical difficulties. Could you please repeat that?"
                    decision = "CONTINUE"
                    reasoning = "Fallback due to processing error"
                
                decisions_made.append(decision)
                
                # Record metrics
                metrics_collector.record_agent_decision(
                    conversation_id, decision, reasoning, agent_response_time
                )
                
                conversation_log.append({
                    'type': 'agent',
                    'message': agent_response,
                    'decision': decision,
                    'reasoning': reasoning,
                    'response_time': agent_response_time,
                    'timestamp': time.time()
                })
                
                # Check for early termination conditions
                if decision == 'SCHEDULE':
                    if simulated_user.should_accept_scheduling({'conversation_log': conversation_log}):
                        success = True
                        self.logger.info(f"Conversation {conversation_id} completed successfully with scheduling")
                        break
                elif decision == 'END':
                    self.logger.info(f"Conversation {conversation_id} ended by agent decision")
                    break
                    
                # Check if user wants to continue
                if not simulated_user.should_continue_conversation({'conversation_log': conversation_log}):
                    self.logger.info(f"Conversation {conversation_id} ended by user choice")
                    break
                
                agent_message = agent_response
            
            # If we completed all turns without early termination, consider it a success
            if not success and len(conversation_log) >= self.user.conversation_length * 2:  # Each turn = 2 messages
                success = True
                self.logger.info(f"Conversation {conversation_id} completed full length successfully")
                
        except Exception as e:
            error_msg = f"Conversation execution error: {str(e)}"
            errors.append(error_msg)
            self.logger.error(f"Critical error in {conversation_id}: {e}")
        
        finally:
            # Record end time and cleanup
            end_time = time.time()
            self.monitor.record_metric("active_connections", -1, end_time)
            
            # Complete metrics
            completion_stage = "completed" if success else "ended"
            try:
                metrics_collector.complete_conversation(conversation_id, success, completion_stage)
            except Exception as e:
                self.logger.error(f"Failed to complete metrics for {conversation_id}: {e}")
        
        # Calculate conversation metrics
        duration = time.time() - actual_start_time
        user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
        
        # Estimate decision accuracy (simplified)
        decision_accuracy = 0.8 if success else 0.4  # Placeholder calculation
        
        # Estimate context retention (simplified)
        context_retention_score = min(1.0, len(conversation_log) / (self.user.conversation_length * 2))
        
        result = {
            "user_id": self.user.user_id,
            "conversation_id": conversation_id,
            "persona_id": self.user.persona_id,
            "persona_type": persona_type,
            "success": success,
            "duration": duration,
            "start_time": actual_start_time,
            "end_time": time.time(),
            "message_count": len(user_messages),
            "decisions_made": decisions_made,
            "response_times": response_times,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "errors": errors,
            "decision_accuracy": decision_accuracy,
            "context_retention_score": context_retention_score,
            "conversation_log": conversation_log if config.SAVE_CONVERSATION_TRANSCRIPTS else None
        }
        
        self.logger.info(f"Conversation {conversation_id} completed: {'SUCCESS' if success else 'FAILED'}")
        self.logger.info(f"   Duration: {duration:.1f}s, Messages: {len(user_messages)}, Avg Response: {result['avg_response_time']:.2f}s")
        
        return result


class Phase3ConcurrentRunner:
    """Advanced test runner for Phase 3 concurrent user scenarios"""
    
    def __init__(self, max_workers: int = 10):
        self.setup_logging()
        self.max_workers = max_workers
        self.resource_monitor = ConcurrentResourceMonitor()
        self.test_results = {}
        
        # Create a shared agent for all concurrent users
        self.shared_agent = SmartMockAgent("ConcurrentTestAgent")
        
    def setup_logging(self):
        """Set up enhanced logging for Phase 3 concurrent tests"""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.SIMULATION_ROOT / "results" / "phase3_concurrent.log"),
                logging.StreamHandler() if config.CONSOLE_OUTPUT else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_concurrent_test(self, scenario: ConcurrentTestScenario) -> Dict[str, Any]:
        """Run a complete concurrent test scenario"""
        self.logger.info(f">> Starting concurrent test: {scenario.name}")
        self.logger.info(f"   Users: {len(scenario.concurrent_users)}, Max Concurrent: {scenario.max_concurrent_users}")
        self.logger.info(f"   Duration: {scenario.test_duration_seconds}s, Pattern: {scenario.load_pattern.value}")
        
        if config.CONSOLE_OUTPUT:
            print(f"\n{'='*80}")
            print(f">> CONCURRENT TEST: {scenario.name}")
            print(f"   Users: {len(scenario.concurrent_users)}")
            print(f"   Max Concurrent: {scenario.max_concurrent_users}")
            print(f"   Expected Duration: {scenario.test_duration_seconds}s")
            print(f"   Difficulty: {scenario.difficulty_level}")
            print(f"{'='*80}")
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        test_start_time = time.time()
        
        # Prepare conversation runners
        conversation_runners = []
        for user in scenario.concurrent_users:
            runner = ConcurrentConversationRunner(user, self.shared_agent, self.resource_monitor)
            conversation_runners.append(runner)
        
        # Execute concurrent conversations
        all_results = []
        timing_data = {
            "test_start_time": test_start_time,
            "baseline_response_time": 1.5,  # Baseline from previous tests
            "max_concurrent_active": 0,
            "system_overload_detected": False
        }
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all conversation tasks
                future_to_runner = {
                    executor.submit(runner.run_conversation): runner 
                    for runner in conversation_runners
                }
                
                # Monitor progress and collect results
                active_conversations = 0
                max_active = 0
                
                for future in as_completed(future_to_runner):
                    try:
                        result = future.result(timeout=scenario.test_duration_seconds)
                        all_results.append(result)
                        
                        # Update monitoring
                        current_time = time.time()
                        if result.get('start_time'):
                            active_conversations += 1
                            max_active = max(max_active, active_conversations)
                        if result.get('end_time'):
                            active_conversations = max(0, active_conversations - 1)
                        
                        # Check for system overload indicators
                        if result.get('max_response_time', 0) > timing_data['baseline_response_time'] * 5:
                            timing_data['system_overload_detected'] = True
                        
                        if config.CONSOLE_OUTPUT:
                            status = "SUCCESS" if result.get('success') else "FAILED"
                            duration = result.get('duration', 0)
                            avg_response = result.get('avg_response_time', 0)
                            print(f"   User {result.get('user_id')}: {status} ({duration:.1f}s, {avg_response:.2f}s avg)")
                        
                    except Exception as e:
                        self.logger.error(f"Concurrent conversation failed: {e}")
                        error_result = {
                            "error": str(e),
                            "user_id": getattr(future_to_runner.get(future), 'user', {}).get('user_id', 'unknown'),
                            "success": False,
                            "duration": 0,
                            "start_time": time.time(),
                            "end_time": time.time()
                        }
                        all_results.append(error_result)
                
                timing_data['max_concurrent_active'] = max_active
        
        except Exception as e:
            self.logger.error(f"Critical error during concurrent test execution: {e}")
            return {"error": str(e), "scenario_id": scenario.id}
        
        finally:
            # Stop resource monitoring
            test_end_time = time.time()
            self.resource_monitor.stop_monitoring()
        
        # Collect resource metrics
        resource_metrics = self.resource_monitor.get_all_metrics_summary()
        
        # Calculate additional timing metrics
        if all_results:
            start_times = [r.get('start_time', 0) for r in all_results if r.get('start_time')]
            end_times = [r.get('end_time', 0) for r in all_results if r.get('end_time')]
            response_times = []
            
            for result in all_results:
                if 'response_times' in result:
                    response_times.extend(result['response_times'])
            
            timing_data.update({
                "actual_test_duration": test_end_time - test_start_time,
                "first_conversation_start": min(start_times) if start_times else test_start_time,
                "last_conversation_end": max(end_times) if end_times else test_end_time,
                "total_response_times": len(response_times),
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0
            })
        
        # Validate scenario results
        validation_results = validate_concurrent_test_scenario(
            scenario, all_results, resource_metrics, timing_data
        )
        
        # Generate comprehensive test result
        test_result = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "test_completed": True,
            "total_users": len(scenario.concurrent_users),
            "successful_conversations": sum(1 for r in all_results if r.get('success', False)),
            "failed_conversations": sum(1 for r in all_results if not r.get('success', False)),
            "success_rate": sum(1 for r in all_results if r.get('success', False)) / len(all_results) if all_results else 0,
            "timing_data": timing_data,
            "resource_metrics": resource_metrics,
            "validation_results": validation_results,
            "individual_results": all_results,
            "scenario_difficulty": scenario.difficulty_level,
            "concurrency_type": scenario.concurrency_type.value,
            "load_pattern": scenario.load_pattern.value
        }
        
        if config.CONSOLE_OUTPUT:
            print(f"\n>> Concurrent Test Result: {'PASSED' if validation_results.get('overall_success') else 'FAILED'}")
            print(f"   Success Rate: {test_result['success_rate']:.1%} ({test_result['successful_conversations']}/{test_result['total_users']})")
            print(f"   Max Concurrent: {timing_data['max_concurrent_active']}")
            print(f"   Avg Response Time: {timing_data['avg_response_time']:.2f}s")
            print(f"   Test Duration: {timing_data['actual_test_duration']:.1f}s")
            print(f"{'='*80}\n")
        
        return test_result
    
    def run_all_concurrent_scenarios(self, difficulty_filter: str = None, max_users_filter: int = None) -> Dict:
        """Run all concurrent scenarios or filter by criteria"""
        print("\n>> PHASE 3: CONCURRENT USER TESTING")
        print("=" * 60)
        
        all_scenarios = phase3_concurrent_testing.get_all_scenarios()
        
        # Apply filters
        scenarios_to_run = all_scenarios
        
        if difficulty_filter:
            scenarios_to_run = [s for s in scenarios_to_run if s.difficulty_level == difficulty_filter]
            
        if max_users_filter:
            scenarios_to_run = [s for s in scenarios_to_run if s.max_concurrent_users <= max_users_filter]
        
        print(f"Running {len(scenarios_to_run)} concurrent scenarios")
        if difficulty_filter:
            print(f"  Difficulty filter: {difficulty_filter}")
        if max_users_filter:
            print(f"  Max users filter: {max_users_filter}")
        print()
        
        all_results = []
        scenario_summary = {}
        
        for scenario in scenarios_to_run:
            print(f">> Running scenario: {scenario.name}")
            print(f"   {len(scenario.concurrent_users)} users, max {scenario.max_concurrent_users} concurrent")
            
            try:
                result = self.run_concurrent_test(scenario)
                all_results.append(result)
                scenario_summary[scenario.id] = result
                
                # Brief pause between scenarios to allow system recovery
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Failed to run scenario {scenario.id}: {e}")
                error_result = {
                    "scenario_id": scenario.id,
                    "error": str(e),
                    "test_completed": False,
                    "success_rate": 0.0
                }
                all_results.append(error_result)
                scenario_summary[scenario.id] = error_result
        
        # Generate comprehensive analysis
        comprehensive_analysis = self._generate_concurrent_analysis(scenario_summary)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = config.SIMULATION_ROOT / "results" / f"phase3_concurrent_{timestamp}.json"
        
        complete_results = {
            "phase": "Phase 3 - Concurrent User Testing",
            "timestamp": datetime.now().isoformat(),
            "filters_applied": {
                "difficulty": difficulty_filter,
                "max_users": max_users_filter
            },
            "summary": {
                "total_scenarios": len(scenarios_to_run),
                "successful_scenarios": sum(1 for r in all_results if r.get('validation_results', {}).get('overall_success', False)),
                "total_simulated_users": sum(r.get('total_users', 0) for r in all_results),
                "overall_success_rate": sum(r.get('success_rate', 0) for r in all_results) / len(all_results) if all_results else 0,
                "avg_concurrent_users": sum(r.get('timing_data', {}).get('max_concurrent_active', 0) for r in all_results) / len(all_results) if all_results else 0
            },
            "individual_results": all_results,
            "comprehensive_analysis": comprehensive_analysis
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(complete_results, f, indent=2, default=str)
        
        self.print_concurrent_summary(complete_results)
        
        return complete_results
    
    def _generate_concurrent_analysis(self, scenario_summary: Dict) -> Dict[str, Any]:
        """Generate comprehensive concurrent testing analysis"""
        analysis = {
            "performance_analysis": {},
            "scalability_analysis": {},
            "reliability_analysis": {},
            "resource_utilization": {},
            "concurrency_insights": []
        }
        
        # Performance analysis
        all_response_times = []
        all_success_rates = []
        max_concurrent_users = []
        
        for scenario_id, result in scenario_summary.items():
            if result.get('test_completed'):
                timing_data = result.get('timing_data', {})
                all_response_times.append(timing_data.get('avg_response_time', 0))
                all_success_rates.append(result.get('success_rate', 0))
                max_concurrent_users.append(timing_data.get('max_concurrent_active', 0))
        
        analysis["performance_analysis"] = {
            "avg_response_time_across_scenarios": sum(all_response_times) / len(all_response_times) if all_response_times else 0,
            "best_response_time": min(all_response_times) if all_response_times else 0,
            "worst_response_time": max(all_response_times) if all_response_times else 0,
            "response_time_consistency": 1.0 - (max(all_response_times) - min(all_response_times)) / max(all_response_times) if all_response_times else 1.0
        }
        
        # Scalability analysis
        analysis["scalability_analysis"] = {
            "max_users_tested": max(max_concurrent_users) if max_concurrent_users else 0,
            "avg_concurrent_capacity": sum(max_concurrent_users) / len(max_concurrent_users) if max_concurrent_users else 0,
            "success_rate_vs_concurrency": self._analyze_success_vs_concurrency(scenario_summary),
            "scalability_score": sum(all_success_rates) / len(all_success_rates) if all_success_rates else 0
        }
        
        # Reliability analysis
        completed_tests = sum(1 for result in scenario_summary.values() if result.get('test_completed', False))
        total_tests = len(scenario_summary)
        
        analysis["reliability_analysis"] = {
            "test_completion_rate": completed_tests / total_tests if total_tests > 0 else 0,
            "avg_success_rate": sum(all_success_rates) / len(all_success_rates) if all_success_rates else 0,
            "reliability_score": (completed_tests / total_tests) * (sum(all_success_rates) / len(all_success_rates)) if total_tests > 0 and all_success_rates else 0
        }
        
        # Resource utilization (aggregated from all scenarios)
        total_peak_memory = 0
        total_avg_cpu = 0
        scenarios_with_resources = 0
        
        for result in scenario_summary.values():
            resource_metrics = result.get('resource_metrics', {})
            if resource_metrics:
                scenarios_with_resources += 1
                total_peak_memory += resource_metrics.get('memory_usage', {}).get('max', 0)
                total_avg_cpu += resource_metrics.get('cpu_usage', {}).get('avg', 0)
        
        analysis["resource_utilization"] = {
            "avg_peak_memory": total_peak_memory / scenarios_with_resources if scenarios_with_resources > 0 else 0,
            "avg_cpu_usage": total_avg_cpu / scenarios_with_resources if scenarios_with_resources > 0 else 0,
            "resource_efficiency": 1.0,  # Placeholder - would calculate based on resource usage vs performance
            "memory_stability": all(not result.get('resource_metrics', {}).get('memory_leak_detected', False) 
                                   for result in scenario_summary.values())
        }
        
        # Generate insights
        analysis["concurrency_insights"] = self._generate_concurrency_insights(scenario_summary, analysis)
        
        return analysis
    
    def _analyze_success_vs_concurrency(self, scenario_summary: Dict) -> List[Dict]:
        """Analyze how success rate correlates with concurrency level"""
        data_points = []
        
        for scenario_id, result in scenario_summary.items():
            if result.get('test_completed'):
                concurrent_users = result.get('timing_data', {}).get('max_concurrent_active', 0)
                success_rate = result.get('success_rate', 0)
                
                data_points.append({
                    "concurrent_users": concurrent_users,
                    "success_rate": success_rate,
                    "scenario": scenario_id
                })
        
        # Sort by concurrent users for trend analysis
        data_points.sort(key=lambda x: x['concurrent_users'])
        
        return data_points
    
    def _generate_concurrency_insights(self, scenario_summary: Dict, analysis: Dict) -> List[str]:
        """Generate actionable insights about concurrent performance"""
        insights = []
        
        # Overall performance insights
        avg_success_rate = analysis["reliability_analysis"]["avg_success_rate"]
        if avg_success_rate >= 0.8:
            insights.append(f"Excellent concurrent performance ({avg_success_rate:.1%} success rate)")
        elif avg_success_rate >= 0.6:
            insights.append(f"Good concurrent performance ({avg_success_rate:.1%} success rate)")
        else:
            insights.append(f"Concurrent performance needs improvement ({avg_success_rate:.1%} success rate)")
        
        # Scalability insights
        max_users = analysis["scalability_analysis"]["max_users_tested"]
        if max_users >= 10:
            insights.append(f"Successfully tested up to {max_users} concurrent users")
        elif max_users >= 5:
            insights.append(f"Tested with {max_users} concurrent users - consider higher loads")
        else:
            insights.append(f"Limited concurrency testing ({max_users} users) - expand test coverage")
        
        # Performance insights
        avg_response_time = analysis["performance_analysis"]["avg_response_time_across_scenarios"]
        if avg_response_time <= 2.0:
            insights.append("Excellent response times under concurrent load")
        elif avg_response_time <= 5.0:
            insights.append("Acceptable response times under concurrent load")
        else:
            insights.append(f"Response times degraded under load ({avg_response_time:.1f}s average)")
        
        # Resource insights
        memory_stable = analysis["resource_utilization"]["memory_stability"]
        if memory_stable:
            insights.append("Memory usage remained stable across all concurrent tests")
        else:
            insights.append("Memory leaks detected during concurrent testing")
        
        return insights
    
    def print_concurrent_summary(self, results: Dict):
        """Print comprehensive concurrent testing summary"""
        print("\n" + "="*80)
        print(">> PHASE 3: CONCURRENT USER TESTING RESULTS")
        print("="*80)
        
        summary = results["summary"]
        print(f"\n>> Overall Performance:")
        print(f"   Total Scenarios: {summary['total_scenarios']}")
        print(f"   Successful Scenarios: {summary['successful_scenarios']}")
        print(f"   Total Simulated Users: {summary['total_simulated_users']}")
        print(f"   Overall Success Rate: {summary['overall_success_rate']:.1%}")
        print(f"   Avg Concurrent Users: {summary['avg_concurrent_users']:.1f}")
        
        # Analysis results
        analysis = results["comprehensive_analysis"]
        
        print(f"\n>> Performance Analysis:")
        perf = analysis["performance_analysis"]
        print(f"   Avg Response Time: {perf['avg_response_time_across_scenarios']:.2f}s")
        print(f"   Best Response Time: {perf['best_response_time']:.2f}s")
        print(f"   Worst Response Time: {perf['worst_response_time']:.2f}s")
        print(f"   Response Consistency: {perf['response_time_consistency']:.2f}")
        
        print(f"\n>> Scalability Analysis:")
        scale = analysis["scalability_analysis"]
        print(f"   Max Users Tested: {scale['max_users_tested']}")
        print(f"   Avg Concurrent Capacity: {scale['avg_concurrent_capacity']:.1f}")
        print(f"   Scalability Score: {scale['scalability_score']:.2f}")
        
        print(f"\n>> Reliability Analysis:")
        rel = analysis["reliability_analysis"]
        print(f"   Test Completion Rate: {rel['test_completion_rate']:.1%}")
        print(f"   Avg Success Rate: {rel['avg_success_rate']:.1%}")
        print(f"   Reliability Score: {rel['reliability_score']:.2f}")
        
        print(f"\n>> Key Insights:")
        for insight in analysis["concurrency_insights"]:
            print(f"   - {insight}")
        
        print("\n" + "="*80 + "\n")


def main():
    """Main concurrent testing entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 3 Concurrent User Testing")
    parser.add_argument("--difficulty", choices=["medium", "high", "extreme"], 
                       help="Filter scenarios by difficulty level")
    parser.add_argument("--max-users", type=int, 
                       help="Filter scenarios by maximum concurrent users")
    parser.add_argument("--scenario-id", help="Run specific scenario by ID")
    parser.add_argument("--workers", type=int, default=10,
                       help="Maximum number of worker threads")
    
    args = parser.parse_args()
    
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        print("X Configuration issues found:")
        for issue in config_issues:
            print(f"   - {issue}")
        return
    
    print(">> Phase 3: Concurrent User Testing")
    config.print_config_summary()
    
    # Run tests
    runner = Phase3ConcurrentRunner(max_workers=args.workers)
    
    if args.scenario_id:
        # Run specific scenario
        scenario = phase3_concurrent_testing.get_scenario_by_id(args.scenario_id)
        if scenario:
            print(f"\n>> Running specific scenario: {scenario.name}")
            result = runner.run_concurrent_test(scenario)
            success = result.get('validation_results', {}).get('overall_success', False)
            print(f"\nResult: {'PASSED' if success else 'FAILED'}")
        else:
            print(f"X Scenario '{args.scenario_id}' not found")
    else:
        # Run all scenarios (with optional filters)
        results = runner.run_all_concurrent_scenarios(
            difficulty_filter=args.difficulty,
            max_users_filter=args.max_users
        )
        
        print(f"\n>> Concurrent User Testing Completed!")
        print(f"   Results saved to: simulation_testing/results/phase3_concurrent_*.json")


if __name__ == "__main__":
    main()