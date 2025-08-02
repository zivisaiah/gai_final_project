"""
Phase 3: Comprehensive Stress Testing Scenarios
Testing system behavior under various stress conditions and edge cases
"""

import time
import random
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum


class StressType(Enum):
    """Types of stress testing scenarios"""
    LONG_CONVERSATIONS = "long_conversations"
    RAPID_FIRE_MESSAGES = "rapid_fire_messages"
    CONTEXT_OVERFLOW = "context_overflow"
    INVALID_INPUT = "invalid_input"
    MEMORY_PRESSURE = "memory_pressure"
    API_TIMEOUT_SIMULATION = "api_timeout_simulation"
    MALFORMED_DATA = "malformed_data"
    BOUNDARY_CONDITIONS = "boundary_conditions"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class ErrorType(Enum):
    """Types of errors to simulate"""
    API_TIMEOUT = "api_timeout"
    INVALID_JSON = "invalid_json"
    MEMORY_OVERFLOW = "memory_overflow"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    MALFORMED_INPUT = "malformed_input"
    UNICODE_ERROR = "unicode_error"
    AUTHENTICATION_ERROR = "auth_error"


@dataclass
class StressCondition:
    """Represents a specific stress condition to apply"""
    stress_type: StressType
    severity: str  # low, medium, high, extreme
    parameters: Dict[str, Any]
    expected_behavior: str
    recovery_expected: bool = True


@dataclass
class StressTestScenario:
    """A complete stress testing scenario"""
    id: str
    name: str
    description: str
    stress_conditions: List[StressCondition]
    target_personas: List[str]
    success_criteria: Dict[str, Any]
    difficulty_level: str
    expected_decisions: List[str]
    max_duration_seconds: int = 300  # 5 minutes max
    expected_errors: List[ErrorType] = None


class Phase3StressTestingScenarios:
    """Phase 3 Comprehensive Stress Testing Scenarios"""
    
    def __init__(self):
        self.scenarios = self._create_scenarios()
    
    def _create_scenarios(self) -> List[StressTestScenario]:
        """Create comprehensive stress testing scenarios"""
        
        scenarios = []
        
        # Scenario 1: Long Conversation Endurance Test
        scenarios.append(StressTestScenario(
            id="stress_long_conversation",
            name="Long Conversation Endurance Test",
            description="Test system behavior with extended conversations (20+ messages)",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.LONG_CONVERSATIONS,
                    severity="high",
                    parameters={
                        "min_messages": 20,
                        "max_messages": 30,
                        "topics_to_cover": ["experience", "salary", "benefits", "schedule", "technical"]
                    },
                    expected_behavior="System maintains context and performance throughout long conversation",
                    recovery_expected=True
                )
            ],
            target_personas=["eager_junior", "experienced_senior"],
            success_criteria={
                "maintains_context": True,
                "no_memory_leaks": True,
                "consistent_performance": True,
                "successful_completion": True,
                "max_response_time_degradation": 2.0  # Max 2x slower than baseline
            },
            difficulty_level="high",
            expected_decisions=["CONTINUE", "INFO", "SCHEDULE"],
            max_duration_seconds=600  # 10 minutes for long conversations
        ))
        
        # Scenario 2: Rapid Fire Message Stress
        scenarios.append(StressTestScenario(
            id="stress_rapid_fire",
            name="Rapid Fire Message Handling",
            description="Test system with rapid succession of messages",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.RAPID_FIRE_MESSAGES,
                    severity="high",
                    parameters={
                        "message_interval_seconds": 0.5,
                        "total_messages": 15,
                        "message_variety": True
                    },
                    expected_behavior="System handles rapid messages without errors or delays",
                    recovery_expected=True
                )
            ],
            target_personas=["difficult_candidate", "eager_junior"],
            success_criteria={
                "no_dropped_messages": True,
                "maintains_order": True,
                "stable_performance": True,
                "max_queue_buildup": 5  # Max 5 messages in processing queue
            },
            difficulty_level="high",
            expected_decisions=["CONTINUE", "INFO"],
            max_duration_seconds=120
        ))
        
        # Scenario 3: Context Memory Overflow Test
        scenarios.append(StressTestScenario(
            id="stress_context_overflow",
            name="Context Memory Overflow Test",
            description="Test system behavior when conversation context exceeds memory limits",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.CONTEXT_OVERFLOW,
                    severity="extreme",
                    parameters={
                        "very_long_messages": True,
                        "complex_technical_content": True,
                        "repeated_information": True,
                        "max_context_tokens": 4000  # Approach token limits
                    },
                    expected_behavior="System gracefully handles context overflow without losing critical information",
                    recovery_expected=True
                )
            ],
            target_personas=["experienced_senior", "career_changer"],
            success_criteria={
                "no_context_loss": True,
                "graceful_degradation": True,
                "maintains_key_info": True,
                "no_crashes": True
            },
            difficulty_level="extreme",
            expected_decisions=["CONTINUE", "INFO", "SCHEDULE"],
            max_duration_seconds=300
        ))
        
        # Scenario 4: Invalid Input Handling
        scenarios.append(StressTestScenario(
            id="stress_invalid_input",
            name="Invalid Input Stress Test",
            description="Test system resilience with various invalid inputs",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.INVALID_INPUT,
                    severity="high",
                    parameters={
                        "empty_messages": True,
                        "very_long_strings": True,
                        "special_characters": True,
                        "unicode_edge_cases": True,
                        "sql_injection_attempts": True,
                        "malformed_json": True
                    },
                    expected_behavior="System sanitizes input and responds appropriately to invalid data",
                    recovery_expected=True
                )
            ],
            target_personas=["difficult_candidate"],
            success_criteria={
                "no_system_crashes": True,
                "proper_error_handling": True,
                "security_maintained": True,
                "graceful_responses": True
            },
            difficulty_level="high",
            expected_decisions=["CONTINUE", "END"],
            expected_errors=[ErrorType.MALFORMED_INPUT, ErrorType.UNICODE_ERROR],
            max_duration_seconds=180
        ))
        
        # Scenario 5: Memory Pressure Test
        scenarios.append(StressTestScenario(
            id="stress_memory_pressure",
            name="Memory Pressure Endurance Test",
            description="Test system behavior under simulated memory pressure",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.MEMORY_PRESSURE,
                    severity="high",
                    parameters={
                        "large_conversation_history": True,
                        "multiple_concurrent_operations": True,
                        "retain_all_context": True,
                        "complex_decision_trees": True
                    },
                    expected_behavior="System manages memory efficiently without degradation",
                    recovery_expected=True
                )
            ],
            target_personas=["experienced_senior", "career_changer", "eager_junior"],
            success_criteria={
                "no_memory_leaks": True,
                "stable_performance": True,
                "maintains_functionality": True,
                "graceful_cleanup": True
            },
            difficulty_level="high",
            expected_decisions=["CONTINUE", "INFO", "SCHEDULE", "END"],
            max_duration_seconds=400
        ))
        
        # Scenario 6: API Timeout Simulation
        scenarios.append(StressTestScenario(
            id="stress_api_timeout",
            name="API Timeout Stress Test",
            description="Test system resilience with simulated API timeouts and failures",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.API_TIMEOUT_SIMULATION,
                    severity="medium",
                    parameters={
                        "timeout_probability": 0.3,  # 30% chance of timeout
                        "retry_logic": True,
                        "fallback_responses": True,
                        "timeout_duration": 10  # seconds
                    },
                    expected_behavior="System handles API failures gracefully with appropriate fallbacks",
                    recovery_expected=True
                )
            ],
            target_personas=["eager_junior", "experienced_senior"],
            success_criteria={
                "fallback_activation": True,
                "user_notification": True,
                "eventual_recovery": True,
                "no_data_loss": True
            },
            difficulty_level="medium",
            expected_decisions=["CONTINUE", "INFO"],
            expected_errors=[ErrorType.API_TIMEOUT, ErrorType.NETWORK_ERROR],
            max_duration_seconds=240
        ))
        
        # Scenario 7: Boundary Condition Testing
        scenarios.append(StressTestScenario(
            id="stress_boundary_conditions",
            name="Boundary Condition Stress Test",
            description="Test system behavior at various operational boundaries",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.BOUNDARY_CONDITIONS,
                    severity="high",
                    parameters={
                        "max_message_length": 10000,  # Very long messages
                        "min_message_length": 1,      # Single character messages
                        "edge_case_inputs": True,
                        "limit_testing": True,
                        "zero_values": True,
                        "negative_values": True
                    },
                    expected_behavior="System handles boundary conditions without errors",
                    recovery_expected=True
                )
            ],
            target_personas=["difficult_candidate", "career_changer"],
            success_criteria={
                "handles_edge_cases": True,
                "validates_inputs": True,
                "no_buffer_overflows": True,
                "stable_operation": True
            },
            difficulty_level="high",
            expected_decisions=["CONTINUE", "END"],
            expected_errors=[ErrorType.MALFORMED_INPUT],
            max_duration_seconds=200
        ))
        
        # Scenario 8: Resource Exhaustion Test
        scenarios.append(StressTestScenario(
            id="stress_resource_exhaustion",
            name="Resource Exhaustion Stress Test",
            description="Test system behavior when approaching resource limits",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.RESOURCE_EXHAUSTION,
                    severity="extreme",
                    parameters={
                        "high_cpu_simulation": True,
                        "memory_intensive_operations": True,
                        "disk_space_pressure": False,  # Don't actually fill disk
                        "network_bandwidth_limits": True,
                        "concurrent_operations": 10
                    },
                    expected_behavior="System degrades gracefully under resource pressure",
                    recovery_expected=True
                )
            ],
            target_personas=["experienced_senior"],
            success_criteria={
                "graceful_degradation": True,
                "maintains_core_functionality": True,
                "proper_error_reporting": True,
                "recovery_capability": True
            },
            difficulty_level="extreme",
            expected_decisions=["CONTINUE", "INFO", "END"],
            expected_errors=[ErrorType.MEMORY_OVERFLOW, ErrorType.NETWORK_ERROR],
            max_duration_seconds=300
        ))
        
        # Scenario 9: Unicode and Encoding Stress Test
        scenarios.append(StressTestScenario(
            id="stress_unicode_encoding",
            name="Unicode and Encoding Stress Test",
            description="Test system with various Unicode and encoding challenges",
            stress_conditions=[
                StressCondition(
                    stress_type=StressType.MALFORMED_DATA,
                    severity="medium",
                    parameters={
                        "emoji_heavy_text": True,
                        "mixed_encoding": True,
                        "special_unicode_chars": True,
                        "rtl_text": True,  # Right-to-left text
                        "combining_characters": True,
                        "zero_width_characters": True
                    },
                    expected_behavior="System handles all Unicode characters correctly without encoding errors",
                    recovery_expected=True
                )
            ],
            target_personas=["difficult_candidate", "eager_junior"],
            success_criteria={
                "no_encoding_errors": True,
                "preserves_text_integrity": True,
                "handles_all_unicode": True,
                "stable_display": True
            },
            difficulty_level="medium",
            expected_decisions=["CONTINUE", "INFO"],
            expected_errors=[ErrorType.UNICODE_ERROR],
            max_duration_seconds=150
        ))
        
        return scenarios
    
    def get_scenario_by_id(self, scenario_id: str) -> Optional[StressTestScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        return None
    
    def get_scenarios_by_stress_type(self, stress_type: StressType) -> List[StressTestScenario]:
        """Get scenarios by stress type"""
        matching_scenarios = []
        for scenario in self.scenarios:
            for condition in scenario.stress_conditions:
                if condition.stress_type == stress_type:
                    matching_scenarios.append(scenario)
                    break
        return matching_scenarios
    
    def get_scenarios_by_severity(self, severity: str) -> List[StressTestScenario]:
        """Get scenarios by severity level"""
        matching_scenarios = []
        for scenario in self.scenarios:
            for condition in scenario.stress_conditions:
                if condition.severity == severity:
                    matching_scenarios.append(scenario)
                    break
        return matching_scenarios
    
    def get_scenarios_for_persona(self, persona_id: str) -> List[StressTestScenario]:
        """Get scenarios that target a specific persona"""
        return [s for s in self.scenarios if persona_id in s.target_personas]
    
    def get_all_scenarios(self) -> List[StressTestScenario]:
        """Get all stress testing scenarios"""
        return self.scenarios
    
    def get_scenario_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all scenarios"""
        total_scenarios = len(self.scenarios)
        difficulty_counts = {}
        stress_type_coverage = set()
        severity_distribution = {}
        
        for scenario in self.scenarios:
            # Count by difficulty
            if scenario.difficulty_level not in difficulty_counts:
                difficulty_counts[scenario.difficulty_level] = 0
            difficulty_counts[scenario.difficulty_level] += 1
            
            # Track stress type coverage
            for condition in scenario.stress_conditions:
                stress_type_coverage.add(condition.stress_type)
                
                # Track severity distribution
                if condition.severity not in severity_distribution:
                    severity_distribution[condition.severity] = 0
                severity_distribution[condition.severity] += 1
        
        expected_errors = []
        for scenario in self.scenarios:
            if scenario.expected_errors:
                expected_errors.extend(scenario.expected_errors)
        
        return {
            "total_scenarios": total_scenarios,
            "difficulty_distribution": difficulty_counts,
            "stress_types_covered": len(stress_type_coverage),
            "severity_distribution": severity_distribution,
            "expected_error_types": len(set(expected_errors)),
            "avg_max_duration": sum(s.max_duration_seconds for s in self.scenarios) / total_scenarios,
            "scenarios_by_difficulty": difficulty_counts,
            "scenarios_with_expected_errors": len([s for s in self.scenarios if s.expected_errors])
        }


# Global instance for easy import
phase3_stress_testing = Phase3StressTestingScenarios()


class StressTestMessageGenerator:
    """Generates various types of stress test messages"""
    
    @staticmethod
    def generate_long_message(topic: str = "experience", length: int = 1000) -> str:
        """Generate a very long message for stress testing"""
        base_messages = {
            "experience": "I have extensive experience in Python development including ",
            "technical": "Regarding the technical aspects of this position, I'm curious about ",
            "salary": "When it comes to compensation and benefits, I would like to know about ",
            "schedule": "Concerning the scheduling of interviews and the timeline for this role "
        }
        
        base = base_messages.get(topic, "I wanted to discuss ")
        
        # Add repetitive content to reach desired length
        filler_phrases = [
            "working with various frameworks and libraries, ",
            "developing scalable applications and systems, ",
            "collaborating with cross-functional teams, ",
            "implementing best practices and design patterns, ",
            "optimizing performance and maintaining code quality, ",
            "learning new technologies and staying current with industry trends, "
        ]
        
        message = base
        while len(message) < length:
            message += random.choice(filler_phrases)
        
        return message[:length]
    
    @staticmethod
    def generate_invalid_input() -> str:
        """Generate various types of invalid input for testing"""
        invalid_inputs = [
            "",  # Empty string
            " ",  # Whitespace only
            "\x00\x01\x02",  # Control characters
            "A" * 20000,  # Extremely long string
            "'; DROP TABLE users; --",  # SQL injection attempt
            '{"invalid": json}',  # Malformed JSON
            "🎉" * 1000,  # Many emojis
            "\u200B" * 100,  # Zero-width spaces
            "Hello\nWorld\r\nTest\t\tTab",  # Various whitespace
            "مرحبا بالعالم",  # Arabic text
            "你好世界",  # Chinese text
            "🏳️‍🌈🏳️‍⚧️👨‍👩‍👧‍👦",  # Complex emoji sequences
        ]
        
        return random.choice(invalid_inputs)
    
    @staticmethod
    def generate_unicode_stress_message() -> str:
        """Generate messages with various Unicode edge cases"""
        unicode_messages = [
            "Hello! 👋 I'm interested in this Python 🐍 position! Can we discuss the salary 💰?",
            "Résumé • Curriculum Vitæ • naïve • café • jalapeño • piñata",
            "Testing combining characters: a\u0300e\u0301i\u0302o\u0303u\u0308",
            "Right-to-left text: שלום עולם مرحبا بالعالم",
            "Mathematical symbols: ∑∏∫∮∂∇∆∞±×÷√∝∈∉⊂⊃∩∪",
            "Emoji with modifiers: 👨‍💻👩‍💻🏳️‍🌈🏳️‍⚧️👨‍👩‍👧‍👦",
            "Zero-width characters: Hell\u200Bo Wor\u200Bld",
            "Unusual spaces: Hello\u00A0World\u2000Test\u3000Space",
        ]
        
        return random.choice(unicode_messages)
    
    @staticmethod
    def generate_rapid_fire_messages(count: int = 10) -> List[str]:
        """Generate a series of messages for rapid-fire testing"""
        messages = [
            "Hi there!",
            "What's the salary?",
            "Are you remote?",
            "Tell me about benefits",
            "Can we schedule?",
            "What's the tech stack?",
            "Team size?",
            "Growth opportunities?",
            "Work-life balance?",
            "When can I start?",
            "Any questions for me?",
            "What's next?",
            "I'm very interested!",
            "Let's move forward",
            "Thanks for your time"
        ]
        
        return messages[:count]


def validate_stress_test_scenario(scenario: StressTestScenario, 
                                 conversation_log: List[Dict],
                                 decisions_made: List[str],
                                 errors_encountered: List[str],
                                 performance_metrics: Dict) -> Dict[str, Any]:
    """
    Validate if a stress test scenario was handled successfully
    
    Args:
        scenario: The stress test scenario that was run
        conversation_log: Complete conversation log
        decisions_made: List of agent decisions made
        errors_encountered: List of errors that occurred
        performance_metrics: Performance metrics collected
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "scenario_id": scenario.id,
        "overall_success": False,
        "validations": [],
        "stress_handling": [],
        "error_analysis": {},
        "performance_analysis": {},
        "recovery_analysis": {}
    }
    
    # Check basic success criteria
    criteria = scenario.success_criteria
    
    # Performance validation
    if 'max_response_time_degradation' in criteria:
        baseline_time = performance_metrics.get('baseline_response_time', 1.0)
        max_time = performance_metrics.get('max_response_time', 0.0)
        degradation = max_time / baseline_time if baseline_time > 0 else 1.0
        
        passed = degradation <= criteria['max_response_time_degradation']
        validation_results["validations"].append({
            "criteria": "max_response_time_degradation",
            "expected": criteria['max_response_time_degradation'],
            "actual": degradation,
            "passed": passed
        })
    
    # Memory and stability validation
    if 'no_memory_leaks' in criteria:
        memory_stable = performance_metrics.get('memory_stable', True)
        validation_results["validations"].append({
            "criteria": "no_memory_leaks",
            "expected": True,
            "actual": memory_stable,
            "passed": memory_stable
        })
    
    # Error handling validation
    if 'no_system_crashes' in criteria:
        no_crashes = 'system_crash' not in errors_encountered
        validation_results["validations"].append({
            "criteria": "no_system_crashes",
            "expected": True,
            "actual": no_crashes,
            "passed": no_crashes
        })
    
    # Context preservation validation
    if 'maintains_context' in criteria:
        context_maintained = performance_metrics.get('context_maintained', True)
        validation_results["validations"].append({
            "criteria": "maintains_context",
            "expected": True,
            "actual": context_maintained,
            "passed": context_maintained
        })
    
    # Analyze stress condition handling
    for i, condition in enumerate(scenario.stress_conditions):
        stress_validation = {
            "condition_index": i,
            "stress_type": condition.stress_type.value,
            "severity": condition.severity,
            "handled_appropriately": True,  # Default assumption
            "recovery_successful": condition.recovery_expected,
            "performance_impact": "acceptable"
        }
        
        # Analyze specific stress types
        if condition.stress_type == StressType.LONG_CONVERSATIONS:
            message_count = len([msg for msg in conversation_log if msg.get('type') == 'user'])
            min_expected = condition.parameters.get('min_messages', 10)
            stress_validation["handled_appropriately"] = message_count >= min_expected
            
        elif condition.stress_type == StressType.INVALID_INPUT:
            # Check if system handled invalid inputs gracefully
            invalid_input_errors = [e for e in errors_encountered if 'invalid' in e.lower()]
            stress_validation["handled_appropriately"] = len(invalid_input_errors) == 0 or all(
                'handled_gracefully' in e for e in invalid_input_errors
            )
        
        validation_results["stress_handling"].append(stress_validation)
    
    # Error analysis
    expected_errors = scenario.expected_errors or []
    validation_results["error_analysis"] = {
        "expected_errors": [e.value for e in expected_errors],
        "actual_errors": errors_encountered,
        "unexpected_errors": [e for e in errors_encountered 
                             if not any(exp.value in e for exp in expected_errors)],
        "missing_expected_errors": [e.value for e in expected_errors 
                                   if not any(e.value in actual for actual in errors_encountered)]
    }
    
    # Performance analysis
    validation_results["performance_analysis"] = {
        "avg_response_time": performance_metrics.get('avg_response_time', 0.0),
        "max_response_time": performance_metrics.get('max_response_time', 0.0),
        "min_response_time": performance_metrics.get('min_response_time', 0.0),
        "memory_usage_stable": performance_metrics.get('memory_stable', True),
        "error_rate": len(errors_encountered) / max(1, len(conversation_log))
    }
    
    # Recovery analysis
    recovery_events = performance_metrics.get('recovery_events', [])
    validation_results["recovery_analysis"] = {
        "recovery_events": len(recovery_events),
        "successful_recoveries": len([e for e in recovery_events if e.get('successful', False)]),
        "average_recovery_time": sum(e.get('recovery_time', 0) for e in recovery_events) / max(1, len(recovery_events))
    }
    
    # Calculate overall success
    passed_validations = sum(1 for v in validation_results["validations"] if v["passed"])
    total_validations = len(validation_results["validations"])
    successful_stress_handling = sum(1 for s in validation_results["stress_handling"] 
                                   if s["handled_appropriately"])
    total_stress_conditions = len(validation_results["stress_handling"])
    
    validation_rate = passed_validations / max(1, total_validations)
    stress_handling_rate = successful_stress_handling / max(1, total_stress_conditions)
    
    # Overall success if both validation and stress handling rates are acceptable
    validation_results["overall_success"] = (validation_rate >= 0.8 and stress_handling_rate >= 0.7)
    
    return validation_results


if __name__ == "__main__":
    # Test the scenarios
    scenarios = phase3_stress_testing
    summary = scenarios.get_scenario_summary()
    
    print(">> Phase 3: Stress Testing Scenarios Summary")
    print("=" * 50)
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"Stress Types Covered: {summary['stress_types_covered']}")
    print(f"Expected Error Types: {summary['expected_error_types']}")
    print(f"Average Max Duration: {summary['avg_max_duration']:.0f} seconds")
    
    print("\nDifficulty Distribution:")
    for difficulty, count in summary['scenarios_by_difficulty'].items():
        print(f"  {difficulty.capitalize()}: {count}")
    
    print("\nSeverity Distribution:")
    for severity, count in summary['severity_distribution'].items():
        print(f"  {severity.capitalize()}: {count}")
    
    print(f"\nScenarios with Expected Errors: {summary['scenarios_with_expected_errors']}")
    
    print("\nAll Scenarios:")
    for scenario in scenarios.get_all_scenarios():
        print(f"  {scenario.id}: {scenario.name} ({scenario.difficulty_level})")
        print(f"    Stress Conditions: {len(scenario.stress_conditions)}")
        print(f"    Max Duration: {scenario.max_duration_seconds}s")
        if scenario.expected_errors:
            error_names = [e.value for e in scenario.expected_errors]
            print(f"    Expected Errors: {', '.join(error_names)}")
    
    # Test message generators
    print("\n>> Testing Message Generators:")
    gen = StressTestMessageGenerator()
    print(f"Long message sample: {gen.generate_long_message('experience', 100)[:80]}...")
    print(f"Invalid input sample: {repr(gen.generate_invalid_input())}")
    print(f"Unicode stress sample: {gen.generate_unicode_stress_message()}")
    print(f"Rapid fire messages: {len(gen.generate_rapid_fire_messages(5))} messages generated")