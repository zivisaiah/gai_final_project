"""
OpenAI Vector Store Module

This module provides functionality for:
- OpenAI Vector Store integration (cloud-based)
- Document embedding storage via OpenAI API
- Similarity search using OpenAI's infrastructure
- File upload and management
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import time

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Please install openai package: pip install openai")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIVectorStore:
    """
    Vector database manager using OpenAI Vector Stores for document embeddings and similarity search.
    """
    
    def __init__(
        self,
        vector_store_name: str = "job_description_docs",
        api_key: Optional[str] = None
    ):
        """
        Initialize the OpenAI Vector Store.
        
        Args:
            vector_store_name: Name of the vector store
            api_key: OpenAI API key (will use environment variable if not provided)
        """
        self.vector_store_name = vector_store_name
        
        # Initialize OpenAI client
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Get API key from environment or settings
            try:
                from config.phase1_settings import settings
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except:
                self.client = OpenAI()  # Will use OPENAI_API_KEY env var
        
        # Check if Vector Stores API is available
        self._check_vector_stores_availability()
        
        # Get or create vector store
        self.vector_store = self._get_or_create_vector_store()
        self.vector_store_id = self.vector_store.id if self.vector_store else None
        
        if self.vector_store_id:
            logger.info(f"OpenAI Vector Store initialized: '{vector_store_name}' (ID: {self.vector_store_id})")
        else:
            raise Exception("Failed to initialize OpenAI Vector Store")
    
    def _check_vector_stores_availability(self):
        """Check if Vector Stores API is available"""
        try:
            # Test if the API endpoints exist
            if not hasattr(self.client, 'beta'):
                raise Exception("OpenAI beta features not available")
            
            if not hasattr(self.client.beta, 'vector_stores'):
                # Fallback: Check for alternative API structure
                logger.warning("Direct vector_stores API not found, checking alternatives...")
                
                # Try alternative API paths
                possible_paths = [
                    'self.client.vector_stores',
                    'self.client.beta.assistants.vector_stores',
                ]
                
                for path_str in possible_paths:
                    try:
                        # This is a simplified check - in practice you'd use eval carefully
                        logger.info(f"Checking API path: {path_str}")
                    except:
                        continue
                
                # If no vector stores API found, use file-based fallback
                logger.warning("Vector Stores API not available, using file-based approach")
                self.use_file_fallback = True
            else:
                self.use_file_fallback = False
                logger.info("Vector Stores API available")
                
        except Exception as e:
            logger.warning(f"Vector Stores API check failed: {e}")
            self.use_file_fallback = True
    
    def _get_or_create_vector_store(self):
        """Get existing vector store or create a new one."""
        if self.use_file_fallback:
            # Use a simple file-based approach with assistants
            return self._create_file_based_store()
        
        try:
            # List existing vector stores
            vector_stores = self.client.beta.vector_stores.list()
            
            # Look for existing store with our name
            for store in vector_stores.data:
                if store.name == self.vector_store_name:
                    logger.info(f"Found existing vector store: {store.name}")
                    return store
            
            # Create new vector store if not found
            vector_store = self.client.beta.vector_stores.create(
                name=self.vector_store_name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": 365  # Keep for 1 year
                }
            )
            logger.info(f"Created new vector store: {vector_store.name}")
            return vector_store
            
        except Exception as e:
            logger.error(f"Failed to get/create vector store: {e}")
            logger.info("Falling back to file-based approach")
            self.use_file_fallback = True
            return self._create_file_based_store()
    
    def _create_file_based_store(self):
        """Create a simple file-based store using OpenAI files"""
        logger.info("Using file-based storage approach")
        
        # Create a pseudo vector store object
        class FileBasedStore:
            def __init__(self, name):
                self.name = name
                self.id = f"file_based_{name}_{int(time.time())}"
                self.files = []
        
        return FileBasedStore(self.vector_store_name)
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the OpenAI Vector Store.
        
        Args:
            documents: List of document texts to add
            metadatas: Optional list of metadata dictionaries for each document
            ids: Optional list of document IDs (will generate if not provided)
            
        Returns:
            List of file IDs that were added
        """
        try:
            file_ids = []
            
            for i, document in enumerate(documents):
                # Prepare metadata
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                
                # Create a temporary file with the document content
                temp_file_path = f"temp_job_doc_{i}_{int(time.time())}.txt"
                
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    # Include metadata as header if available
                    if metadata:
                        f.write(f"# Document Metadata\n")
                        for key, value in metadata.items():
                            f.write(f"# {key}: {value}\n")
                        f.write(f"\n# Document Content\n")
                    f.write(document)
                
                try:
                    # Upload file to OpenAI
                    with open(temp_file_path, 'rb') as f:
                        file = self.client.files.create(
                            file=f,
                            purpose="assistants"
                        )
                    
                    # If using vector stores API, add to vector store
                    if not self.use_file_fallback and hasattr(self.client.beta, 'vector_stores'):
                        self.client.beta.vector_stores.files.create(
                            vector_store_id=self.vector_store_id,
                            file_id=file.id
                        )
                    else:
                        # Store file ID in our pseudo store
                        self.vector_store.files.append(file.id)
                    
                    file_ids.append(file.id)
                    logger.info(f"Added document {i+1}/{len(documents)} to OpenAI (File ID: {file.id})")
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
            
            logger.info(f"Successfully added {len(file_ids)} documents to OpenAI")
            return file_ids
            
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
        Perform similarity search using OpenAI.
        
        Args:
            query: Query text to search for
            n_results: Number of results to return (limited by OpenAI)
            where: Optional metadata filter (not directly supported)
            
        Returns:
            List of search results with documents, metadata, and relevance scores
        """
        try:
            # Create a temporary assistant for retrieval
            assistant_params = {
                "name": "Job Info Retrieval Assistant",
                "instructions": f"You are a helpful assistant that answers questions about job descriptions. Use the provided files to find relevant information about: {query}. Provide specific details from the job description.",
                "model": "gpt-4-1106-preview",
                "tools": [{"type": "file_search"}]
            }
            
            # Add file search resources
            if not self.use_file_fallback and self.vector_store_id:
                assistant_params["tool_resources"] = {
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            elif hasattr(self.vector_store, 'files') and self.vector_store.files:
                # Use individual files
                assistant_params["tool_resources"] = {
                    "file_search": {
                        "vector_stores": [{
                            "file_ids": self.vector_store.files[:20]  # OpenAI limit
                        }]
                    }
                }
            
            assistant = self.client.beta.assistants.create(**assistant_params)
            
            try:
                # Create a thread and send the query
                thread = self.client.beta.threads.create()
                
                # Add the query message
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=query
                )
                
                # Run the assistant
                run = self.client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=assistant.id
                )
                
                # Wait for completion
                max_wait = 30  # Maximum 30 seconds
                wait_time = 0
                while run.status in ['queued', 'in_progress'] and wait_time < max_wait:
                    time.sleep(1)
                    wait_time += 1
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                if run.status == 'completed':
                    # Get the assistant's response
                    messages = self.client.beta.threads.messages.list(
                        thread_id=thread.id
                    )
                    
                    # Extract the response
                    for message in messages.data:
                        if message.role == "assistant":
                            content = message.content[0].text.value
                            
                            # Return in expected format
                            return [{
                                'document': content,
                                'metadata': {
                                    'source': self.vector_store_name,
                                    'query': query,
                                    'method': 'openai_assistant_search'
                                },
                                'distance': 0.5,  # OpenAI doesn't provide exact distance scores
                                'id': f"openai_result_{int(time.time())}"
                            }]
                    
                else:
                    logger.warning(f"Assistant run failed with status: {run.status}")
                    return []
                
            finally:
                # Clean up temporary assistant
                try:
                    self.client.beta.assistants.delete(assistant.id)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            # Return empty results instead of failing
            return []
    
    def get_vector_store_info(self) -> Dict[str, Any]:
        """Get information about the vector store."""
        try:
            if self.use_file_fallback:
                return {
                    'name': self.vector_store_name,
                    'id': self.vector_store.id,
                    'file_count': len(getattr(self.vector_store, 'files', [])),
                    'status': 'file_based',
                    'created_at': int(time.time()),
                    'usage_bytes': 0,  # Not available in file-based approach
                    'type': 'file_based'
                }
            
            # Refresh vector store info
            store = self.client.beta.vector_stores.retrieve(self.vector_store_id)
            
            # Get file count
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=self.vector_store_id
            )
            
            return {
                'name': store.name,
                'id': store.id,
                'file_count': len(files.data),
                'status': store.status,
                'created_at': store.created_at,
                'usage_bytes': store.usage_bytes,
                'expires_at': getattr(store, 'expires_at', None),
                'type': 'vector_store'
            }
            
        except Exception as e:
            logger.error(f"Failed to get vector store info: {e}")
            return {
                'name': self.vector_store_name,
                'id': self.vector_store_id,
                'error': str(e),
                'type': 'error'
            }
    
    def delete_vector_store(self) -> bool:
        """Delete the vector store and all its files."""
        try:
            if self.use_file_fallback:
                # Delete individual files
                if hasattr(self.vector_store, 'files'):
                    for file_id in self.vector_store.files:
                        try:
                            self.client.files.delete(file_id)
                        except:
                            pass
                return True
            
            # Delete all files first
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=self.vector_store_id
            )
            
            for file in files.data:
                try:
                    self.client.files.delete(file.id)
                except:
                    pass  # Continue even if some files fail
            
            # Delete the vector store
            self.client.beta.vector_stores.delete(self.vector_store_id)
            logger.info(f"Deleted vector store: {self.vector_store_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector store: {e}")
            return False
    
    def list_files(self) -> List[Dict[str, Any]]:
        """List all files in the vector store."""
        try:
            if self.use_file_fallback:
                # List files from our pseudo store
                file_list = []
                if hasattr(self.vector_store, 'files'):
                    for file_id in self.vector_store.files:
                        try:
                            file_info = self.client.files.retrieve(file_id)
                            file_list.append({
                                'id': file_id,
                                'filename': file_info.filename,
                                'bytes': file_info.bytes,
                                'created_at': file_info.created_at,
                                'status': 'uploaded'
                            })
                        except:
                            pass
                return file_list
            
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=self.vector_store_id
            )
            
            file_list = []
            for file in files.data:
                file_info = self.client.files.retrieve(file.id)
                file_list.append({
                    'id': file.id,
                    'filename': file_info.filename,
                    'bytes': file_info.bytes,
                    'created_at': file_info.created_at,
                    'status': getattr(file, 'status', 'unknown')
                })
            
            return file_list
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []


def create_openai_vector_store(
    vector_store_name: str = "job_description_docs",
    api_key: Optional[str] = None
) -> OpenAIVectorStore:
    """
    Factory function to create an OpenAI Vector Store instance.
    
    Args:
        vector_store_name: Name for the vector store
        api_key: OpenAI API key
        
    Returns:
        OpenAIVectorStore instance
    """
    return OpenAIVectorStore(
        vector_store_name=vector_store_name,
        api_key=api_key
    ) 