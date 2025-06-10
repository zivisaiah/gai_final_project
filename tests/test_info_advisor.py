#!/usr/bin/env python3
"""
Test suite for Info Advisor functionality
Tests RAG-based question answering with vector database integration
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.agents.info_advisor import InfoAdvisor, InfoResponse
from app.modules.database.vector_store import VectorStore


class TestInfoAdvisor:
    """Test cases for Info Advisor functionality"""
    
    @pytest.fixture
    def info_advisor(self):
        """Create Info Advisor instance for testing"""
        return InfoAdvisor(temperature=0.3)
    
    @pytest.fixture
    def vector_store(self):
        """Create Vector Store instance for testing"""
        return VectorStore(
            collection_name="job_description_docs",
            embedding_function="sentence_transformers"
        )
    
    def test_initialization(self, info_advisor):
        """Test Info Advisor initialization"""
        assert info_advisor is not None
        assert info_advisor.model_name is not None
        assert info_advisor.vector_store is not None
        assert info_advisor.tools is not None
        assert len(info_advisor.tools) > 0
    
    def test_vector_store_status(self, info_advisor):
        """Test vector store status check"""
        status = info_advisor.get_vector_store_status()
        
        assert status["available"] is True
        assert "collection_name" in status
        assert "document_count" in status
        assert status["status"] == "operational"
    
    def test_document_retrieval(self, info_advisor):
        """Test document retrieval functionality"""
        test_queries = [
            "What programming languages are required?",
            "What are the main responsibilities?",
            "What experience is needed?",
            "What technologies should I know?"
        ]
        
        retrieval_test = info_advisor.test_retrieval(test_queries)
        
        assert "results" in retrieval_test
        assert len(retrieval_test["results"]) == len(test_queries)
        
        # Check that all queries found results
        for query, result in retrieval_test["results"].items():
            assert result["found_results"] is True
            assert result["context_length"] > 0
            assert len(result["sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_technical_questions(self, info_advisor):
        """Test answering technical requirement questions"""
        questions = [
            "What programming languages are required for this position?",
            "What frameworks should I know?",
            "What technologies are used in the development stack?"
        ]
        
        for question in questions:
            response = await info_advisor.answer_question(question)
            
            assert isinstance(response, InfoResponse)
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.confidence >= 0.7  # Should have high confidence with context
            assert response.question_type == "technical_requirements"
            assert response.has_context is True
            assert len(response.sources_used) > 0
    
    @pytest.mark.asyncio
    async def test_job_responsibility_questions(self, info_advisor):
        """Test answering job responsibility questions"""
        questions = [
            "What are the main responsibilities of this role?",
            "What will I be doing day to day?",
            "What tasks are involved in this position?"
        ]
        
        for question in questions:
            response = await info_advisor.answer_question(question)
            
            assert isinstance(response, InfoResponse)
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.confidence >= 0.7
            assert response.question_type == "job_responsibilities"
            assert response.has_context is True
    
    @pytest.mark.asyncio
    async def test_qualification_questions(self, info_advisor):
        """Test answering qualification questions"""
        questions = [
            "What experience level is needed?",
            "What qualifications are required?",
            "What skills should I have?"
        ]
        
        for question in questions:
            response = await info_advisor.answer_question(question)
            
            assert isinstance(response, InfoResponse)
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.confidence >= 0.7
            assert response.question_type == "qualifications"
            assert response.has_context is True
    
    @pytest.mark.asyncio
    async def test_unknown_topic_questions(self, info_advisor):
        """Test handling questions about topics not in the job description"""
        questions = [
            "What is the salary range?",
            "Do you offer remote work options?",
            "What are the company benefits?"
        ]
        
        for question in questions:
            response = await info_advisor.answer_question(question)
            
            assert isinstance(response, InfoResponse)
            assert response.answer is not None
            assert len(response.answer) > 0
            # Should acknowledge lack of specific information
            assert "don't have specific information" in response.answer.lower() or \
                   "not explicitly mentioned" in response.answer.lower() or \
                   "not specify" in response.answer.lower()
    
    @pytest.mark.asyncio
    async def test_conversation_history_context(self, info_advisor):
        """Test answering questions with conversation history"""
        conversation_history = [
            {"role": "user", "content": "Hi, I'm interested in the Python developer position"},
            {"role": "assistant", "content": "Great! I'd be happy to help you learn more about our Python Developer position."},
            {"role": "user", "content": "I have 3 years of Python experience"}
        ]
        
        question = "What specific Python frameworks are mentioned in the job requirements?"
        
        response = await info_advisor.answer_question(
            question=question,
            conversation_history=conversation_history
        )
        
        assert isinstance(response, InfoResponse)
        assert response.answer is not None
        assert len(response.answer) > 0
        assert response.confidence >= 0.7
        assert response.has_context is True
    
    @pytest.mark.asyncio
    async def test_response_structure(self, info_advisor):
        """Test that all responses have proper structure"""
        question = "What programming languages are required?"
        
        response = await info_advisor.answer_question(question)
        
        # Check InfoResponse structure
        assert hasattr(response, 'answer')
        assert hasattr(response, 'confidence')
        assert hasattr(response, 'sources_used')
        assert hasattr(response, 'question_type')
        assert hasattr(response, 'has_context')
        
        # Check types
        assert isinstance(response.answer, str)
        assert isinstance(response.confidence, float)
        assert isinstance(response.sources_used, list)
        assert isinstance(response.question_type, str)
        assert isinstance(response.has_context, bool)
        
        # Check value ranges
        assert 0.0 <= response.confidence <= 1.0
        assert len(response.answer) > 0
    
    def test_direct_vector_search(self, vector_store):
        """Test direct vector store search functionality"""
        test_queries = [
            "Python programming requirements",
            "job responsibilities and duties",
            "required experience and qualifications"
        ]
        
        for query in test_queries:
            results = vector_store.similarity_search(query, n_results=1)
            
            assert len(results) > 0
            assert 'document' in results[0]
            assert 'metadata' in results[0]
            assert len(results[0]['document']) > 0
    
    def test_question_classification(self, info_advisor):
        """Test question classification functionality"""
        from app.modules.prompts.info_prompts import classify_question
        
        test_cases = [
            ("What programming languages are required?", "technical_requirements"),
            ("What are the main responsibilities?", "job_responsibilities"),
            ("What experience do I need?", "qualifications"),
            ("Do you offer remote work?", "company_culture"),
            ("What is the salary?", "compensation")
        ]
        
        for question, expected_type in test_cases:
            classified_type = classify_question(question)
            assert classified_type == expected_type


# Integration tests
class TestInfoAdvisorIntegration:
    """Integration tests for Info Advisor with other components"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_qa_flow(self):
        """Test complete question-answering flow"""
        # Initialize Info Advisor
        info_advisor = InfoAdvisor(temperature=0.3)
        
        # Test a comprehensive question
        question = "I'm a Python developer with 5 years experience. What technologies and frameworks should I know for this position?"
        
        response = await info_advisor.answer_question(question)
        
        # Verify response quality
        assert response.has_context is True
        assert response.confidence >= 0.7
        assert "python" in response.answer.lower()
        assert len(response.sources_used) > 0
        
        # Should mention specific technologies from the job description
        answer_lower = response.answer.lower()
        expected_technologies = ["numpy", "pandas", "django", "flask"]
        
        # At least some technologies should be mentioned
        mentioned_count = sum(1 for tech in expected_technologies if tech in answer_lower)
        assert mentioned_count > 0


if __name__ == "__main__":
    # Run specific tests for quick verification
    import asyncio
    
    async def quick_test():
        print("🧠 Running Quick Info Advisor Tests...")
        
        # Test initialization
        info_advisor = InfoAdvisor(temperature=0.3)
        print("✅ Info Advisor initialized")
        
        # Test vector store status
        status = info_advisor.get_vector_store_status()
        print(f"✅ Vector Store Status: {status['available']}")
        
        # Test a simple question
        response = await info_advisor.answer_question("What programming languages are required?")
        print(f"✅ Question answered with confidence: {response.confidence:.2f}")
        print(f"📝 Answer preview: {response.answer[:100]}...")
        
        print("\n🎉 Quick tests passed! Run 'pytest tests/test_info_advisor.py' for full test suite.")
    
    asyncio.run(quick_test()) 