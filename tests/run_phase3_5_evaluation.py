#!/usr/bin/env python3
"""
Phase 3.5: Complete Evaluation Pipeline Runner
Comprehensive evaluation of the multi-agent recruitment system
"""

import sys
import json
import asyncio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
import time

# ML evaluation metrics
from sklearn.metrics import (
    confusion_matrix, 
    classification_report, 
    accuracy_score,
    precision_recall_fscore_support
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.agents.core_agent import CoreAgent, AgentDecision
from app.modules.agents.info_advisor import InfoAdvisor
from app.modules.agents.scheduling_advisor import SchedulingAdvisor
from app.modules.agents.exit_advisor import ExitAdvisor
from config.phase1_settings import get_settings


class SystemEvaluator:
    """Complete system evaluation pipeline for Phase 3.5"""
    
    def __init__(self):
        """Initialize the evaluation system"""
        self.settings = get_settings()
        self.results_dir = Path("tests/evaluation_results")
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize agents
        self.initialize_agents()
        
        # Define test cases
        self.setup_test_cases()
    
    def initialize_agents(self):
        """Initialize all agents for testing"""
        print("🤖 Initializing agents for evaluation...")
        
        try:
            # Core Agent with INFO capability
            self.core_agent = CoreAgent(
                model_name=self.settings.OPENAI_MODEL,
                vector_store_type="openai"
            )
            print("✅ Core Agent initialized")
            
            # Info Advisor
            self.info_advisor = InfoAdvisor(
                model_name=self.settings.OPENAI_MODEL,
                vector_store_type="openai"
            )
            print("✅ Info Advisor initialized")
            
            # Scheduling Advisor
            self.scheduling_advisor = SchedulingAdvisor(
                model_name=self.settings.OPENAI_MODEL
            )
            print("✅ Scheduling Advisor initialized")
            
            # Exit Advisor
            self.exit_advisor = ExitAdvisor(
                model_name=self.settings.OPENAI_MODEL
            )
            print("✅ Exit Advisor initialized")
            
        except Exception as e:
            print(f"❌ Error initializing agents: {e}")
            raise
    
    def setup_test_cases(self):
        """Define comprehensive test cases"""
        # Core Agent test cases
        self.core_agent_test_cases = [
            # CONTINUE decisions (5 cases)
            {"message": "Hi, I'm interested in learning more about this position", "expected": "CONTINUE"},
            {"message": "Tell me about your company culture", "expected": "CONTINUE"},
            {"message": "I have some questions about the role", "expected": "CONTINUE"},
            {"message": "What's the work environment like?", "expected": "CONTINUE"},
            {"message": "Can you tell me more about the team?", "expected": "CONTINUE"},
            
            # INFO decisions (8 cases)
            {"message": "What programming languages are required for this position?", "expected": "INFO"},
            {"message": "What are the main responsibilities of this role?", "expected": "INFO"},
            {"message": "What experience level is needed?", "expected": "INFO"},
            {"message": "What technologies should I know?", "expected": "INFO"},
            {"message": "What qualifications are required?", "expected": "INFO"},
            {"message": "What frameworks are mentioned in the job description?", "expected": "INFO"},
            {"message": "What skills are most important for this position?", "expected": "INFO"},
            {"message": "What kind of projects will I work on?", "expected": "INFO"},
            
            # SCHEDULE decisions (5 cases)
            {"message": "I'd like to schedule an interview", "expected": "SCHEDULE"},
            {"message": "When can we meet for an interview?", "expected": "SCHEDULE"},
            {"message": "Let's set up a time to talk", "expected": "SCHEDULE"},
            {"message": "I'm ready to schedule our interview", "expected": "SCHEDULE"},
            {"message": "Can we book a time slot?", "expected": "SCHEDULE"},
            
            # END decisions (5 cases)
            {"message": "I'm not interested in this position", "expected": "END"},
            {"message": "I found another job, thanks", "expected": "END"},
            {"message": "This role isn't a good fit for me", "expected": "END"},
            {"message": "I'll pass on this opportunity", "expected": "END"},
            {"message": "Thank you, but I'm not interested", "expected": "END"}
        ]
        
        # Info Advisor test cases
        self.info_advisor_test_cases = [
            # Technical requirements (high confidence expected)
            {"question": "What programming languages are required?", "category": "technical", "expected_confidence": 0.8},
            {"question": "What frameworks should I know?", "category": "technical", "expected_confidence": 0.8},
            {"question": "What development tools are used?", "category": "technical", "expected_confidence": 0.7},
            
            # Job responsibilities (high confidence expected)
            {"question": "What are the main responsibilities?", "category": "responsibilities", "expected_confidence": 0.8},
            {"question": "What will I be doing day to day?", "category": "responsibilities", "expected_confidence": 0.7},
            {"question": "What tasks are involved?", "category": "responsibilities", "expected_confidence": 0.7},
            
            # Qualifications (high confidence expected)
            {"question": "What experience is needed?", "category": "qualifications", "expected_confidence": 0.8},
            {"question": "What skills are required?", "category": "qualifications", "expected_confidence": 0.8},
            {"question": "What background should I have?", "category": "qualifications", "expected_confidence": 0.7},
            
            # Out of scope (low confidence expected)
            {"question": "What's the salary range?", "category": "unknown", "expected_confidence": 0.3},
            {"question": "Do you offer remote work?", "category": "unknown", "expected_confidence": 0.3},
            {"question": "What are the benefits?", "category": "unknown", "expected_confidence": 0.3}
        ]
        
        print(f"📊 Test cases prepared:")
        print(f"   Core Agent: {len(self.core_agent_test_cases)} cases")
        print(f"   Info Advisor: {len(self.info_advisor_test_cases)} cases")
    
    async def evaluate_core_agent(self):
        """Evaluate Core Agent decision making"""
        print("🎯 Evaluating Core Agent decision making...")
        
        results = []
        y_true = []
        y_pred = []
        
        for i, test_case in enumerate(self.core_agent_test_cases):
            try:
                message = test_case['message']
                expected = test_case['expected']
                
                # Get Core Agent decision
                response, decision, reasoning = self.core_agent.process_message(
                    message, 
                    conversation_id=f"eval_test_{i}"
                )
                
                predicted = decision.value
                correct = predicted == expected
                
                results.append({
                    'message': message,
                    'expected': expected,
                    'predicted': predicted,
                    'correct': correct,
                    'reasoning': reasoning,
                    'response': response[:100] + '...' if len(response) > 100 else response
                })
                
                y_true.append(expected)
                y_pred.append(predicted)
                
                status = "✓" if correct else "✗"
                print(f"  Test {i+1:2d}: {expected:8s} -> {predicted:8s} {status}")
                
            except Exception as e:
                print(f"  Test {i+1:2d}: ERROR - {e}")
                results.append({
                    'message': message,
                    'expected': expected,
                    'predicted': 'ERROR',
                    'correct': False,
                    'reasoning': str(e),
                    'response': 'ERROR'
                })
                y_true.append(expected)
                y_pred.append('ERROR')
        
        # Calculate metrics
        accuracy = sum(r['correct'] for r in results) / len(results)
        print(f"🎯 Core Agent Accuracy: {accuracy:.1%}")
        
        return results, y_true, y_pred, accuracy
    
    async def evaluate_info_advisor(self):
        """Evaluate Info Advisor Q&A quality"""
        print("📚 Evaluating Info Advisor Q&A quality...")
        
        results = []
        confidence_scores = []
        response_times = []
        
        for i, test_case in enumerate(self.info_advisor_test_cases):
            try:
                question = test_case['question']
                expected_confidence = test_case['expected_confidence']
                category = test_case['category']
                
                start_time = time.time()
                
                # Get Info Advisor response
                response = await self.info_advisor.answer_question(question)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Evaluate response quality
                confidence_met = (
                    response.confidence >= expected_confidence * 0.8  # 20% tolerance
                )
                
                has_answer = len(response.answer) > 20  # Non-trivial answer
                has_context = response.has_context
                
                quality_score = (
                    0.4 * confidence_met +
                    0.3 * has_answer +
                    0.3 * has_context
                )
                
                results.append({
                    'question': question,
                    'category': category,
                    'expected_confidence': expected_confidence,
                    'actual_confidence': response.confidence,
                    'confidence_met': confidence_met,
                    'has_answer': has_answer,
                    'has_context': has_context,
                    'quality_score': quality_score,
                    'response_time': response_time,
                    'answer_length': len(response.answer),
                    'sources_count': len(response.sources_used)
                })
                
                confidence_scores.append(response.confidence)
                response_times.append(response_time)
                
                print(f"  Q{i+1:2d}: {category:13s} conf={response.confidence:.2f} quality={quality_score:.2f}")
                
            except Exception as e:
                print(f"  Q{i+1:2d}: ERROR - {e}")
                results.append({
                    'question': question,
                    'category': category,
                    'expected_confidence': expected_confidence,
                    'actual_confidence': 0.0,
                    'confidence_met': False,
                    'has_answer': False,
                    'has_context': False,
                    'quality_score': 0.0,
                    'response_time': 0.0,
                    'answer_length': 0,
                    'sources_count': 0
                })
        
        # Calculate metrics
        avg_quality = np.mean([r['quality_score'] for r in results])
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        avg_response_time = np.mean(response_times) if response_times else 0
        
        print(f"📚 Info Advisor Quality: {avg_quality:.1%}")
        print(f"   Average Confidence: {avg_confidence:.2f}")
        print(f"   Average Response Time: {avg_response_time:.2f}s")
        
        return results, avg_quality, avg_confidence, avg_response_time
    
    def generate_confusion_matrix(self, y_true, y_pred, accuracy):
        """Generate and save confusion matrix"""
        labels = ['CONTINUE', 'INFO', 'SCHEDULE', 'END']
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        # Plot confusion matrix
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=labels, yticklabels=labels)
        plt.title(f'Core Agent Decision Confusion Matrix\nAccuracy: {accuracy:.1%}')
        plt.ylabel('True Decision')
        plt.xlabel('Predicted Decision')
        plt.tight_layout()
        
        # Save plot
        confusion_file = self.results_dir / f"confusion_matrix_{self.timestamp}.png"
        plt.savefig(confusion_file, dpi=300, bbox_inches='tight')
        plt.savefig(self.results_dir / "latest_confusion_matrix.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        return cm, classification_report(y_true, y_pred, labels=labels, output_dict=True)
    
    def calculate_system_score(self, core_accuracy, info_quality):
        """Calculate overall system performance score"""
        # Weighted combination: Core Agent is more critical
        system_score = (
            0.6 * core_accuracy +  # Core Agent weight
            0.4 * info_quality     # Info Advisor weight
        )
        return system_score
    
    def save_results(self, core_results, info_results, core_accuracy, info_quality, 
                    system_score, classification_report):
        """Save comprehensive evaluation results"""
        # Comprehensive evaluation report
        evaluation_report = {
            "timestamp": self.timestamp,
            "system_performance": {
                "overall_score": system_score,
                "target_met": system_score >= 0.85,
                "target_threshold": 0.85
            },
            "core_agent": {
                "accuracy": core_accuracy,
                "total_tests": len(core_results),
                "correct_predictions": sum(r['correct'] for r in core_results),
                "classification_report": classification_report
            },
            "info_advisor": {
                "average_quality_score": info_quality,
                "total_tests": len(info_results)
            },
            "evaluation_config": {
                "model": self.settings.OPENAI_MODEL,
                "temperature": self.settings.OPENAI_TEMPERATURE
            }
        }
        
        # Save to JSON
        report_file = self.results_dir / f"evaluation_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_report, f, indent=2, default=str)
        
        # Save latest results (overwrite)
        latest_file = self.results_dir / "latest_evaluation.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_report, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {report_file}")
        return evaluation_report
    
    def print_summary(self, core_accuracy, info_quality, system_score):
        """Print evaluation summary"""
        print("\n" + "="*60)
        print("📋 PHASE 3.5 EVALUATION SUMMARY")
        print("="*60)
        
        print(f"\n🎯 PERFORMANCE METRICS:")
        print(f"   Core Agent Accuracy:  {core_accuracy:.1%}")
        print(f"   Info Advisor Quality: {info_quality:.1%}")
        print(f"   Overall System Score: {system_score:.1%}")
        
        # Check target achievement
        target_met = system_score >= 0.85
        print(f"\n🎯 TARGET (85%): {'✅ ACHIEVED' if target_met else '❌ NOT MET'}")
        
        if target_met:
            print("🎉 EXCELLENT! System exceeds performance targets.")
            print("✅ Ready for Phase 3.6: Deployment Preparation")
        else:
            gap = 0.85 - system_score
            print(f"⚠️  Improvement needed: {gap:.1%} points below target")
            print("💡 Consider fine-tuning before deployment")
        
        print(f"\n📊 Detailed results saved to: tests/evaluation_results/")
        print("="*60)
    
    async def run_complete_evaluation(self):
        """Run the complete evaluation pipeline"""
        print("🚀 STARTING PHASE 3.5: COMPLETE EVALUATION PIPELINE")
        print("="*60)
        
        start_time = time.time()
        
        try:
            # 1. Evaluate Core Agent
            core_results, y_true, y_pred, core_accuracy = await self.evaluate_core_agent()
            
            # 2. Evaluate Info Advisor
            info_results, info_quality, avg_confidence, avg_response_time = await self.evaluate_info_advisor()
            
            # 3. Generate confusion matrix and classification report
            cm, class_report = self.generate_confusion_matrix(y_true, y_pred, core_accuracy)
            
            # 4. Calculate overall system score
            system_score = self.calculate_system_score(core_accuracy, info_quality)
            
            # 5. Save results
            evaluation_report = self.save_results(
                core_results, info_results, core_accuracy, info_quality,
                system_score, class_report
            )
            
            # 6. Print summary
            self.print_summary(core_accuracy, info_quality, system_score)
            
            # 7. Performance summary
            end_time = time.time()
            total_time = end_time - start_time
            print(f"\n⏱️  Total evaluation time: {total_time:.2f}s")
            print(f"📊 Tests completed: {len(core_results) + len(info_results)}")
            
            return evaluation_report
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            raise


async def main():
    """Main evaluation entry point"""
    evaluator = SystemEvaluator()
    return await evaluator.run_complete_evaluation()


if __name__ == "__main__":
    # Run the complete evaluation
    try:
        evaluation_results = asyncio.run(main())
        
        # Check if we should proceed to next phase
        if evaluation_results["system_performance"]["target_met"]:
            print("\n🎯 Phase 3.5 COMPLETE - Ready for Phase 3.6!")
        else:
            print("\n⚠️  Phase 3.5 needs improvement before proceeding")
            
    except KeyboardInterrupt:
        print("\n⏹️  Evaluation interrupted by user")
    except Exception as e:
        print(f"\n❌ Evaluation error: {e}")
        sys.exit(1) 