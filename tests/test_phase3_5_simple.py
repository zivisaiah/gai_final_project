#!/usr/bin/env python3
"""
Phase 3.5: Simplified Evaluation Pipeline
Working evaluation of the multi-agent recruitment system
"""

import sys
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import Counter
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.agents.core_agent import CoreAgent, AgentDecision
from app.modules.agents.info_advisor import InfoAdvisor
from config.phase1_settings import get_settings


async def test_core_agent_decisions():
    """Test Core Agent decision making with simple cases"""
    print("🎯 Testing Core Agent Decision Making...")
    
    # Initialize Core Agent with default temperature
    try:
        core_agent = CoreAgent(
            model_name="gpt-3.5-turbo",  # Use reliable model
            vector_store_type="local"     # Use local for reliability
        )
        print("✅ Core Agent initialized")
    except Exception as e:
        print(f"❌ Core Agent initialization failed: {e}")
        return {"accuracy": 0.0, "total_tests": 0, "results": []}
    
    # Simple test cases for reliability
    test_cases = [
        # CONTINUE decisions
        {"message": "Hi, I'm interested in this position", "expected": "CONTINUE"},
        {"message": "Tell me about the company", "expected": "CONTINUE"},
        {"message": "I have questions about the role", "expected": "CONTINUE"},
        
        # INFO decisions (clear technical questions)
        {"message": "What programming languages are required?", "expected": "INFO"},
        {"message": "What are the main responsibilities?", "expected": "INFO"},
        {"message": "What experience is needed?", "expected": "INFO"},
        
        # SCHEDULE decisions (clear scheduling intent)
        {"message": "I'd like to schedule an interview", "expected": "SCHEDULE"},
        {"message": "When can we meet?", "expected": "SCHEDULE"},
        {"message": "Let's set up a time", "expected": "SCHEDULE"},
        
        # END decisions (clear disinterest)
        {"message": "I'm not interested", "expected": "END"},
        {"message": "I found another job", "expected": "END"},
        {"message": "This isn't a good fit", "expected": "END"},
    ]
    
    results = []
    correct_predictions = 0
    
    for i, test_case in enumerate(test_cases):
        try:
            message = test_case['message']
            expected = test_case['expected']
            
            # Use async process_message_async
            response, decision, reasoning = await core_agent.process_message_async(
                message, 
                conversation_id=f"test_{i}"
            )
            
            predicted = decision.value
            correct = predicted == expected
            
            if correct:
                correct_predictions += 1
            
            results.append({
                'message': message,
                'expected': expected,
                'predicted': predicted,
                'correct': correct
            })
            
            status = "✓" if correct else "✗"
            print(f"  Test {i+1:2d}: {expected:8s} -> {predicted:8s} {status}")
            
        except Exception as e:
            print(f"  Test {i+1:2d}: ERROR - {str(e)[:50]}...")
            results.append({
                'message': message,
                'expected': expected,
                'predicted': 'ERROR',
                'correct': False
            })
    
    accuracy = correct_predictions / len(test_cases) if test_cases else 0
    print(f"🎯 Core Agent Accuracy: {accuracy:.1%} ({correct_predictions}/{len(test_cases)})")
    
    return {
        "accuracy": accuracy,
        "total_tests": len(test_cases),
        "correct_predictions": correct_predictions,
        "results": results
    }


async def test_info_advisor_quality():
    """Test Info Advisor with fixed temperature issue"""
    print("📚 Testing Info Advisor Quality...")
    
    # Initialize Info Advisor with default temperature (1.0)
    try:
        info_advisor = InfoAdvisor(
            model_name="gpt-3.5-turbo",
            temperature=1.0,  # Use default temperature
            vector_store_type="local"
        )
        print("✅ Info Advisor initialized")
    except Exception as e:
        print(f"❌ Info Advisor initialization failed: {e}")
        return {"quality": 0.0, "total_tests": 0, "results": []}
    
    # Simple test questions
    test_questions = [
        "What programming languages are required?",
        "What are the main responsibilities?",
        "What experience is needed?",
        "What is the salary range?",  # Should have low confidence
        "What are the benefits?"      # Should have low confidence
    ]
    
    results = []
    quality_scores = []
    
    for i, question in enumerate(test_questions):
        try:
            start_time = time.time()
            response = await info_advisor.answer_question(question)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Simple quality evaluation
            has_answer = len(response.answer) > 10
            has_confidence = 0 <= response.confidence <= 1
            
            quality_score = (
                0.5 * has_answer +
                0.3 * has_confidence +
                0.2 * (response_time < 30)  # Reasonable response time
            )
            
            quality_scores.append(quality_score)
            
            results.append({
                'question': question,
                'answer_length': len(response.answer),
                'confidence': response.confidence,
                'response_time': response_time,
                'quality_score': quality_score
            })
            
            print(f"  Q{i+1}: conf={response.confidence:.2f} quality={quality_score:.2f} time={response_time:.1f}s")
            
        except Exception as e:
            print(f"  Q{i+1}: ERROR - {str(e)[:50]}...")
            results.append({
                'question': question,
                'answer_length': 0,
                'confidence': 0.0,
                'response_time': 0.0,
                'quality_score': 0.0
            })
            quality_scores.append(0.0)
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    print(f"📚 Info Advisor Quality: {avg_quality:.1%}")
    
    return {
        "quality": avg_quality,
        "total_tests": len(test_questions),
        "results": results
    }


def test_vector_database():
    """Test vector database functionality"""
    print("🗄️ Testing Vector Database...")
    
    try:
        from app.modules.database.vector_store import VectorStore
        
        # Test local vector store
        vector_store = VectorStore(
            collection_name="job_description_docs",
            embedding_function="sentence_transformers"
        )
        
        # Test search functionality
        test_queries = [
            "Python programming",
            "responsibilities",
            "experience required"
        ]
        
        search_results = []
        for query in test_queries:
            try:
                results = vector_store.search(query, n_results=2)
                has_results = len(results.get("documents", [[]])[0]) > 0
                search_results.append(has_results)
                print(f"  Query '{query}': {'✓' if has_results else '✗'}")
            except Exception as e:
                print(f"  Query '{query}': ERROR - {str(e)[:30]}...")
                search_results.append(False)
        
        success_rate = sum(search_results) / len(search_results) if search_results else 0
        print(f"🗄️ Vector DB Success Rate: {success_rate:.1%}")
        
        return {
            "success_rate": success_rate,
            "total_queries": len(test_queries),
            "successful_queries": sum(search_results)
        }
        
    except Exception as e:
        print(f"❌ Vector DB test failed: {e}")
        return {"success_rate": 0.0, "total_queries": 0, "successful_queries": 0}


async def run_simplified_evaluation():
    """Run simplified but working evaluation"""
    print("🚀 STARTING PHASE 3.5: SIMPLIFIED EVALUATION")
    print("="*60)
    
    start_time = time.time()
    
    try:
        # 1. Test Core Agent
        core_results = await test_core_agent_decisions()
        
        # 2. Test Info Advisor
        info_results = await test_info_advisor_quality()
        
        # 3. Test Vector Database
        vector_results = test_vector_database()
        
        # 4. Calculate overall system score
        core_accuracy = core_results["accuracy"]
        info_quality = info_results["quality"]
        vector_success = vector_results["success_rate"]
        
        # Weighted system score
        system_score = (
            0.5 * core_accuracy +    # Core Agent is most important
            0.3 * info_quality +     # Info Advisor quality
            0.2 * vector_success     # Vector DB reliability
        )
        
        # 5. Generate summary
        print("\n" + "="*60)
        print("📋 PHASE 3.5 SIMPLIFIED EVALUATION SUMMARY")
        print("="*60)
        
        print(f"\n🎯 PERFORMANCE METRICS:")
        print(f"   Core Agent Accuracy:    {core_accuracy:.1%}")
        print(f"   Info Advisor Quality:   {info_quality:.1%}")
        print(f"   Vector DB Success:      {vector_success:.1%}")
        print(f"   Overall System Score:   {system_score:.1%}")
        
        # Check target achievement
        target_met = system_score >= 0.85
        print(f"\n🎯 TARGET (85%): {'✅ ACHIEVED' if target_met else '❌ NOT MET'}")
        
        if target_met:
            print("🎉 EXCELLENT! System meets performance targets.")
            print("✅ Ready for Phase 3.6: Deployment Preparation")
        else:
            gap = 0.85 - system_score
            print(f"⚠️  Improvement needed: {gap:.1%} points below target")
            
            # Specific recommendations
            if core_accuracy < 0.7:
                print("💡 Priority: Improve Core Agent decision accuracy")
            if info_quality < 0.7:
                print("💡 Priority: Improve Info Advisor responses")
            if vector_success < 0.7:
                print("💡 Priority: Fix vector database issues")
        
        # 6. Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = Path("tests/evaluation_results")
        results_dir.mkdir(exist_ok=True)
        
        evaluation_report = {
            "timestamp": timestamp,
            "system_score": system_score,
            "target_met": target_met,
            "core_agent": core_results,
            "info_advisor": info_results,
            "vector_database": vector_results,
            "evaluation_type": "simplified"
        }
        
        report_file = results_dir / f"simplified_eval_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(evaluation_report, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {report_file}")
        
        # 7. Performance summary
        end_time = time.time()
        total_time = end_time - start_time
        print(f"⏱️  Total evaluation time: {total_time:.1f}s")
        print("="*60)
        
        return evaluation_report
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    # Run the simplified evaluation
    try:
        results = asyncio.run(run_simplified_evaluation())
        
        if results["target_met"]:
            print("\n🎯 Phase 3.5 EVALUATION COMPLETE!")
            sys.exit(0)
        else:
            print("\n⚠️  Phase 3.5 needs improvement")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Evaluation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Evaluation error: {e}")
        sys.exit(1) 