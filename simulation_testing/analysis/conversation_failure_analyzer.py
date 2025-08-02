"""
Phase 3A: Conversation Failure Analysis Tool
Analyzes conversation logs to identify patterns and root causes of failures
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from simulation_testing.config.test_config import config


@dataclass
class ConversationFailure:
    """Represents a conversation failure case"""
    conversation_id: str
    persona_id: str
    persona_type: str
    failure_reason: str
    failure_stage: str  # early, middle, late
    message_count: int
    duration: float
    last_agent_decision: str
    last_user_message: str
    last_agent_message: str
    decisions_sequence: List[str]
    failure_indicators: List[str]


@dataclass
class FailurePattern:
    """Represents a pattern of failures"""
    pattern_id: str
    pattern_name: str
    frequency: int
    affected_personas: List[str]
    common_failure_stage: str
    typical_message_count: float
    root_cause_hypothesis: str
    recommended_fixes: List[str]
    examples: List[str]


class ConversationFailureAnalyzer:
    """Analyzes conversation logs to identify failure patterns and root causes"""
    
    def __init__(self):
        self.results_dir = config.SIMULATION_ROOT / "results"
        self.analysis_results = {}
        self.failure_cases = []
        self.success_cases = []
        
    def load_recent_test_results(self, days_back: int = 7) -> List[Dict]:
        """Load recent test result files"""
        cutoff_time = datetime.now().timestamp() - (days_back * 24 * 3600)
        result_files = []
        
        for file_path in self.results_dir.glob("*.json"):
            if file_path.stat().st_mtime > cutoff_time:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['_file_path'] = str(file_path)
                        result_files.append(data)
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")
        
        print(f">> Loaded {len(result_files)} recent test result files")
        return result_files
    
    def extract_conversation_data(self, test_results: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Extract individual conversation data from test results"""
        all_conversations = []
        
        for result_file in test_results:
            # Handle different result file formats
            if 'individual_results' in result_file:
                # Phase 2/3 format
                for result in result_file['individual_results']:
                    if 'conversation_log' in result:
                        all_conversations.append(result)
            elif 'results' in result_file:
                # Phase 1 format
                for result in result_file['results']:
                    if 'conversation_log' in result:
                        all_conversations.append(result)
        
        # Separate successes and failures
        successes = [conv for conv in all_conversations if conv.get('success', False)]
        failures = [conv for conv in all_conversations if not conv.get('success', False)]
        
        print(f">> Extracted {len(all_conversations)} conversations:")
        print(f"   Successes: {len(successes)} ({len(successes)/len(all_conversations)*100:.1f}%)")
        print(f"   Failures: {len(failures)} ({len(failures)/len(all_conversations)*100:.1f}%)")
        
        return successes, failures
    
    def analyze_failure_case(self, failure_data: Dict) -> ConversationFailure:
        """Analyze a single failure case in detail"""
        conversation_log = failure_data.get('conversation_log', [])
        
        # Determine failure stage
        message_count = len([msg for msg in conversation_log if msg.get('type') == 'user'])
        if message_count <= 2:
            failure_stage = "early"
        elif message_count <= 5:
            failure_stage = "middle"
        else:
            failure_stage = "late"
        
        # Extract last messages
        user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
        agent_messages = [msg for msg in conversation_log if msg.get('type') == 'agent']
        
        last_user_message = user_messages[-1]['message'] if user_messages else ""
        last_agent_message = agent_messages[-1]['message'] if agent_messages else ""
        last_agent_decision = agent_messages[-1].get('decision', 'UNKNOWN') if agent_messages else 'UNKNOWN'
        
        # Extract decision sequence
        decisions_sequence = [msg.get('decision') for msg in agent_messages if msg.get('decision')]
        
        # Identify failure indicators
        failure_indicators = self._identify_failure_indicators(failure_data, conversation_log)
        
        # Determine failure reason
        failure_reason = self._determine_failure_reason(failure_data, conversation_log, failure_indicators)
        
        return ConversationFailure(
            conversation_id=failure_data.get('conversation_id', 'unknown'),
            persona_id=failure_data.get('persona_id', 'unknown'),
            persona_type=failure_data.get('persona_type', 'unknown'),
            failure_reason=failure_reason,
            failure_stage=failure_stage,
            message_count=message_count,
            duration=failure_data.get('duration', 0.0),
            last_agent_decision=last_agent_decision,
            last_user_message=last_user_message,
            last_agent_message=last_agent_message,
            decisions_sequence=decisions_sequence,
            failure_indicators=failure_indicators
        )
    
    def _identify_failure_indicators(self, failure_data: Dict, conversation_log: List[Dict]) -> List[str]:
        """Identify specific indicators that led to the failure"""
        indicators = []
        
        # Check for early termination
        message_count = len([msg for msg in conversation_log if msg.get('type') == 'user'])
        if message_count <= 1:
            indicators.append("extremely_short_conversation")
        elif message_count <= 2:
            indicators.append("very_short_conversation")
        
        # Check for agent END decisions
        agent_messages = [msg for msg in conversation_log if msg.get('type') == 'agent']
        if any(msg.get('decision') == 'END' for msg in agent_messages):
            indicators.append("agent_ended_conversation")
        
        # Check for user abandonment patterns
        user_messages = [msg for msg in conversation_log if msg.get('type') == 'user']
        if user_messages:
            last_user_msg = user_messages[-1]['message'].lower()
            
            # Look for rejection patterns
            rejection_phrases = ['not interested', 'no thanks', 'not right for me', 'changed my mind']
            if any(phrase in last_user_msg for phrase in rejection_phrases):
                indicators.append("explicit_user_rejection")
            
            # Look for confusion patterns
            confusion_phrases = ['what?', 'i don\'t understand', 'confused', 'unclear']
            if any(phrase in last_user_msg for phrase in confusion_phrases):
                indicators.append("user_confusion")
        
        # Check for repetitive patterns
        agent_responses = [msg['message'] for msg in agent_messages]
        if len(agent_responses) >= 2:
            # Check for similar responses (simplified)
            last_responses = agent_responses[-2:]
            if any(len(set(response.split()[:5])) < 3 for response in last_responses):
                indicators.append("repetitive_agent_responses")
        
        # Check for decision inconsistency
        decisions = [msg.get('decision') for msg in agent_messages if msg.get('decision')]
        if len(set(decisions)) > len(decisions) * 0.7:  # Too many different decisions
            indicators.append("inconsistent_decisions")
        
        # Check for long response times
        response_times = [msg.get('response_time', 0) for msg in agent_messages if msg.get('response_time')]
        if response_times and max(response_times) > 10.0:
            indicators.append("slow_agent_responses")
        
        # Check for errors
        if 'errors' in failure_data and failure_data['errors']:
            indicators.append("technical_errors")
        
        return indicators
    
    def _determine_failure_reason(self, failure_data: Dict, conversation_log: List[Dict], 
                                 indicators: List[str]) -> str:
        """Determine the primary reason for conversation failure"""
        
        # Priority-based failure reason determination
        if "technical_errors" in indicators:
            return "technical_error"
        elif "agent_ended_conversation" in indicators:
            return "premature_agent_termination"
        elif "explicit_user_rejection" in indicators:
            return "user_rejection"
        elif "user_confusion" in indicators:
            return "user_confusion"
        elif "extremely_short_conversation" in indicators:
            return "immediate_dropout"
        elif "very_short_conversation" in indicators:
            return "early_dropout"
        elif "repetitive_agent_responses" in indicators:
            return "poor_agent_responses"
        elif "inconsistent_decisions" in indicators:
            return "agent_decision_confusion"
        elif "slow_agent_responses" in indicators:
            return "performance_issues"
        else:
            return "unknown_failure"
    
    def identify_failure_patterns(self, failure_cases: List[ConversationFailure]) -> List[FailurePattern]:
        """Identify common patterns across failure cases"""
        patterns = []
        
        # Group failures by reason
        reason_groups = defaultdict(list)
        for failure in failure_cases:
            reason_groups[failure.failure_reason].append(failure)
        
        # Analyze each failure reason group
        for reason, failures in reason_groups.items():
            if len(failures) < 2:  # Need at least 2 cases to be a pattern
                continue
            
            # Analyze the pattern
            affected_personas = list(set(f.persona_id for f in failures))
            stages = [f.failure_stage for f in failures]
            message_counts = [f.message_count for f in failures]
            
            # Determine common characteristics
            common_stage = Counter(stages).most_common(1)[0][0] if stages else "unknown"
            avg_message_count = sum(message_counts) / len(message_counts) if message_counts else 0
            
            # Generate hypothesis and recommendations
            hypothesis, recommendations = self._generate_failure_hypothesis(reason, failures)
            
            pattern = FailurePattern(
                pattern_id=f"pattern_{reason}",
                pattern_name=reason.replace('_', ' ').title(),
                frequency=len(failures),
                affected_personas=affected_personas,
                common_failure_stage=common_stage,
                typical_message_count=avg_message_count,
                root_cause_hypothesis=hypothesis,
                recommended_fixes=recommendations,
                examples=[f.conversation_id for f in failures[:3]]  # First 3 examples
            )
            
            patterns.append(pattern)
        
        # Sort patterns by frequency (most common first)
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        
        return patterns
    
    def _generate_failure_hypothesis(self, reason: str, failures: List[ConversationFailure]) -> Tuple[str, List[str]]:
        """Generate hypothesis and recommendations for a failure pattern"""
        
        hypotheses = {
            "premature_agent_termination": (
                "Agent is ending conversations too early, possibly due to overly strict termination conditions or misinterpreting user intent.",
                [
                    "Review and relax agent END decision criteria",
                    "Improve user intent detection accuracy",
                    "Add more CONTINUE decisions for ambiguous cases",
                    "Implement conversation length minimums before allowing END"
                ]
            ),
            "immediate_dropout": (
                "Users or system are failing on the very first exchange, indicating fundamental initialization or greeting issues.",
                [
                    "Review initial greeting effectiveness",
                    "Check for technical initialization errors",
                    "Improve first-message persona responses",
                    "Add better error handling for conversation startup"
                ]
            ),
            "early_dropout": (
                "Conversations are ending after 1-2 exchanges, suggesting engagement or relevance issues in early conversation.",
                [
                    "Improve conversation opening strategies",
                    "Make agent responses more engaging and personalized",
                    "Better persona-agent matching in early turns",
                    "Add conversation flow guidance for early stages"
                ]
            ),
            "user_rejection": (
                "Users are explicitly rejecting the opportunity, which may be normal but could indicate poor targeting or presentation.",
                [
                    "Analyze rejection reasons for improvements",
                    "Improve initial value proposition presentation",
                    "Better persona-role matching",
                    "Consider if rejection rate is within normal bounds"
                ]
            ),
            "poor_agent_responses": (
                "Agent is providing repetitive or low-quality responses that fail to advance the conversation meaningfully.",
                [
                    "Improve response generation diversity",
                    "Add conversation state tracking to avoid repetition",
                    "Enhance agent reasoning and context awareness",
                    "Implement response quality checks"
                ]
            ),
            "user_confusion": (
                "Users are becoming confused by agent responses or conversation flow, indicating clarity or coherence issues.",
                [
                    "Simplify agent language and responses",
                    "Improve conversation flow logic",
                    "Add clarification mechanisms",
                    "Better context maintenance and referencing"
                ]
            ),
            "technical_error": (
                "Technical issues are causing conversation failures, indicating system reliability problems.",
                [
                    "Improve error handling and recovery",
                    "Add system monitoring and alerting",
                    "Implement graceful degradation",
                    "Review and fix underlying technical issues"
                ]
            ),
            "agent_decision_confusion": (
                "Agent is making inconsistent or inappropriate decisions, suggesting decision logic problems.",
                [
                    "Review and refine decision-making algorithms",
                    "Improve decision consistency mechanisms",
                    "Add decision validation and correction",
                    "Better training data for decision models"
                ]
            )
        }
        
        return hypotheses.get(reason, (
            "Unknown failure pattern - requires manual investigation",
            ["Conduct detailed manual analysis", "Review conversation logs", "Identify specific issues"]
        ))
    
    def compare_success_vs_failure_patterns(self, success_cases: List[Dict], 
                                          failure_cases: List[ConversationFailure]) -> Dict[str, Any]:
        """Compare patterns between successful and failed conversations"""
        
        # Analyze successful conversations
        success_message_counts = []
        success_durations = []
        success_decisions = []
        success_personas = []
        
        for success in success_cases:
            conv_log = success.get('conversation_log', [])
            user_msgs = [msg for msg in conv_log if msg.get('type') == 'user']
            agent_msgs = [msg for msg in conv_log if msg.get('type') == 'agent']
            
            success_message_counts.append(len(user_msgs))
            success_durations.append(success.get('duration', 0))
            success_decisions.extend([msg.get('decision') for msg in agent_msgs if msg.get('decision')])
            success_personas.append(success.get('persona_id', 'unknown'))
        
        # Analyze failed conversations
        failure_message_counts = [f.message_count for f in failure_cases]
        failure_durations = [f.duration for f in failure_cases]
        failure_decisions = []
        failure_personas = [f.persona_id for f in failure_cases]
        
        for failure in failure_cases:
            failure_decisions.extend(failure.decisions_sequence)
        
        return {
            "message_count_comparison": {
                "success_avg": sum(success_message_counts) / len(success_message_counts) if success_message_counts else 0,
                "failure_avg": sum(failure_message_counts) / len(failure_message_counts) if failure_message_counts else 0,
                "success_range": (min(success_message_counts), max(success_message_counts)) if success_message_counts else (0, 0),
                "failure_range": (min(failure_message_counts), max(failure_message_counts)) if failure_message_counts else (0, 0)
            },
            "duration_comparison": {
                "success_avg": sum(success_durations) / len(success_durations) if success_durations else 0,
                "failure_avg": sum(failure_durations) / len(failure_durations) if failure_durations else 0
            },
            "decision_patterns": {
                "success_decisions": dict(Counter(success_decisions).most_common(5)),
                "failure_decisions": dict(Counter(failure_decisions).most_common(5))
            },
            "persona_performance": {
                "success_personas": dict(Counter(success_personas).most_common()),
                "failure_personas": dict(Counter(failure_personas).most_common())
            }
        }
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run complete conversation failure analysis"""
        print(">> Starting Comprehensive Conversation Failure Analysis")
        print("=" * 60)
        
        # Load recent test data
        test_results = self.load_recent_test_results()
        if not test_results:
            print("X No recent test results found")
            return {"error": "No test data available"}
        
        # Extract conversation data
        successes, failures = self.extract_conversation_data(test_results)
        if not failures:
            print(">> No failures found - system performing well!")
            return {"status": "no_failures", "success_count": len(successes)}
        
        # Analyze each failure case
        print(f"\n>> Analyzing {len(failures)} failure cases...")
        failure_cases = []
        for failure_data in failures:
            try:
                failure_case = self.analyze_failure_case(failure_data)
                failure_cases.append(failure_case)
            except Exception as e:
                print(f"Warning: Could not analyze failure case: {e}")
        
        # Identify failure patterns
        print(f">> Identifying failure patterns...")
        failure_patterns = self.identify_failure_patterns(failure_cases)
        
        # Compare with successes
        print(f">> Comparing success vs failure patterns...")
        comparison = self.compare_success_vs_failure_patterns(successes, failure_cases)
        
        # Generate comprehensive report
        analysis_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "data_summary": {
                "total_conversations": len(successes) + len(failures),
                "successful_conversations": len(successes),
                "failed_conversations": len(failures),
                "success_rate": len(successes) / (len(successes) + len(failures)) * 100
            },
            "failure_cases": [
                {
                    "conversation_id": f.conversation_id,
                    "persona_id": f.persona_id,
                    "failure_reason": f.failure_reason,
                    "failure_stage": f.failure_stage,
                    "message_count": f.message_count,
                    "failure_indicators": f.failure_indicators
                }
                for f in failure_cases
            ],
            "failure_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_name": p.pattern_name,
                    "frequency": p.frequency,
                    "affected_personas": p.affected_personas,
                    "common_failure_stage": p.common_failure_stage,
                    "typical_message_count": p.typical_message_count,
                    "root_cause_hypothesis": p.root_cause_hypothesis,
                    "recommended_fixes": p.recommended_fixes
                }
                for p in failure_patterns
            ],
            "success_vs_failure_comparison": comparison,
            "key_insights": self._generate_key_insights(failure_patterns, comparison),
            "priority_fixes": self._prioritize_fixes(failure_patterns)
        }
        
        # Save analysis results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = config.SIMULATION_ROOT / "results" / f"conversation_failure_analysis_{timestamp}.json"
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        self.print_analysis_summary(analysis_results)
        
        return analysis_results
    
    def _generate_key_insights(self, patterns: List[FailurePattern], comparison: Dict) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        if patterns:
            # Most common failure pattern
            top_pattern = patterns[0]
            insights.append(f"Most common failure: {top_pattern.pattern_name} ({top_pattern.frequency} cases)")
            
            # Stage analysis
            stages = [p.common_failure_stage for p in patterns]
            stage_counts = Counter(stages)
            most_common_stage = stage_counts.most_common(1)[0][0]
            insights.append(f"Most failures occur in {most_common_stage} conversation stage")
            
            # Message count insight
            msg_comparison = comparison.get("message_count_comparison", {})
            success_avg = msg_comparison.get("success_avg", 0)
            failure_avg = msg_comparison.get("failure_avg", 0)
            
            if success_avg > failure_avg * 2:
                insights.append(f"Successful conversations are much longer ({success_avg:.1f} vs {failure_avg:.1f} messages)")
            
            # Decision pattern insights
            decision_patterns = comparison.get("decision_patterns", {})
            success_decisions = decision_patterns.get("success_decisions", {})
            failure_decisions = decision_patterns.get("failure_decisions", {})
            
            if "END" in failure_decisions and failure_decisions["END"] > success_decisions.get("END", 0):
                insights.append("Failed conversations have significantly more END decisions")
            
            # Persona insights
            persona_perf = comparison.get("persona_performance", {})
            if persona_perf.get("failure_personas"):
                worst_persona = max(persona_perf["failure_personas"].items(), key=lambda x: x[1])
                insights.append(f"Persona '{worst_persona[0]}' has the most failures ({worst_persona[1]} cases)")
        
        return insights
    
    def _prioritize_fixes(self, patterns: List[FailurePattern]) -> List[Dict[str, Any]]:
        """Prioritize fixes based on impact and frequency"""
        fixes = []
        
        for pattern in patterns:
            # Calculate priority score (frequency * severity)
            severity_weights = {
                "technical_error": 10,
                "premature_agent_termination": 8,
                "immediate_dropout": 9,
                "early_dropout": 7,
                "poor_agent_responses": 6,
                "user_confusion": 7,
                "agent_decision_confusion": 8
            }
            
            severity = severity_weights.get(pattern.pattern_id.replace("pattern_", ""), 5)
            priority_score = pattern.frequency * severity
            
            for fix in pattern.recommended_fixes:
                fixes.append({
                    "fix_description": fix,
                    "addresses_pattern": pattern.pattern_name,
                    "frequency": pattern.frequency,
                    "severity": severity,
                    "priority_score": priority_score,
                    "affected_personas": pattern.affected_personas
                })
        
        # Sort by priority score
        fixes.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return fixes[:10]  # Top 10 priority fixes
    
    def print_analysis_summary(self, results: Dict[str, Any]):
        """Print a comprehensive analysis summary"""
        print("\n" + "="*80)
        print(">> CONVERSATION FAILURE ANALYSIS RESULTS")
        print("="*80)
        
        # Data summary
        summary = results["data_summary"]
        print(f"\n>> Data Summary:")
        print(f"   Total Conversations: {summary['total_conversations']}")
        print(f"   Successful: {summary['successful_conversations']}")
        print(f"   Failed: {summary['failed_conversations']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        # Failure patterns
        patterns = results["failure_patterns"]
        if patterns:
            print(f"\n>> Top Failure Patterns:")
            for i, pattern in enumerate(patterns[:5], 1):
                print(f"   {i}. {pattern['pattern_name']}: {pattern['frequency']} cases")
                print(f"      Stage: {pattern['common_failure_stage']}, Avg Messages: {pattern['typical_message_count']:.1f}")
                print(f"      Hypothesis: {pattern['root_cause_hypothesis']}")
                print()
        
        # Key insights
        insights = results["key_insights"]
        if insights:
            print(f">> Key Insights:")
            for insight in insights:
                print(f"   - {insight}")
        
        # Priority fixes
        fixes = results["priority_fixes"]
        if fixes:
            print(f"\n>> Top Priority Fixes:")
            for i, fix in enumerate(fixes[:5], 1):
                print(f"   {i}. {fix['fix_description']}")
                print(f"      Addresses: {fix['addresses_pattern']} ({fix['frequency']} cases)")
                print(f"      Priority Score: {fix['priority_score']}")
                print()
        
        print("="*80 + "\n")


def main():
    """Main analysis entry point"""
    analyzer = ConversationFailureAnalyzer()
    results = analyzer.run_comprehensive_analysis()
    
    if "error" not in results:
        print(f"\n>> Analysis completed successfully!")
        print(f"   Results saved to: simulation_testing/results/conversation_failure_analysis_*.json")
        
        # Check if we have high-priority issues
        priority_fixes = results.get("priority_fixes", [])
        if priority_fixes:
            high_priority = [f for f in priority_fixes if f["priority_score"] > 50]
            if high_priority:
                print(f"\n!! CRITICAL: {len(high_priority)} high-priority fixes identified!")
                print("   Recommend implementing these fixes before continuing testing.")


if __name__ == "__main__":
    main()