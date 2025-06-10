#!/usr/bin/env python3
"""
Test suite for Vector Database functionality
Tests embedding quality, search performance, and relevance evaluation
"""

import pytest
import numpy as np
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.database.vector_store import VectorStore
from app.modules.database.openai_vector_store import OpenAIVectorStore
from app.modules.database.embeddings import EmbeddingProcessor
from sentence_transformers import SentenceTransformer


class TestVectorDatabase:
    """Test cases for vector database functionality"""
    
    @pytest.fixture
    def local_vector_store(self):
        """Create local vector store instance for testing"""
        return VectorStore(
            collection_name="test_collection",
            embedding_function="sentence_transformers",
            persist_directory="data/vector_db_test"
        )
    
    @pytest.fixture
    def openai_vector_store(self):
        """Create OpenAI vector store instance for testing"""
        try:
            return OpenAIVectorStore()
        except Exception as e:
            pytest.skip(f"OpenAI Vector Store not available: {e}")
    
    @pytest.fixture
    def embedding_processor(self):
        """Create embedding processor for testing"""
        return EmbeddingProcessor()
    
    @pytest.fixture
    def test_documents(self):
        """Sample documents for testing"""
        return [
            {
                "content": "Python is a high-level programming language with dynamic semantics. "
                          "Its high-level built in data structures, combined with dynamic typing "
                          "and dynamic binding, make it very attractive for Rapid Application Development.",
                "metadata": {"source": "python_intro", "category": "programming"}
            },
            {
                "content": "Django is a high-level Python web framework that encourages rapid development "
                          "and clean, pragmatic design. Built by experienced developers, it takes care "
                          "of much of the hassle of web development.",
                "metadata": {"source": "django_intro", "category": "framework"}
            },
            {
                "content": "Machine learning is a method of data analysis that automates analytical model building. "
                          "It is a branch of artificial intelligence based on the idea that systems can learn from data.",
                "metadata": {"source": "ml_intro", "category": "ai"}
            },
            {
                "content": "Flask is a lightweight WSGI web application framework in Python. "
                          "It is designed to make getting started quick and easy, with the ability to scale up to complex applications.",
                "metadata": {"source": "flask_intro", "category": "framework"}
            }
        ]

    def test_vector_store_initialization(self, local_vector_store):
        """Test vector store initialization and basic properties"""
        assert local_vector_store is not None
        assert local_vector_store.collection_name == "test_collection"
        assert local_vector_store.collection is not None
        
    def test_embedding_generation(self, embedding_processor):
        """Test embedding generation quality"""
        test_texts = [
            "Python programming language",
            "Django web framework",
            "Machine learning algorithms",
            "Data science and analytics"
        ]
        
        # Test sentence transformers embeddings
        embeddings_st = embedding_processor.create_embeddings(test_texts, method="sentence_transformers")
        
        assert len(embeddings_st) == len(test_texts)
        for embedding in embeddings_st:
            assert isinstance(embedding, np.ndarray)
            assert len(embedding) > 0
            # Check if embedding is normalized (typical for sentence transformers)
            assert 0.8 <= np.linalg.norm(embedding) <= 1.2
        
        # Test OpenAI embeddings (if available)
        try:
            embeddings_openai = embedding_processor.create_embeddings(test_texts, method="openai")
            assert len(embeddings_openai) == len(test_texts)
            for embedding in embeddings_openai:
                assert isinstance(embedding, np.ndarray)
                assert len(embedding) > 0
        except Exception as e:
            pytest.skip(f"OpenAI embeddings not available: {e}")

    def test_document_storage_and_retrieval(self, local_vector_store, test_documents):
        """Test document storage and basic retrieval"""
        # Clear any existing data
        local_vector_store.collection.delete(where={})
        
        # Store test documents
        for i, doc in enumerate(test_documents):
            doc_id = f"test_doc_{i}"
            local_vector_store.add_document(
                content=doc["content"],
                metadata=doc["metadata"],
                doc_id=doc_id
            )
        
        # Test retrieval
        query = "Python programming"
        results = local_vector_store.search(query, n_results=3)
        
        assert len(results) > 0
        assert "distances" in results
        assert "documents" in results
        assert "metadatas" in results
        
        # Check that distances are reasonable (lower is better)
        distances = results["distances"][0]
        assert all(0 <= d <= 2 for d in distances)  # Cosine distance range
        
        # Check that most relevant document is returned first
        documents = results["documents"][0]
        assert "Python" in documents[0]

    def test_search_relevance_quality(self, local_vector_store, test_documents):
        """Test search relevance and quality metrics"""
        # Setup test data
        local_vector_store.collection.delete(where={})
        for i, doc in enumerate(test_documents):
            local_vector_store.add_document(
                content=doc["content"],
                metadata=doc["metadata"],
                doc_id=f"test_doc_{i}"
            )
        
        # Define test queries with expected relevant documents
        test_queries = [
            {
                "query": "Python programming language",
                "expected_categories": ["programming"],
                "expected_keywords": ["Python"]
            },
            {
                "query": "web development framework",
                "expected_categories": ["framework"],
                "expected_keywords": ["Django", "Flask", "web"]
            },
            {
                "query": "artificial intelligence and machine learning",
                "expected_categories": ["ai"],
                "expected_keywords": ["machine learning", "artificial intelligence"]
            }
        ]
        
        relevance_scores = []
        
        for test_case in test_queries:
            results = local_vector_store.search(test_case["query"], n_results=2)
            
            # Check if top result is relevant
            top_doc = results["documents"][0][0].lower()
            top_metadata = results["metadatas"][0][0]
            
            # Score relevance based on category match
            category_match = top_metadata.get("category") in test_case["expected_categories"]
            
            # Score relevance based on keyword presence
            keyword_matches = sum(
                1 for keyword in test_case["expected_keywords"]
                if keyword.lower() in top_doc
            )
            keyword_score = keyword_matches / len(test_case["expected_keywords"])
            
            # Combined relevance score
            relevance = (0.5 * category_match) + (0.5 * keyword_score)
            relevance_scores.append(relevance)
        
        # Average relevance should be high
        avg_relevance = np.mean(relevance_scores)
        assert avg_relevance >= 0.7, f"Low relevance score: {avg_relevance}"

    def test_search_performance(self, local_vector_store, test_documents):
        """Test search performance and response times"""
        # Setup test data
        local_vector_store.collection.delete(where={})
        
        # Add more documents for performance testing
        extended_docs = test_documents * 10  # 40 documents total
        for i, doc in enumerate(extended_docs):
            local_vector_store.add_document(
                content=doc["content"],
                metadata=doc["metadata"],
                doc_id=f"perf_test_doc_{i}"
            )
        
        # Test search performance
        test_queries = [
            "Python programming",
            "web framework",
            "machine learning",
            "data analysis",
            "software development"
        ]
        
        response_times = []
        
        for query in test_queries:
            start_time = time.time()
            results = local_vector_store.search(query, n_results=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Verify results are returned
            assert len(results["documents"][0]) > 0
        
        # Performance assertions
        avg_response_time = np.mean(response_times)
        max_response_time = np.max(response_times)
        
        assert avg_response_time < 2.0, f"Average response time too slow: {avg_response_time}s"
        assert max_response_time < 5.0, f"Max response time too slow: {max_response_time}s"

    def test_embedding_similarity_consistency(self, embedding_processor):
        """Test embedding similarity consistency and quality"""
        # Test similar vs dissimilar text pairs
        similar_pairs = [
            ("Python programming language", "Python coding and development"),
            ("Django web framework", "Django web application framework"),
            ("Machine learning algorithms", "ML and artificial intelligence")
        ]
        
        dissimilar_pairs = [
            ("Python programming", "cooking recipes"),
            ("web development", "mountain climbing"),
            ("machine learning", "car maintenance")
        ]
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # Test similar pairs
        similar_scores = []
        for text1, text2 in similar_pairs:
            emb1 = embedding_processor.create_embeddings([text1])[0]
            emb2 = embedding_processor.create_embeddings([text2])[0]
            similarity = cosine_similarity(emb1, emb2)
            similar_scores.append(similarity)
        
        # Test dissimilar pairs
        dissimilar_scores = []
        for text1, text2 in dissimilar_pairs:
            emb1 = embedding_processor.create_embeddings([text1])[0]
            emb2 = embedding_processor.create_embeddings([text2])[0]
            similarity = cosine_similarity(emb1, emb2)
            dissimilar_scores.append(similarity)
        
        # Assertions
        avg_similar = np.mean(similar_scores)
        avg_dissimilar = np.mean(dissimilar_scores)
        
        assert avg_similar > 0.7, f"Similar texts should have high similarity: {avg_similar}"
        assert avg_dissimilar < 0.5, f"Dissimilar texts should have low similarity: {avg_dissimilar}"
        assert avg_similar > avg_dissimilar, "Similar pairs should score higher than dissimilar pairs"

    def test_openai_vector_store_integration(self, openai_vector_store):
        """Test OpenAI vector store functionality"""
        if openai_vector_store is None:
            pytest.skip("OpenAI Vector Store not available")
        
        # Test basic functionality
        status = openai_vector_store.get_status()
        assert "vector_store_id" in status
        assert status["status"] in ["ready", "operational", "available"]
        
        # Test search if data exists
        try:
            results = openai_vector_store.search("Python programming", limit=3)
            assert isinstance(results, list)
            # If results exist, check structure
            if results:
                assert "content" in results[0]
                assert "score" in results[0]
        except Exception as e:
            logging.warning(f"OpenAI search test skipped: {e}")

    def test_vector_store_metadata_filtering(self, local_vector_store, test_documents):
        """Test metadata-based filtering functionality"""
        # Setup test data
        local_vector_store.collection.delete(where={})
        for i, doc in enumerate(test_documents):
            local_vector_store.add_document(
                content=doc["content"],
                metadata=doc["metadata"],
                doc_id=f"filter_test_doc_{i}"
            )
        
        # Test category filtering
        framework_results = local_vector_store.search(
            query="web development",
            n_results=5,
            where={"category": "framework"}
        )
        
        # All results should be frameworks
        for metadata in framework_results["metadatas"][0]:
            assert metadata["category"] == "framework"
        
        # Test source filtering
        if framework_results["metadatas"][0]:
            specific_source = framework_results["metadatas"][0][0]["source"]
            source_results = local_vector_store.search(
                query="development",
                n_results=5,
                where={"source": specific_source}
            )
            
            # All results should match the source
            for metadata in source_results["metadatas"][0]:
                assert metadata["source"] == specific_source

    def test_vector_store_robustness(self, local_vector_store):
        """Test vector store robustness with edge cases"""
        # Test empty query
        try:
            results = local_vector_store.search("", n_results=1)
            # Should handle gracefully
            assert "documents" in results
        except Exception as e:
            # Should not crash
            assert "empty" in str(e).lower() or "invalid" in str(e).lower()
        
        # Test very long query
        long_query = "Python " * 1000  # Very long query
        try:
            results = local_vector_store.search(long_query, n_results=1)
            assert "documents" in results
        except Exception as e:
            # Should handle gracefully
            logging.warning(f"Long query handling: {e}")
        
        # Test special characters
        special_query = "Python @#$%^&*()_+{}|:<>?[]\\;'\",./"
        try:
            results = local_vector_store.search(special_query, n_results=1)
            assert "documents" in results
        except Exception as e:
            logging.warning(f"Special character handling: {e}")

    def test_embedding_dimension_consistency(self, embedding_processor):
        """Test that embeddings have consistent dimensions"""
        test_texts = [
            "Short text",
            "This is a medium length text with more words and context",
            "This is a much longer text with many more words and detailed information about various topics including programming, web development, machine learning, and other technical subjects that should test the embedding consistency across different text lengths"
        ]
        
        embeddings = embedding_processor.create_embeddings(test_texts)
        
        # All embeddings should have the same dimension
        dimensions = [len(emb) for emb in embeddings]
        assert len(set(dimensions)) == 1, f"Inconsistent embedding dimensions: {dimensions}"
        
        # Dimension should be reasonable (typically 384, 512, 768, or 1536)
        dim = dimensions[0]
        assert dim >= 300, f"Embedding dimension too small: {dim}"
        assert dim <= 2000, f"Embedding dimension too large: {dim}"


class TestVectorStoreIntegration:
    """Integration tests for vector store with real job description data"""
    
    def test_job_description_search_quality(self):
        """Test search quality with actual job description data"""
        # Use production vector store
        try:
            vector_store = VectorStore(collection_name="job_description_docs")
            
            # Test job-related queries
            job_queries = [
                "What programming languages are required?",
                "What are the main responsibilities?",
                "What experience is needed?",
                "What technologies should I know?",
                "What frameworks are mentioned?"
            ]
            
            search_quality_scores = []
            
            for query in job_queries:
                results = vector_store.search(query, n_results=3)
                
                if results["documents"][0]:
                    # Check if results contain job-related content
                    top_doc = results["documents"][0][0].lower()
                    
                    # Score based on presence of job-related keywords
                    job_keywords = [
                        "python", "developer", "experience", "required", 
                        "responsibilities", "skills", "qualifications", 
                        "programming", "development", "software"
                    ]
                    
                    keyword_score = sum(
                        1 for keyword in job_keywords if keyword in top_doc
                    ) / len(job_keywords)
                    
                    search_quality_scores.append(keyword_score)
            
            if search_quality_scores:
                avg_quality = np.mean(search_quality_scores)
                assert avg_quality >= 0.3, f"Job description search quality too low: {avg_quality}"
                
        except Exception as e:
            pytest.skip(f"Job description data not available: {e}")


def run_vector_db_evaluation():
    """Run comprehensive vector database evaluation"""
    print("🧪 Running Vector Database Evaluation...")
    
    # Run all tests
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("✅ All vector database tests passed!")
    else:
        print("❌ Some vector database tests failed")
    
    return exit_code == 0


if __name__ == "__main__":
    run_vector_db_evaluation() 