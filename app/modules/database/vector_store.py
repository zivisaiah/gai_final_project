"""
Vector Database Module for Chroma Integration

This module provides functionality for:
- Chroma database initialization
- Document embedding storage
- Similarity search functions
- Vector database management
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector database manager using ChromaDB for document embeddings and similarity search.
    """
    
    def __init__(
        self,
        collection_name: str = "job_description_docs",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[str] = "openai"
    ):
        """
        Initialize the vector store with ChromaDB.
        
        Args:
            collection_name: Name of the collection to store documents
            persist_directory: Directory to persist the database (default: data/vector_db)
            embedding_function: Type of embedding function to use ("openai" or "sentence_transformers")
        """
        self.collection_name = collection_name
        
        # Set up persist directory
        if persist_directory is None:
            project_root = Path(__file__).parent.parent.parent.parent
            self.persist_directory = str(project_root / "data" / "vector_db")
        else:
            self.persist_directory = persist_directory
            
        # Create directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = self._initialize_client()
        
        # Set up embedding function
        self.embedding_function = self._setup_embedding_function(embedding_function)
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"VectorStore initialized with collection '{collection_name}' at {self.persist_directory}")
    
    def _initialize_client(self) -> chromadb.Client:
        """Initialize ChromaDB client with persistence."""
        try:
            client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info("ChromaDB client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def _setup_embedding_function(self, embedding_type: str):
        """Set up the embedding function based on the specified type."""
        try:
            if embedding_type == "openai":
                # Use OpenAI embeddings
                from config.phase1_settings import settings
                return embedding_functions.OpenAIEmbeddingFunction(
                    api_key=settings.OPENAI_API_KEY,
                    model_name="text-embedding-ada-002"
                )
            elif embedding_type == "sentence_transformers":
                # Use sentence transformers (local, no API calls)
                return embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            else:
                raise ValueError(f"Unsupported embedding type: {embedding_type}")
                
        except Exception as e:
            logger.warning(f"Failed to set up {embedding_type} embeddings: {e}")
            # Fallback to sentence transformers
            logger.info("Falling back to sentence transformers embeddings")
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
    
    def _get_or_create_collection(self):
        """Get existing collection or create a new one."""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection '{self.collection_name}'")
            return collection
        except Exception as e:
            # Check if it's a "collection not found" error
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                # Create new collection if it doesn't exist
                try:
                    collection = self.client.create_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"description": "Job description documents and related content"}
                    )
                    logger.info(f"Created new collection '{self.collection_name}'")
                    return collection
                except Exception as create_error:
                    # If creation fails, try to get it again (race condition)
                    if "already exists" in str(create_error).lower():
                        collection = self.client.get_collection(
                            name=self.collection_name,
                            embedding_function=self.embedding_function
                        )
                        logger.info(f"Retrieved existing collection '{self.collection_name}' after creation conflict")
                        return collection
                    else:
                        raise create_error
            else:
                raise e
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts to add
            metadatas: Optional list of metadata dictionaries for each document
            ids: Optional list of document IDs (will generate UUIDs if not provided)
            
        Returns:
            List of document IDs that were added
        """
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Ensure metadatas is provided
            if metadatas is None:
                metadatas = [{"source": "unknown"} for _ in documents]
            
            # Add documents to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def similarity_search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Query text to search for
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of search results with documents, metadata, and distances
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}
    
    def delete_collection(self) -> bool:
        """Delete the current collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def reset_collection(self) -> bool:
        """Reset (clear) the current collection."""
        try:
            # Delete and recreate collection
            self.delete_collection()
            self.collection = self._get_or_create_collection()
            logger.info(f"Reset collection '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False
    
    def update_document(
        self,
        document_id: str,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing document in the vector store.
        
        Args:
            document_id: ID of the document to update
            document: New document text
            metadata: New metadata for the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.update(
                ids=[document_id],
                documents=[document],
                metadatas=[metadata] if metadata else None
            )
            logger.info(f"Updated document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            return False
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False


def create_vector_store(
    collection_name: str = "job_description_docs",
    embedding_type: str = "openai"
) -> VectorStore:
    """
    Factory function to create a VectorStore instance.
    
    Args:
        collection_name: Name of the collection
        embedding_type: Type of embedding function ("openai" or "sentence_transformers")
        
    Returns:
        VectorStore instance
    """
    return VectorStore(
        collection_name=collection_name,
        embedding_function=embedding_type
    )


if __name__ == "__main__":
    # Test the vector store
    print("Testing VectorStore...")
    
    # Create vector store
    vs = create_vector_store()
    
    # Test adding documents
    test_docs = [
        "Python is a high-level programming language.",
        "Machine learning requires understanding of algorithms and data structures.",
        "Web development involves frontend and backend technologies."
    ]
    
    test_metadata = [
        {"source": "python_info", "category": "programming"},
        {"source": "ml_info", "category": "ai"},
        {"source": "web_info", "category": "development"}
    ]
    
    # Add test documents
    doc_ids = vs.add_documents(test_docs, test_metadata)
    print(f"Added documents with IDs: {doc_ids}")
    
    # Test similarity search
    results = vs.similarity_search("What is Python programming?", n_results=2)
    print(f"Search results: {results}")
    
    # Get collection info
    info = vs.get_collection_info()
    print(f"Collection info: {info}") 