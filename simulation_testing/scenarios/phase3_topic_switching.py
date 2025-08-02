"""
Phase 3: Topic Switching Edge Case Scenarios
Testing conversation flow when users jump between different topics mid-conversation
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TopicType(Enum):
    """Types of conversation topics"""
    EXPERIENCE = "experience"
    AVAILABILITY = "availability"
    SALARY = "salary"
    COMPANY_CULTURE = "company_culture"
    TECHNICAL_QUESTIONS = "technical_questions"
    JOB_REQUIREMENTS = "job_requirements"
    BENEFITS = "benefits"
    WORK_ENVIRONMENT = "work_environment"
    CAREER_GROWTH = "career_growth"
    TEAM_STRUCTURE = "team_structure"


@dataclass
class TopicSwitch:
    """Represents a topic switch in conversation"""
    from_topic: TopicType
    to_topic: TopicType
    trigger_message: str
    expected_agent_handling: str
    difficulty_level: str = "medium"  # easy, medium, hard, extreme


@dataclass
class TopicSwitchingScenario:
    """A complete topic switching test scenario"""
    id: str
    name: str
    description: str
    initial_topic: TopicType
    topic_switches: List[TopicSwitch]
    target_personas: List[str]
    success_criteria: Dict[str, any]
    difficulty_level: str
    expected_decisions: List[str]


class Phase3TopicSwitchingScenarios:
    """Phase 3 Topic Switching Edge Case Test Scenarios"""
    
    def __init__(self):
        self.scenarios = self._create_scenarios()
    
    def _create_scenarios(self) -> List[TopicSwitchingScenario]:
        """Create comprehensive topic switching scenarios"""
        
        scenarios = []
        
        # Scenario 1: Experience -> Salary (Common Switch)
        scenarios.append(TopicSwitchingScenario(
            id="topic_exp_to_salary",
            name="Experience to Salary Discussion",
            description="User starts discussing experience then suddenly asks about salary",
            initial_topic=TopicType.EXPERIENCE,
            topic_switches=[
                TopicSwitch(
                    from_topic=TopicType.EXPERIENCE,
                    to_topic=TopicType.SALARY,
                    trigger_message="That's great! By the way, what's the salary range for this position?",
                    expected_agent_handling="Agent should acknowledge the topic change and provide appropriate salary information or guide to next steps",
                    difficulty_level="medium"
                )
            ],
            target_personas=["eager_junior", "experienced_senior"],
            success_criteria={
                "handles_topic_switch": True,
                "maintains_context": True,
                "provides_appropriate_response": True,
                "max_messages": 6
            },
            difficulty_level="medium",
            expected_decisions=["CONTINUE", "INFO"]
        ))
        
        # Scenario 2: Multiple Rapid Topic Switches (Hard)
        scenarios.append(TopicSwitchingScenario(
            id="topic_rapid_multiple",
            name="Rapid Multiple Topic Switches",
            description="User rapidly switches between multiple topics in succession",
            initial_topic=TopicType.EXPERIENCE,
            topic_switches=[
                TopicSwitch(
                    from_topic=TopicType.EXPERIENCE,
                    to_topic=TopicType.WORK_ENVIRONMENT,
                    trigger_message="Actually, I'm more curious about the work environment. Is it remote?",
                    expected_agent_handling="Agent should handle the topic switch gracefully",
                    difficulty_level="medium"
                ),
                TopicSwitch(
                    from_topic=TopicType.WORK_ENVIRONMENT,
                    to_topic=TopicType.TECHNICAL_QUESTIONS,
                    trigger_message="Wait, before that - what programming languages do you use?",
                    expected_agent_handling="Agent should manage rapid topic changes while maintaining conversation flow",
                    difficulty_level="hard"
                ),
                TopicSwitch(
                    from_topic=TopicType.TECHNICAL_QUESTIONS,
                    to_topic=TopicType.AVAILABILITY,
                    trigger_message="OK cool. When would I start if hired?",
                    expected_agent_handling="Agent should handle scheduling-related inquiry appropriately",
                    difficulty_level="hard"
                )
            ],
            target_personas=["difficult_candidate", "eager_junior"],
            success_criteria={
                "handles_all_switches": True,
                "maintains_conversation_flow": True,
                "no_confusion": True,
                "max_messages": 10
            },
            difficulty_level="hard",
            expected_decisions=["CONTINUE", "INFO", "SCHEDULE"]
        ))
        
        # Scenario 3: Topic Switch Back to Original (Medium)
        scenarios.append(TopicSwitchingScenario(
            id="topic_circular_switch",
            name="Circular Topic Switching",
            description="User switches to new topic then returns to original topic",
            initial_topic=TopicType.EXPERIENCE,
            topic_switches=[
                TopicSwitch(
                    from_topic=TopicType.EXPERIENCE,
                    to_topic=TopicType.COMPANY_CULTURE,
                    trigger_message="Actually, what's the company culture like?",
                    expected_agent_handling="Agent should provide culture information",
                    difficulty_level="easy"
                ),
                TopicSwitch(
                    from_topic=TopicType.COMPANY_CULTURE,
                    to_topic=TopicType.EXPERIENCE,
                    trigger_message="That sounds good. Going back to my experience - I should mention I also worked with Django.",
                    expected_agent_handling="Agent should seamlessly return to experience discussion with new information",
                    difficulty_level="medium"
                )
            ],
            target_personas=["career_changer", "experienced_senior"],
            success_criteria={
                "handles_return_to_original": True,
                "integrates_new_information": True,
                "maintains_context": True,
                "max_messages": 8
            },
            difficulty_level="medium",
            expected_decisions=["CONTINUE", "INFO"]
        ))
        
        # Scenario 4: Irrelevant Topic Switch (Hard)
        scenarios.append(TopicSwitchingScenario(
            id="topic_irrelevant_switch",
            name="Irrelevant Topic Interruption",
            description="User suddenly brings up completely irrelevant topics",
            initial_topic=TopicType.EXPERIENCE,
            topic_switches=[
                TopicSwitch(
                    from_topic=TopicType.EXPERIENCE,
                    to_topic=TopicType.TECHNICAL_QUESTIONS,
                    trigger_message="Oh wait, do you guys have a coffee machine? I'm really into coffee.",
                    expected_agent_handling="Agent should politely redirect back to relevant conversation",
                    difficulty_level="hard"
                )
            ],
            target_personas=["difficult_candidate", "eager_junior"],
            success_criteria={
                "handles_irrelevant_topic": True,
                "redirects_appropriately": True,
                "maintains_professionalism": True,
                "max_messages": 6
            },
            difficulty_level="hard",
            expected_decisions=["CONTINUE"]
        ))
        
        # Scenario 5: Deep Technical Dive Mid-Experience (Medium)
        scenarios.append(TopicSwitchingScenario(
            id="topic_technical_deep_dive",
            name="Technical Deep Dive Interruption",
            description="User switches from general experience to very specific technical questions",
            initial_topic=TopicType.EXPERIENCE,
            topic_switches=[
                TopicSwitch(
                    from_topic=TopicType.EXPERIENCE,
                    to_topic=TopicType.TECHNICAL_QUESTIONS,
                    trigger_message="I see you need Python experience. Do you use async/await patterns? What about type hints and mypy? Are you using FastAPI or Django?",
                    expected_agent_handling="Agent should handle technical inquiry appropriately, possibly using INFO advisor",
                    difficulty_level="medium"
                )
            ],
            target_personas=["experienced_senior", "career_changer"],
            success_criteria={
                "handles_technical_questions": True,
                "uses_info_advisor": True,
                "provides_technical_details": True,
                "max_messages": 6
            },
            difficulty_level="medium",
            expected_decisions=["INFO", "CONTINUE"]
        ))
        
        # Scenario 6: Scheduling Interruption (Critical)
        scenarios.append(TopicSwitchingScenario(
            id="topic_scheduling_interrupt",
            name="Scheduling Topic Interruption",
            description="User suddenly asks about scheduling mid-conversation on another topic",
            initial_topic=TopicType.TECHNICAL_QUESTIONS,
            topic_switches=[
                TopicSwitch(
                    from_topic=TopicType.TECHNICAL_QUESTIONS,
                    to_topic=TopicType.AVAILABILITY,
                    trigger_message="Actually, can we schedule an interview? I'm available this week.",
                    expected_agent_handling="Agent should recognize scheduling intent and handle appropriately",
                    difficulty_level="easy"
                )
            ],
            target_personas=["eager_junior", "experienced_senior", "career_changer"],
            success_criteria={
                "recognizes_scheduling_intent": True,
                "switches_to_scheduling": True,
                "offers_time_slots": True,
                "max_messages": 5
            },
            difficulty_level="medium",
            expected_decisions=["SCHEDULE"]
        ))
            
        # Scenario 7: Context Loss Test (Extreme)
        scenarios.append(TopicSwitchingScenario(
            id="topic_context_stress",
            name="Context Memory Stress Test",
            description="Complex topic switching to test context retention limits",
            initial_topic=TopicType.EXPERIENCE,
            topic_switches=[
                TopicSwitch(
                    from_topic=TopicType.EXPERIENCE,
                    to_topic=TopicType.SALARY,
                    trigger_message="What's the salary?",
                    expected_agent_handling="Handle salary inquiry",
                    difficulty_level="easy"
                ),
                TopicSwitch(
                    from_topic=TopicType.SALARY,
                    to_topic=TopicType.BENEFITS,
                    trigger_message="What about benefits?",
                    expected_agent_handling="Provide benefits information",
                    difficulty_level="easy"
                ),
                TopicSwitch(
                    from_topic=TopicType.BENEFITS,
                    to_topic=TopicType.WORK_ENVIRONMENT,
                    trigger_message="Is it remote work?",
                    expected_agent_handling="Discuss work arrangements",
                    difficulty_level="easy"
                ),
                TopicSwitch(
                    from_topic=TopicType.WORK_ENVIRONMENT,
                    to_topic=TopicType.EXPERIENCE,
                    trigger_message="Going back to my experience - did I mention I have ML experience?",
                    expected_agent_handling="Should remember original experience discussion and integrate new info",
                    difficulty_level="extreme"
                )
            ],
            target_personas=["difficult_candidate"],
            success_criteria={
                "maintains_long_context": True,
                "remembers_original_discussion": True,
                "integrates_all_information": True,
                "max_messages": 12
            },
            difficulty_level="extreme",
            expected_decisions=["CONTINUE", "INFO", "SCHEDULE"]
        ))
        
        return scenarios
    
    def get_scenario_by_id(self, scenario_id: str) -> Optional[TopicSwitchingScenario]:
        """Get a specific scenario by ID"""
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        return None
    
    def get_scenarios_by_difficulty(self, difficulty: str) -> List[TopicSwitchingScenario]:
        """Get scenarios by difficulty level"""
        return [s for s in self.scenarios if s.difficulty_level == difficulty]
    
    def get_scenarios_for_persona(self, persona_id: str) -> List[TopicSwitchingScenario]:
        """Get scenarios that target a specific persona"""
        return [s for s in self.scenarios if persona_id in s.target_personas]
    
    def get_all_scenarios(self) -> List[TopicSwitchingScenario]:
        """Get all topic switching scenarios"""
        return self.scenarios
    
    def get_scenario_summary(self) -> Dict[str, any]:
        """Get summary statistics of all scenarios"""
        total_scenarios = len(self.scenarios)
        difficulty_counts = {}
        topic_coverage = set()
        
        for scenario in self.scenarios:
            # Count by difficulty
            if scenario.difficulty_level not in difficulty_counts:
                difficulty_counts[scenario.difficulty_level] = 0
            difficulty_counts[scenario.difficulty_level] += 1
            
            # Track topic coverage
            topic_coverage.add(scenario.initial_topic)
            for switch in scenario.topic_switches:
                topic_coverage.add(switch.from_topic)
                topic_coverage.add(switch.to_topic)
        
        return {
            "total_scenarios": total_scenarios,
            "difficulty_distribution": difficulty_counts,
            "topics_covered": len(topic_coverage),
            "average_switches_per_scenario": sum(len(s.topic_switches) for s in self.scenarios) / total_scenarios,
            "scenarios_by_difficulty": {
                "easy": len([s for s in self.scenarios if s.difficulty_level == "easy"]),
                "medium": len([s for s in self.scenarios if s.difficulty_level == "medium"]),
                "hard": len([s for s in self.scenarios if s.difficulty_level == "hard"]),
                "extreme": len([s for s in self.scenarios if s.difficulty_level == "extreme"])
            }
        }


# Global instance for easy import
phase3_topic_switching = Phase3TopicSwitchingScenarios()


def validate_topic_switching_scenario(scenario: TopicSwitchingScenario, 
                                     conversation_log: List[Dict],
                                     decisions_made: List[str]) -> Dict[str, any]:
    """
    Validate if a topic switching scenario was handled successfully
    
    Args:
        scenario: The topic switching scenario that was run
        conversation_log: Complete conversation log
        decisions_made: List of agent decisions made
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "scenario_id": scenario.id,
        "overall_success": False,
        "validations": [],
        "topic_switch_handling": [],
        "context_retention_score": 0.0,
        "agent_adaptability_score": 0.0
    }
    
    # Check basic success criteria
    criteria = scenario.success_criteria
    
    # Message count validation
    user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
    message_count = len(user_messages)
    
    if 'max_messages' in criteria:
        passed = message_count <= criteria['max_messages']
        validation_results["validations"].append({
            "criteria": "max_messages",
            "expected": criteria['max_messages'],
            "actual": message_count,
            "passed": passed
        })
    
    # Topic switch specific validations
    for i, topic_switch in enumerate(scenario.topic_switches):
        switch_validation = {
            "switch_index": i,
            "from_topic": topic_switch.from_topic.value,
            "to_topic": topic_switch.to_topic.value,
            "handled_appropriately": False,
            "maintained_context": False,
            "response_quality": "unknown"
        }
        
        # Look for the trigger message and subsequent agent response
        trigger_found = False
        agent_response_after_switch = None
        
        for j, msg in enumerate(conversation_log):
            if (msg.get('type') == 'user' and 
                topic_switch.trigger_message.lower() in msg.get('message', '').lower()):
                trigger_found = True
                
                # Find the next agent message
                for k in range(j + 1, len(conversation_log)):
                    if conversation_log[k].get('type') == 'agent':
                        agent_response_after_switch = conversation_log[k]
                        break
                break
        
        if trigger_found and agent_response_after_switch:
            # Analyze if agent handled the topic switch well
            agent_message = agent_response_after_switch.get('message', '').lower()
            
            # Check for appropriate handling based on topic type
            if topic_switch.to_topic == TopicType.SALARY:
                switch_validation["handled_appropriately"] = any(word in agent_message 
                    for word in ['salary', 'compensation', 'pay', 'range'])
            elif topic_switch.to_topic == TopicType.AVAILABILITY:
                switch_validation["handled_appropriately"] = any(word in agent_message 
                    for word in ['schedule', 'available', 'interview', 'time'])
            elif topic_switch.to_topic == TopicType.TECHNICAL_QUESTIONS:
                switch_validation["handled_appropriately"] = any(word in agent_message 
                    for word in ['technical', 'technology', 'programming', 'language'])
            else:
                # General topic switch handling
                switch_validation["handled_appropriately"] = len(agent_message) > 10
        
        validation_results["topic_switch_handling"].append(switch_validation)
    
    # Calculate overall scores
    handled_switches = sum(1 for ts in validation_results["topic_switch_handling"] 
                          if ts["handled_appropriately"])
    total_switches = len(scenario.topic_switches)
    
    if total_switches > 0:
        validation_results["agent_adaptability_score"] = handled_switches / total_switches
    
    # Context retention score (simplified)
    context_indicators = 0
    total_indicators = 0
    
    for msg in conversation_log:
        if msg.get('type') == 'agent':
            message_text = msg.get('message', '').lower()
            total_indicators += 1
            # Check if agent message shows awareness of conversation context
            if any(word in message_text for word in ['you mentioned', 'earlier', 'previously', 'going back']):
                context_indicators += 1
    
    if total_indicators > 0:
        validation_results["context_retention_score"] = context_indicators / total_indicators
    
    # Overall success calculation
    passed_validations = sum(1 for v in validation_results["validations"] if v["passed"])
    total_validations = len(validation_results["validations"])
    successful_switches = sum(1 for ts in validation_results["topic_switch_handling"] 
                             if ts["handled_appropriately"])
    
    success_rate = 0.0
    if total_validations > 0:
        success_rate = passed_validations / total_validations
    
    switch_success_rate = 0.0
    if total_switches > 0:
        switch_success_rate = successful_switches / total_switches
    
    # Overall success if both criteria and topic switches are mostly successful
    validation_results["overall_success"] = (success_rate >= 0.7 and switch_success_rate >= 0.6)
    
    return validation_results


if __name__ == "__main__":
    # Test the scenarios
    scenarios = phase3_topic_switching
    summary = scenarios.get_scenario_summary()
    
    print(">> Phase 3: Topic Switching Scenarios Summary")
    print("=" * 50)
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"Topics Covered: {summary['topics_covered']}")
    print(f"Average Switches per Scenario: {summary['average_switches_per_scenario']:.1f}")
    print("\nDifficulty Distribution:")
    for difficulty, count in summary['scenarios_by_difficulty'].items():
        print(f"  {difficulty.capitalize()}: {count}")
    
    print("\nAll Scenarios:")
    for scenario in scenarios.get_all_scenarios():
        print(f"  {scenario.id}: {scenario.name} ({scenario.difficulty_level})")
        print(f"    Switches: {len(scenario.topic_switches)}")
        print(f"    Personas: {', '.join(scenario.target_personas)}")