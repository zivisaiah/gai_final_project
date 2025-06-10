"""
Vector Database Setup Script

This script processes the Python Developer Job Description PDF and stores it in the vector database.
It's designed to be run once to set up the vector database for the Info Advisor.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from .vector_store import create_vector_store
from .embeddings import create_embedding_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_vector_database(
    pdf_path: Optional[str] = None,
    collection_name: str = "job_description_docs",
    embedding_type: str = "openai",
    chunking_strategy: str = "tokens",
    reset_existing: bool = False
) -> bool:
    """
    Set up the vector database with the job description PDF.
    
    Args:
        pdf_path: Path to the PDF file (defaults to resources/Python Developer Job Description.pdf)
        collection_name: Name of the vector database collection
        embedding_type: Type of embeddings to use ("openai" or "sentence_transformers")
        chunking_strategy: Strategy for text chunking ("tokens", "sentences", "characters")
        reset_existing: Whether to reset existing collection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Set default PDF path if not provided
        if pdf_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            pdf_path = project_root / "resources" / "Python Developer Job Description.pdf"
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return False
        
        logger.info(f"Setting up vector database with PDF: {pdf_path}")
        logger.info(f"Collection: {collection_name}, Embedding: {embedding_type}, Chunking: {chunking_strategy}")
        
        # Create vector store
        vector_store = create_vector_store(
            collection_name=collection_name,
            embedding_type=embedding_type
        )
        
        # Check if collection already has documents
        collection_info = vector_store.get_collection_info()
        if collection_info.get("count", 0) > 0:
            if reset_existing:
                logger.info(f"Resetting existing collection with {collection_info['count']} documents")
                vector_store.reset_collection()
            else:
                logger.info(f"Collection already contains {collection_info['count']} documents")
                logger.info("Use reset_existing=True to reset the collection")
                return True
        
        # Create embedding manager
        embedding_manager = create_embedding_manager(vector_store=vector_store)
        
        # Process and store the PDF
        logger.info("Processing PDF and creating embeddings...")
        doc_ids = embedding_manager.process_and_store_pdf(
            pdf_path=str(pdf_path),
            chunking_strategy=chunking_strategy
        )
        
        # Verify the setup
        final_info = vector_store.get_collection_info()
        logger.info(f"✅ Vector database setup complete!")
        logger.info(f"   Collection: {final_info['name']}")
        logger.info(f"   Documents: {final_info['count']}")
        logger.info(f"   Location: {final_info['persist_directory']}")
        
        # Test search functionality
        logger.info("Testing search functionality...")
        test_results = embedding_manager.search_documents(
            query="What are the Python requirements for this position?",
            n_results=3
        )
        
        if test_results:
            logger.info(f"✅ Search test successful - found {len(test_results)} relevant documents")
            for i, result in enumerate(test_results[:2]):  # Show first 2 results
                logger.info(f"   Result {i+1}: {result['document'][:100]}...")
        else:
            logger.warning("⚠️ Search test returned no results")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up vector database: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_database(collection_name: str = "job_description_docs") -> bool:
    """
    Test the vector database functionality.
    
    Args:
        collection_name: Name of the collection to test
        
    Returns:
        True if tests pass, False otherwise
    """
    try:
        logger.info("Testing vector database functionality...")
        
        # Create vector store
        vector_store = create_vector_store(collection_name=collection_name)
        
        # Get collection info
        info = vector_store.get_collection_info()
        logger.info(f"Collection info: {info}")
        
        if info.get("count", 0) == 0:
            logger.warning("Collection is empty - run setup_vector_database() first")
            return False
        
        # Create embedding manager
        embedding_manager = create_embedding_manager(vector_store=vector_store)
        
        # Test various queries
        test_queries = [
            "What programming languages are required?",
            "What are the responsibilities of this role?",
            "What experience is needed for this position?",
            "What technologies should I know?",
            "What are the qualifications required?"
        ]
        
        all_tests_passed = True
        
        for query in test_queries:
            logger.info(f"Testing query: '{query}'")
            results = embedding_manager.search_documents(query, n_results=2)
            
            if results:
                logger.info(f"  ✅ Found {len(results)} results")
                for i, result in enumerate(results):
                    distance = result.get('distance', 'N/A')
                    logger.info(f"    {i+1}. Distance: {distance}, Preview: {result['document'][:80]}...")
            else:
                logger.warning(f"  ⚠️ No results found for query")
                all_tests_passed = False
            
            print()  # Add spacing
        
        if all_tests_passed:
            logger.info("✅ All vector database tests passed!")
        else:
            logger.warning("⚠️ Some tests failed")
        
        return all_tests_passed
        
    except Exception as e:
        logger.error(f"Vector database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_vector_database_status(collection_name: str = "job_description_docs") -> dict:
    """
    Get the current status of the vector database.
    
    Args:
        collection_name: Name of the collection to check
        
    Returns:
        Dictionary with status information
    """
    try:
        vector_store = create_vector_store(collection_name=collection_name)
        info = vector_store.get_collection_info()
        
        status = {
            "initialized": True,
            "collection_name": info.get("name", "unknown"),
            "document_count": info.get("count", 0),
            "persist_directory": info.get("persist_directory", "unknown"),
            "ready": info.get("count", 0) > 0
        }
        
        return status
        
    except Exception as e:
        return {
            "initialized": False,
            "error": str(e),
            "ready": False
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up vector database for Info Advisor")
    parser.add_argument("--pdf-path", help="Path to PDF file")
    parser.add_argument("--collection", default="job_description_docs", help="Collection name")
    parser.add_argument("--embedding", choices=["openai", "sentence_transformers"], 
                       default="openai", help="Embedding type")
    parser.add_argument("--chunking", choices=["tokens", "sentences", "characters"],
                       default="tokens", help="Chunking strategy")
    parser.add_argument("--reset", action="store_true", help="Reset existing collection")
    parser.add_argument("--test", action="store_true", help="Test vector database")
    parser.add_argument("--status", action="store_true", help="Show database status")
    
    args = parser.parse_args()
    
    if args.status:
        status = get_vector_database_status(args.collection)
        print(f"Vector Database Status: {status}")
    elif args.test:
        success = test_vector_database(args.collection)
        exit(0 if success else 1)
    else:
        success = setup_vector_database(
            pdf_path=args.pdf_path,
            collection_name=args.collection,
            embedding_type=args.embedding,
            chunking_strategy=args.chunking,
            reset_existing=args.reset
        )
        exit(0 if success else 1) 