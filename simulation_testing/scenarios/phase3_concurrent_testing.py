"""
Phase 3: Concurrent User Testing Scenarios
Testing system behavior with multiple simultaneous users and conversations
"""

import time
import asyncio
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import random


class ConcurrencyType(Enum):
    """Types of concurrency testing scenarios"""
    SIMULTANEOUS_START = "simultaneous_start"
    STAGGERED_START = "staggered_start"
    BURST_LOAD = "burst_load"
    SUSTAINED_LOAD = "sustained_load"
    MIXED_PERSONAS = "mixed_personas"
    RESOURCE_CONTENTION = "resource_contention"
    SCHEDULING_CONFLICTS = "scheduling_conflicts"


class LoadPattern(Enum):
    """Load patterns for concurrent testing"""
    CONSTANT = "constant"
    RAMP_UP = "ramp_up"
    SPIKE = "spike"
    WAVE = "wave"
    RANDOM = "random"


@dataclass
class ConcurrentUser:
    """Represents a concurrent user in the test"""
    user_id: str
    persona_id: str
    start_delay: float = 0.0
    conversation_length: int = 5
    message_interval: float = 2.0
    behavior_variation: float = 0.2  # Random variation in timing
    priority: str = "normal"  # normal, high, low


@dataclass
class ConcurrentTestScenario:
    """A complete concurrent user testing scenario"""
    id: str
    name: str
    description: str
    concurrency_type: ConcurrencyType
    concurrent_users: List[ConcurrentUser]
    load_pattern: LoadPattern
    max_concurrent_users: int
    test_duration_seconds: int
    success_criteria: Dict[str, Any]
    difficulty_level: str
    expected_challenges: List[str]
    resource_monitoring: bool = True


class Phase3ConcurrentTestingScenarios:
    """Phase 3 Concurrent User Testing Scenarios"""
    
    def __init__(self):
        self.scenarios = self._create_scenarios()
    
    def _create_scenarios(self) -> List[ConcurrentTestScenario]:
        """Create comprehensive concurrent testing scenarios"""
        
        scenarios = []
        
        # Scenario 1: Simultaneous Startup Stress Test
        simultaneous_users = []
        personas = ["eager_junior", "experienced_senior", "career_changer", "passive_candidate", "difficult_candidate"]
        
        for i in range(5):
            simultaneous_users.append(ConcurrentUser(
                user_id=f"sim_user_{i+1}",
                persona_id=personas[i],
                start_delay=0.0,  # All start at the same time
                conversation_length=8,
                message_interval=2.5,
                behavior_variation=0.3
            ))
        
        scenarios.append(ConcurrentTestScenario(
            id="concurrent_simultaneous_start",
            name="Simultaneous Startup Stress Test",
            description="5 users starting conversations simultaneously to test system initialization handling",
            concurrency_type=ConcurrencyType.SIMULTANEOUS_START,
            concurrent_users=simultaneous_users,
            load_pattern=LoadPattern.SPIKE,
            max_concurrent_users=5,
            test_duration_seconds=180,
            success_criteria={
                "all_users_served": True,
                "no_initialization_conflicts": True,
                "max_response_degradation": 2.0,
                "successful_completion_rate": 0.8,
                "no_database_locks": True
            },
            difficulty_level="medium",
            expected_challenges=["initialization_bottleneck", "resource_contention"],
            resource_monitoring=True
        ))
        
        # Scenario 2: Staggered Load Ramp-Up Test
        staggered_users = []
        for i in range(7):
            staggered_users.append(ConcurrentUser(
                user_id=f"stag_user_{i+1}",
                persona_id=random.choice(personas),
                start_delay=i * 15.0,  # 15 second intervals
                conversation_length=10,
                message_interval=3.0,
                behavior_variation=0.4
            ))
        
        scenarios.append(ConcurrentTestScenario(
            id="concurrent_staggered_ramp",
            name="Staggered Load Ramp-Up Test",
            description="7 users joining at 15-second intervals to test gradual load scaling",
            concurrency_type=ConcurrencyType.STAGGERED_START,
            concurrent_users=staggered_users,
            load_pattern=LoadPattern.RAMP_UP,
            max_concurrent_users=7,
            test_duration_seconds=300,
            success_criteria={
                "handles_gradual_scaling": True,
                "maintains_performance": True,
                "no_memory_leaks": True,
                "stable_response_times": True,
                "successful_completion_rate": 0.85
            },
            difficulty_level="medium",
            expected_challenges=["memory_accumulation", "context_management"],
            resource_monitoring=True
        ))
        
        # Scenario 3: High Concurrency Burst Test
        burst_users = []
        for i in range(10):
            burst_users.append(ConcurrentUser(
                user_id=f"burst_user_{i+1}",
                persona_id=personas[i % len(personas)],
                start_delay=random.uniform(0, 5),  # Random start within 5 seconds
                conversation_length=6,
                message_interval=1.5,  # Faster interactions
                behavior_variation=0.5
            ))
        
        scenarios.append(ConcurrentTestScenario(
            id="concurrent_burst_load",
            name="High Concurrency Burst Test",
            description="10 users in rapid succession to test maximum concurrent capacity",
            concurrency_type=ConcurrencyType.BURST_LOAD,
            concurrent_users=burst_users,
            load_pattern=LoadPattern.SPIKE,
            max_concurrent_users=10,
            test_duration_seconds=200,
            success_criteria={
                "handles_burst_load": True,
                "no_system_overload": True,
                "graceful_degradation": True,
                "successful_completion_rate": 0.7,  # Lower expectation due to high load
                "queue_management": True
            },
            difficulty_level="high",
            expected_challenges=["resource_exhaustion", "queue_buildup", "response_delays"],
            resource_monitoring=True
        ))
        
        # Scenario 4: Sustained Load Endurance Test
        sustained_users = []
        for i in range(6):
            sustained_users.append(ConcurrentUser(
                user_id=f"sust_user_{i+1}",
                persona_id=personas[i % len(personas)],
                start_delay=i * 10.0,
                conversation_length=15,  # Longer conversations
                message_interval=4.0,
                behavior_variation=0.3
            ))
        
        scenarios.append(ConcurrentTestScenario(
            id="concurrent_sustained_load",
            name="Sustained Load Endurance Test",
            description="6 users with long conversations to test sustained concurrent operations",
            concurrency_type=ConcurrencyType.SUSTAINED_LOAD,
            concurrent_users=sustained_users,
            load_pattern=LoadPattern.CONSTANT,
            max_concurrent_users=6,
            test_duration_seconds=600,  # 10 minutes
            success_criteria={
                "maintains_long_term_stability": True,
                "no_memory_leaks": True,
                "consistent_performance": True,
                "successful_completion_rate": 0.9,
                "resource_cleanup": True
            },
            difficulty_level="high",
            expected_challenges=["memory_management", "long_term_stability", "context_overflow"],
            resource_monitoring=True
        ))
        
        # Scenario 5: Mixed Persona Interaction Test
        mixed_users = []
        persona_counts = {"eager_junior": 2, "experienced_senior": 2, "career_changer": 1, 
                         "passive_candidate": 1, "difficult_candidate": 2}
        
        user_id_counter = 1
        for persona, count in persona_counts.items():
            for _ in range(count):
                mixed_users.append(ConcurrentUser(
                    user_id=f"mixed_user_{user_id_counter}",
                    persona_id=persona,
                    start_delay=random.uniform(0, 20),
                    conversation_length=random.randint(5, 12),
                    message_interval=random.uniform(2.0, 4.0),
                    behavior_variation=0.4
                ))
                user_id_counter += 1
        
        scenarios.append(ConcurrentTestScenario(
            id="concurrent_mixed_personas",
            name="Mixed Persona Interaction Test",
            description="8 users with different personas to test agent adaptability under concurrent load",
            concurrency_type=ConcurrencyType.MIXED_PERSONAS,
            concurrent_users=mixed_users,
            load_pattern=LoadPattern.RANDOM,
            max_concurrent_users=8,
            test_duration_seconds=400,
            success_criteria={
                "handles_persona_diversity": True,
                "maintains_context_separation": True,
                "no_conversation_mixing": True,
                "successful_completion_rate": 0.8,
                "agent_decision_accuracy": 0.75
            },
            difficulty_level="high",
            expected_challenges=["context_isolation", "persona_management", "decision_consistency"],
            resource_monitoring=True
        ))
        
        # Scenario 6: Scheduling Conflict Resolution Test
        scheduling_users = []
        for i in range(6):
            scheduling_users.append(ConcurrentUser(
                user_id=f"sched_user_{i+1}",
                persona_id=random.choice(["eager_junior", "experienced_senior", "career_changer"]),
                start_delay=i * 5.0,
                conversation_length=7,
                message_interval=2.0,
                behavior_variation=0.2,
                priority="high" if i < 2 else "normal"  # First 2 are high priority
            ))
        
        scenarios.append(ConcurrentTestScenario(
            id="concurrent_scheduling_conflicts",
            name="Scheduling Conflict Resolution Test",
            description="6 users attempting to schedule interviews simultaneously to test slot conflict resolution",
            concurrency_type=ConcurrencyType.SCHEDULING_CONFLICTS,
            concurrent_users=scheduling_users,
            load_pattern=LoadPattern.CONSTANT,
            max_concurrent_users=6,
            test_duration_seconds=250,
            success_criteria={
                "prevents_double_booking": True,
                "handles_slot_contention": True,
                "fair_slot_allocation": True,
                "successful_completion_rate": 0.8,
                "no_database_conflicts": True
            },
            difficulty_level="high",
            expected_challenges=["slot_contention", "database_locking", "transaction_conflicts"],
            resource_monitoring=True
        ))
        
        # Scenario 7: Resource Contention Stress Test
        resource_users = []
        for i in range(8):
            resource_users.append(ConcurrentUser(
                user_id=f"res_user_{i+1}",
                persona_id=personas[i % len(personas)],
                start_delay=random.uniform(0, 10),
                conversation_length=8,
                message_interval=1.0,  # Fast interactions to increase load
                behavior_variation=0.6
            ))
        
        scenarios.append(ConcurrentTestScenario(
            id="concurrent_resource_contention",
            name="Resource Contention Stress Test",
            description="8 users with fast interactions to test resource contention handling",
            concurrency_type=ConcurrencyType.RESOURCE_CONTENTION,
            concurrent_users=resource_users,
            load_pattern=LoadPattern.WAVE,
            max_concurrent_users=8,
            test_duration_seconds=320,
            success_criteria={
                "manages_resource_contention": True,
                "no_deadlocks": True,
                "fair_resource_allocation": True,
                "successful_completion_rate": 0.75,
                "maintains_system_stability": True
            },
            difficulty_level="extreme",
            expected_challenges=["api_rate_limiting", "database_contention", "memory_pressure"],
            resource_monitoring=True
        ))
        
        return scenarios
    
    def get_scenario_by_id(self, scenario_id: str) -> Optional[ConcurrentTestScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        return None
    
    def get_scenarios_by_concurrency_type(self, concurrency_type: ConcurrencyType) -> List[ConcurrentTestScenario]:
        """Get scenarios by concurrency type"""
        return [s for s in self.scenarios if s.concurrency_type == concurrency_type]
    
    def get_scenarios_by_difficulty(self, difficulty: str) -> List[ConcurrentTestScenario]:
        """Get scenarios by difficulty level"""
        return [s for s in self.scenarios if s.difficulty_level == difficulty]
    
    def get_scenarios_by_max_users(self, min_users: int, max_users: int = None) -> List[ConcurrentTestScenario]:
        """Get scenarios by user count range"""
        if max_users is None:
            return [s for s in self.scenarios if s.max_concurrent_users >= min_users]
        return [s for s in self.scenarios if min_users <= s.max_concurrent_users <= max_users]
    
    def get_all_scenarios(self) -> List[ConcurrentTestScenario]:
        """Get all concurrent testing scenarios"""
        return self.scenarios
    
    def get_scenario_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all scenarios"""
        total_scenarios = len(self.scenarios)
        difficulty_counts = {}
        concurrency_types = set()
        load_patterns = set()
        
        total_users = 0
        max_users = 0
        min_users = float('inf')
        total_duration = 0
        
        for scenario in self.scenarios:
            # Count by difficulty
            if scenario.difficulty_level not in difficulty_counts:
                difficulty_counts[scenario.difficulty_level] = 0
            difficulty_counts[scenario.difficulty_level] += 1
            
            # Track types and patterns
            concurrency_types.add(scenario.concurrency_type)
            load_patterns.add(scenario.load_pattern)
            
            # User statistics
            user_count = len(scenario.concurrent_users)
            total_users += user_count
            max_users = max(max_users, scenario.max_concurrent_users)
            min_users = min(min_users, scenario.max_concurrent_users)
            total_duration += scenario.test_duration_seconds
        
        return {
            "total_scenarios": total_scenarios,
            "difficulty_distribution": difficulty_counts,
            "concurrency_types_covered": len(concurrency_types),
            "load_patterns_covered": len(load_patterns),
            "total_simulated_users": total_users,
            "max_concurrent_users": max_users,
            "min_concurrent_users": min_users if min_users != float('inf') else 0,
            "avg_concurrent_users": total_users / total_scenarios if total_scenarios > 0 else 0,
            "total_test_duration": total_duration,
            "avg_test_duration": total_duration / total_scenarios if total_scenarios > 0 else 0,
            "scenarios_with_monitoring": len([s for s in self.scenarios if s.resource_monitoring])
        }


# Global instance for easy import
phase3_concurrent_testing = Phase3ConcurrentTestingScenarios()


class ConcurrentResourceMonitor:
    """Monitors system resources during concurrent testing"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "active_connections": [],
            "response_times": [],
            "error_rates": [],
            "database_connections": []
        }
        self.start_time = None
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.start_time = time.time()
        self.metrics = {key: [] for key in self.metrics.keys()}
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
    
    def record_metric(self, metric_name: str, value: Any, timestamp: float = None):
        """Record a metric value"""
        if not self.monitoring:
            return
        
        if timestamp is None:
            timestamp = time.time()
        
        if metric_name in self.metrics:
            self.metrics[metric_name].append({
                "value": value,
                "timestamp": timestamp,
                "elapsed": timestamp - self.start_time if self.start_time else 0
            })
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get summary statistics for a specific metric"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {"error": f"No data for metric {metric_name}"}
        
        values = [entry["value"] for entry in self.metrics[metric_name]]
        
        return {
            "count": len(values),
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "avg": sum(values) / len(values) if values else 0,
            "first": values[0] if values else 0,
            "last": values[-1] if values else 0
        }
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all monitored metrics"""
        summary = {}
        for metric_name in self.metrics.keys():
            summary[metric_name] = self.get_metric_summary(metric_name)
        
        return summary


def validate_concurrent_test_scenario(scenario: ConcurrentTestScenario,
                                     all_conversation_results: List[Dict],
                                     resource_metrics: Dict,
                                     timing_data: Dict) -> Dict[str, Any]:
    """
    Validate if a concurrent test scenario was handled successfully
    
    Args:
        scenario: The concurrent test scenario that was run
        all_conversation_results: Results from all concurrent conversations
        resource_metrics: Resource usage metrics during the test
        timing_data: Timing and performance data
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "scenario_id": scenario.id,
        "overall_success": False,
        "validations": [],
        "concurrency_analysis": {},
        "performance_analysis": {},
        "resource_analysis": {},
        "user_experience_analysis": {}
    }
    
    # Basic success criteria validation
    criteria = scenario.success_criteria
    total_users = len(scenario.concurrent_users)
    successful_conversations = sum(1 for result in all_conversation_results if result.get('success', False))
    completion_rate = successful_conversations / total_users if total_users > 0 else 0
    
    # Completion rate validation
    if 'successful_completion_rate' in criteria:
        expected_rate = criteria['successful_completion_rate']
        passed = completion_rate >= expected_rate
        validation_results["validations"].append({
            "criteria": "successful_completion_rate",
            "expected": expected_rate,
            "actual": completion_rate,
            "passed": passed
        })
    
    # Response time degradation validation
    if 'max_response_degradation' in criteria:
        baseline_time = timing_data.get('baseline_response_time', 1.0)
        max_concurrent_time = timing_data.get('max_response_time', 0.0)
        degradation = max_concurrent_time / baseline_time if baseline_time > 0 else 1.0
        
        passed = degradation <= criteria['max_response_degradation']
        validation_results["validations"].append({
            "criteria": "max_response_degradation",
            "expected": criteria['max_response_degradation'],
            "actual": degradation,
            "passed": passed
        })
    
    # No system overload validation
    if 'no_system_overload' in criteria:
        system_overload = timing_data.get('system_overload_detected', False)
        passed = not system_overload
        validation_results["validations"].append({
            "criteria": "no_system_overload",
            "expected": True,
            "actual": not system_overload,
            "passed": passed
        })
    
    # Database conflict validation
    if 'no_database_conflicts' in criteria:
        db_conflicts = sum(1 for result in all_conversation_results 
                          if 'database_conflict' in result.get('errors', []))
        passed = db_conflicts == 0
        validation_results["validations"].append({
            "criteria": "no_database_conflicts",
            "expected": 0,
            "actual": db_conflicts,
            "passed": passed
        })
    
    # Context separation validation (for mixed persona scenarios)
    if 'no_conversation_mixing' in criteria:
        conversation_mixing = sum(1 for result in all_conversation_results 
                                if 'context_mixing' in result.get('errors', []))
        passed = conversation_mixing == 0
        validation_results["validations"].append({
            "criteria": "no_conversation_mixing",
            "expected": 0,
            "actual": conversation_mixing,
            "passed": passed
        })
    
    # Concurrency analysis
    start_times = [result.get('start_time', 0) for result in all_conversation_results]
    end_times = [result.get('end_time', 0) for result in all_conversation_results]
    
    validation_results["concurrency_analysis"] = {
        "total_users": total_users,
        "successful_users": successful_conversations,
        "failed_users": total_users - successful_conversations,
        "completion_rate": completion_rate,
        "avg_conversation_duration": sum(result.get('duration', 0) for result in all_conversation_results) / total_users if total_users > 0 else 0,
        "max_concurrent_active": timing_data.get('max_concurrent_active', 0),
        "overlap_period": max(end_times) - min(start_times) if start_times and end_times else 0
    }
    
    # Performance analysis
    response_times = []
    for result in all_conversation_results:
        if 'response_times' in result:
            response_times.extend(result['response_times'])
    
    validation_results["performance_analysis"] = {
        "total_messages": sum(result.get('message_count', 0) for result in all_conversation_results),
        "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
        "max_response_time": max(response_times) if response_times else 0,
        "min_response_time": min(response_times) if response_times else 0,
        "response_time_std": 0,  # Simplified - would calculate standard deviation
        "throughput_per_second": len(response_times) / (max(end_times) - min(start_times)) if start_times and end_times and max(end_times) > min(start_times) else 0
    }
    
    # Resource analysis
    validation_results["resource_analysis"] = {
        "peak_memory_usage": resource_metrics.get('memory_usage', {}).get('max', 0),
        "avg_cpu_usage": resource_metrics.get('cpu_usage', {}).get('avg', 0),
        "peak_connections": resource_metrics.get('active_connections', {}).get('max', 0),
        "resource_stability": resource_metrics.get('stability_score', 1.0),
        "memory_leak_detected": resource_metrics.get('memory_leak_detected', False)
    }
    
    # User experience analysis
    decision_accuracy = []
    context_retention_scores = []
    
    for result in all_conversation_results:
        if 'decision_accuracy' in result:
            decision_accuracy.append(result['decision_accuracy'])
        if 'context_retention_score' in result:
            context_retention_scores.append(result['context_retention_score'])
    
    validation_results["user_experience_analysis"] = {
        "avg_decision_accuracy": sum(decision_accuracy) / len(decision_accuracy) if decision_accuracy else 0,
        "avg_context_retention": sum(context_retention_scores) / len(context_retention_scores) if context_retention_scores else 0,
        "user_satisfaction_estimate": completion_rate * 0.7 + (sum(decision_accuracy) / len(decision_accuracy) if decision_accuracy else 0) * 0.3,
        "consistency_across_users": 1.0 - (max(response_times) - min(response_times)) / max(response_times) if response_times else 1.0
    }
    
    # Calculate overall success
    passed_validations = sum(1 for v in validation_results["validations"] if v["passed"])
    total_validations = len(validation_results["validations"])
    validation_rate = passed_validations / total_validations if total_validations > 0 else 0
    
    # Consider performance and resource metrics
    performance_ok = validation_results["performance_analysis"]["avg_response_time"] < 10.0  # 10 second threshold
    resource_ok = not validation_results["resource_analysis"]["memory_leak_detected"]
    
    validation_results["overall_success"] = (
        validation_rate >= 0.8 and 
        completion_rate >= 0.6 and 
        performance_ok and 
        resource_ok
    )
    
    return validation_results


if __name__ == "__main__":
    # Test the scenarios
    scenarios = phase3_concurrent_testing
    summary = scenarios.get_scenario_summary()
    
    print(">> Phase 3: Concurrent Testing Scenarios Summary")
    print("=" * 55)
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"Concurrency Types Covered: {summary['concurrency_types_covered']}")
    print(f"Load Patterns Covered: {summary['load_patterns_covered']}")
    print(f"Total Simulated Users: {summary['total_simulated_users']}")
    print(f"Max Concurrent Users: {summary['max_concurrent_users']}")
    print(f"Average Concurrent Users: {summary['avg_concurrent_users']:.1f}")
    print(f"Total Test Duration: {summary['total_test_duration']} seconds")
    print(f"Average Test Duration: {summary['avg_test_duration']:.0f} seconds")
    
    print("\nDifficulty Distribution:")
    for difficulty, count in summary['difficulty_distribution'].items():
        print(f"  {difficulty.capitalize()}: {count}")
    
    print(f"\nScenarios with Resource Monitoring: {summary['scenarios_with_monitoring']}")
    
    print("\nAll Scenarios:")
    for scenario in scenarios.get_all_scenarios():
        print(f"  {scenario.id}: {scenario.name}")
        print(f"    Users: {len(scenario.concurrent_users)}, Max Concurrent: {scenario.max_concurrent_users}")
        print(f"    Duration: {scenario.test_duration_seconds}s, Difficulty: {scenario.difficulty_level}")
        print(f"    Type: {scenario.concurrency_type.value}, Pattern: {scenario.load_pattern.value}")
        if scenario.expected_challenges:
            print(f"    Expected Challenges: {', '.join(scenario.expected_challenges)}")
        print()
    
    print(">> Concurrent Testing Framework Ready!")
    print("   Resource monitoring, timing analysis, and validation included")
    print("   Supports 5-10 concurrent users across various scenarios")