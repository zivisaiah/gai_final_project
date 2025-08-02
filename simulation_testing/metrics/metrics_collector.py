"""
Basic Metrics Collection System
Tracks agent decision accuracy and user experience metrics
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class ConversationMetrics:
    """Metrics for a single conversation"""
    conversation_id: str
    persona_id: str
    persona_type: str
    start_time: float
    end_time: Optional[float] = None
    total_messages: int = 0
    agent_decisions: List[Dict] = None
    response_times: List[float] = None
    success: bool = False
    completion_stage: str = "started"  # started, chatting, scheduling, completed, failed
    errors: List[str] = None
    
    def __post_init__(self):
        if self.agent_decisions is None:
            self.agent_decisions = []
        if self.response_times is None:
            self.response_times = []
        if self.errors is None:
            self.errors = []
    
    def add_agent_decision(self, decision: str, reasoning: str, response_time: float):
        """Add an agent decision to metrics"""
        self.agent_decisions.append({
            'decision': decision,
            'reasoning': reasoning,
            'response_time': response_time,
            'timestamp': time.time()
        })
        self.response_times.append(response_time)
    
    def add_error(self, error: str):
        """Add an error to metrics"""
        self.errors.append({
            'error': error,
            'timestamp': time.time()
        })
    
    def complete_conversation(self, success: bool, completion_stage: str):
        """Mark conversation as completed"""
        self.end_time = time.time()
        self.success = success
        self.completion_stage = completion_stage
    
    def get_duration(self) -> float:
        """Get conversation duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if self.response_times:
            return sum(self.response_times) / len(self.response_times)
        return 0.0

class MetricsCollector:
    """Collects and manages simulation metrics"""
    
    def __init__(self, results_dir: Optional[Path] = None):
        if results_dir is None:
            results_dir = Path(__file__).parent.parent / "results"
        self.results_dir = results_dir
        self.results_dir.mkdir(exist_ok=True)
        
        self.conversations: Dict[str, ConversationMetrics] = {}
        self.session_start_time = time.time()
        
    def start_conversation(self, conversation_id: str, persona_id: str, persona_type: str) -> ConversationMetrics:
        """Start tracking a new conversation"""
        metrics = ConversationMetrics(
            conversation_id=conversation_id,
            persona_id=persona_id,
            persona_type=persona_type,
            start_time=time.time()
        )
        self.conversations[conversation_id] = metrics
        return metrics
    
    def get_conversation_metrics(self, conversation_id: str) -> Optional[ConversationMetrics]:
        """Get metrics for a specific conversation"""
        return self.conversations.get(conversation_id)
    
    def record_agent_decision(self, conversation_id: str, decision: str, reasoning: str, response_time: float):
        """Record an agent decision"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].add_agent_decision(decision, reasoning, response_time)
    
    def record_error(self, conversation_id: str, error: str):
        """Record an error"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].add_error(error)
    
    def complete_conversation(self, conversation_id: str, success: bool, completion_stage: str):
        """Mark a conversation as completed"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].complete_conversation(success, completion_stage)
    
    def increment_message_count(self, conversation_id: str):
        """Increment message count for a conversation"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].total_messages += 1
    
    def generate_summary_report(self) -> Dict:
        """Generate a summary report of all metrics"""
        total_conversations = len(self.conversations)
        if total_conversations == 0:
            return {"error": "No conversations recorded"}
        
        successful_conversations = sum(1 for conv in self.conversations.values() if conv.success)
        
        # Aggregate metrics
        total_messages = sum(conv.total_messages for conv in self.conversations.values())
        total_decisions = sum(len(conv.agent_decisions) for conv in self.conversations.values())
        total_errors = sum(len(conv.errors) for conv in self.conversations.values())
        
        # Response time statistics
        all_response_times = []
        for conv in self.conversations.values():
            all_response_times.extend(conv.response_times)
        
        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        
        # Decision breakdown
        decision_counts = {}
        for conv in self.conversations.values():
            for decision_data in conv.agent_decisions:
                decision = decision_data['decision']
                decision_counts[decision] = decision_counts.get(decision, 0) + 1
        
        # Completion stage breakdown
        stage_counts = {}
        for conv in self.conversations.values():
            stage = conv.completion_stage
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        # Persona performance
        persona_performance = {}
        for conv in self.conversations.values():
            persona_type = conv.persona_type
            if persona_type not in persona_performance:
                persona_performance[persona_type] = {"total": 0, "successful": 0}
            persona_performance[persona_type]["total"] += 1
            if conv.success:
                persona_performance[persona_type]["successful"] += 1
        
        return {
            "session_summary": {
                "total_conversations": total_conversations,
                "successful_conversations": successful_conversations,
                "success_rate": successful_conversations / total_conversations * 100,
                "total_messages": total_messages,
                "total_decisions": total_decisions,
                "total_errors": total_errors,
                "average_response_time": round(avg_response_time, 2),
                "session_duration": time.time() - self.session_start_time
            },
            "decision_breakdown": decision_counts,
            "completion_stages": stage_counts,
            "persona_performance": persona_performance,
            "error_rate": total_errors / total_conversations if total_conversations > 0 else 0
        }
    
    def save_results(self, filename: Optional[str] = None):
        """Save all metrics to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_results_{timestamp}.json"
        
        results_file = self.results_dir / filename
        
        # Convert conversations to serializable format
        serializable_conversations = {}
        for conv_id, conv in self.conversations.items():
            serializable_conversations[conv_id] = asdict(conv)
        
        results_data = {
            "session_info": {
                "timestamp": datetime.now().isoformat(),
                "session_duration": time.time() - self.session_start_time,
                "total_conversations": len(self.conversations)
            },
            "conversations": serializable_conversations,
            "summary": self.generate_summary_report()
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2)
        
        print(f">> Results saved to: {results_file}")
        return results_file
    
    def print_summary(self):
        """Print a summary of metrics to console"""
        summary = self.generate_summary_report()
        
        if "error" in summary:
            print(f"X {summary['error']}")
            return
        
        session = summary["session_summary"]
        
        print("\n" + "="*60)
        print(">> SIMULATION RESULTS SUMMARY")
        print("="*60)
        
        print(f"\n>> Overall Performance:")
        print(f"   Total Conversations: {session['total_conversations']}")
        print(f"   Successful Conversations: {session['successful_conversations']}")
        print(f"   Success Rate: {session['success_rate']:.1f}%")
        print(f"   Total Messages: {session['total_messages']}")
        print(f"   Total Agent Decisions: {session['total_decisions']}")
        print(f"   Average Response Time: {session['average_response_time']}s")
        print(f"   Total Errors: {session['total_errors']}")
        
        print(f"\n>> Agent Decisions:")
        for decision, count in summary["decision_breakdown"].items():
            print(f"   {decision}: {count}")
        
        print(f"\n>> Completion Stages:")
        for stage, count in summary["completion_stages"].items():
            print(f"   {stage}: {count}")
        
        print(f"\n>> Persona Performance:")
        for persona, stats in summary["persona_performance"].items():
            success_rate = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"   {persona}: {stats['successful']}/{stats['total']} ({success_rate:.1f}%)")
        
        print("\n" + "="*60 + "\n")

# Global metrics collector instance
metrics_collector = MetricsCollector()