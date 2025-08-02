"""
Phase 2: Comprehensive Basic Test Scenarios
10 test cases covering all major functionality areas
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class TestScenario:
    """Test scenario configuration"""
    id: str
    name: str
    description: str
    target_personas: List[str]
    expected_decisions: List[str]
    success_criteria: Dict
    validation_points: List[str]

class Phase2TestScenarios:
    """Comprehensive test scenarios for Phase 2 basic testing"""
    
    def __init__(self):
        self.scenarios = self._create_test_scenarios()
    
    def _create_test_scenarios(self) -> Dict[str, TestScenario]:
        """Create all Phase 2 test scenarios"""
        scenarios = {}
        
        # === HAPPY PATH TESTING ===
        
        scenarios['happy_path_junior'] = TestScenario(
            id='happy_path_junior',
            name='Happy Path - Junior Developer',
            description='Complete flow with enthusiastic junior developer',
            target_personas=['eager_junior'],
            expected_decisions=['CONTINUE', 'SCHEDULE'],
            success_criteria={
                'min_messages': 4,
                'max_messages': 8,
                'must_schedule': True,
                'expected_completion': 'completed'
            },
            validation_points=[
                'Agent asks about experience',
                'User provides detailed responses',
                'Agent offers scheduling',
                'User accepts interview'
            ]
        )
        
        scenarios['happy_path_senior'] = TestScenario(
            id='happy_path_senior',
            name='Happy Path - Senior Developer',
            description='Efficient flow with experienced senior developer',
            target_personas=['experienced_senior'],
            expected_decisions=['CONTINUE', 'SCHEDULE'],
            success_criteria={
                'min_messages': 3,
                'max_messages': 6,
                'must_schedule': True,
                'expected_completion': 'completed'
            },
            validation_points=[
                'Agent recognizes senior experience',
                'User provides concise technical details',
                'Quick progression to scheduling',
                'Professional conversation tone'
            ]
        )
        
        scenarios['happy_path_career_change'] = TestScenario(
            id='happy_path_career_change',
            name='Happy Path - Career Changer',
            description='Supportive flow with career transition candidate',
            target_personas=['career_changer'],
            expected_decisions=['CONTINUE', 'INFO', 'SCHEDULE'],
            success_criteria={
                'min_messages': 5,
                'max_messages': 10,
                'must_schedule': True,
                'expected_completion': 'completed'
            },
            validation_points=[
                'Agent asks supportive questions',
                'User expresses uncertainty and asks questions',
                'Agent provides helpful information',
                'Reassuring path to scheduling'
            ]
        )
        
        # === CORE AGENT DECISION TESTING ===
        
        scenarios['continue_decision_accuracy'] = TestScenario(
            id='continue_decision_accuracy',
            name='CONTINUE Decision Accuracy',
            description='Test appropriate use of CONTINUE decisions',
            target_personas=['eager_junior', 'career_changer'],
            expected_decisions=['CONTINUE', 'CONTINUE', 'SCHEDULE'],
            success_criteria={
                'continue_count': {'min': 2, 'max': 4},
                'information_gathered': True,
                'no_premature_scheduling': True
            },
            validation_points=[
                'Agent continues when information insufficient',
                'Agent asks varied questions',
                'Agent gathers comprehensive background',
                'Agent schedules only when ready'
            ]
        )
        
        scenarios['schedule_decision_timing'] = TestScenario(
            id='schedule_decision_timing',
            name='SCHEDULE Decision Timing',
            description='Test optimal timing for scheduling decisions',
            target_personas=['eager_junior', 'experienced_senior'],
            expected_decisions=['CONTINUE', 'SCHEDULE'],
            success_criteria={
                'schedule_after_info': True,
                'appropriate_timing': True,
                'user_acceptance_likely': True
            },
            validation_points=[
                'Agent schedules after gathering key info',
                'Agent schedules with engaged candidates',
                'Agent timing feels natural',
                'High probability of user acceptance'
            ]
        )
        
        scenarios['info_decision_handling'] = TestScenario(
            id='info_decision_handling',
            name='INFO Decision Handling',
            description='Test appropriate INFO responses to user questions',
            target_personas=['career_changer', 'eager_junior'],
            expected_decisions=['INFO', 'CONTINUE'],
            success_criteria={
                'info_responses_relevant': True,
                'continues_after_info': True,
                'addresses_user_questions': True
            },
            validation_points=[
                'Agent provides INFO when user asks questions',
                'INFO responses are relevant and helpful',
                'Agent continues conversation after INFO',
                'User questions are addressed appropriately'
            ]
        )
        
        scenarios['end_decision_appropriate'] = TestScenario(
            id='end_decision_appropriate',
            name='END Decision Appropriateness',
            description='Test appropriate use of END decisions',
            target_personas=['difficult_candidate', 'passive_candidate'],
            expected_decisions=['CONTINUE', 'END'],
            success_criteria={
                'end_when_appropriate': True,
                'not_premature_end': True,
                'graceful_conclusion': True
            },
            validation_points=[
                'Agent ends when conversation stalls',
                'Agent tries to engage before ending',
                'Agent ends gracefully and professionally',
                'Appropriate conversation length before END'
            ]
        )
        
        # === INDIVIDUAL AGENT TESTING ===
        
        scenarios['scheduling_workflow'] = TestScenario(
            id='scheduling_workflow',
            name='Scheduling Workflow',
            description='Test complete scheduling workflow functionality',
            target_personas=['eager_junior', 'experienced_senior'],
            expected_decisions=['CONTINUE', 'SCHEDULE'],
            success_criteria={
                'scheduling_offered': True,
                'slots_provided': True,
                'booking_attempted': True
            },
            validation_points=[
                'Agent identifies scheduling opportunity',
                'Agent offers specific time slots',
                'User can select from options',
                'Booking process initiates'
            ]
        )
        
        scenarios['information_provision'] = TestScenario(
            id='information_provision',
            name='Information Provision',
            description='Test quality and relevance of INFO responses',
            target_personas=['career_changer', 'eager_junior'],
            expected_decisions=['INFO', 'INFO', 'CONTINUE'],
            success_criteria={
                'multiple_info_responses': True,
                'info_quality_high': True,
                'varied_topics_covered': True
            },
            validation_points=[
                'Agent handles multiple INFO requests',
                'Responses are specific and helpful',
                'Different topics addressed appropriately',
                'Conversation continues naturally after INFO'
            ]
        )
        
        # === CHALLENGING SCENARIOS ===
        
        scenarios['passive_engagement'] = TestScenario(
            id='passive_engagement',
            name='Passive Candidate Engagement',
            description='Test engagement strategies with passive candidates',
            target_personas=['passive_candidate'],
            expected_decisions=['CONTINUE', 'CONTINUE', 'END'],
            success_criteria={
                'multiple_engagement_attempts': True,
                'appropriate_persistence': True,
                'graceful_handling': True
            },
            validation_points=[
                'Agent attempts to engage passive user',
                'Agent varies questioning strategies',
                'Agent recognizes low engagement',
                'Agent handles conclusion professionally'
            ]
        )
        
        return scenarios
    
    def get_scenario(self, scenario_id: str) -> TestScenario:
        """Get a specific test scenario"""
        return self.scenarios.get(scenario_id)
    
    def get_scenarios_by_category(self, category: str) -> List[TestScenario]:
        """Get scenarios by category (happy_path, decision_testing, etc.)"""
        category_scenarios = []
        for scenario in self.scenarios.values():
            if category in scenario.id:
                category_scenarios.append(scenario)
        return category_scenarios
    
    def get_all_scenarios(self) -> List[TestScenario]:
        """Get all test scenarios"""
        return list(self.scenarios.values())
    
    def get_scenarios_for_persona(self, persona_id: str) -> List[TestScenario]:
        """Get all scenarios that include a specific persona"""
        return [scenario for scenario in self.scenarios.values() 
                if persona_id in scenario.target_personas]

# Global instance
phase2_scenarios = Phase2TestScenarios()