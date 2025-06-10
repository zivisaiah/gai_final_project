"""
Embeddings Module for PDF Processing and Text Chunking

This module provides functionality for:
- PDF processing pipeline
- Text chunking strategies
- Embedding generation with OpenAI
- Document preprocessing for vector storage
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import tiktoken
from pypdf import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Document processor for handling PDF files and preparing them for vector storage.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Maximum size of each text chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
            encoding_name: Tiktoken encoding name for token counting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding_name = encoding_name
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load tokenizer {encoding_name}: {e}")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Fallback
        
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            reader = PdfReader(str(pdf_path))
            text_content = ""
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text
                        text_content += "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            logger.info(f"Extracted {len(text_content)} characters from {len(reader.pages)} pages")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text content
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page markers (optional - might want to keep for context)
        # text = re.sub(r'--- Page \d+ ---', '', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\-.,;:!?()\[\]{}"\'/]', ' ', text)
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        
        # Clean up spacing around punctuation
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        text = re.sub(r'([,.;:!?])\s+', r'\1 ', text)
        
        return text.strip()
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}")
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def chunk_text_by_tokens(self, text: str) -> List[str]:
        """
        Split text into chunks based on token count with overlap.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        try:
            # Tokenize the entire text
            tokens = self.tokenizer.encode(text)
            
            if len(tokens) <= self.chunk_size:
                return [text]  # Text is small enough, return as single chunk
            
            chunks = []
            start = 0
            
            while start < len(tokens):
                # Calculate end position
                end = min(start + self.chunk_size, len(tokens))
                
                # Extract chunk tokens
                chunk_tokens = tokens[start:end]
                
                # Decode back to text
                chunk_text = self.tokenizer.decode(chunk_tokens)
                chunks.append(chunk_text)
                
                # Move start position with overlap
                if end >= len(tokens):
                    break
                start = end - self.chunk_overlap
            
            logger.info(f"Split text into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk text by tokens: {e}")
            # Fallback to character-based chunking
            return self.chunk_text_by_characters(text)
    
    def chunk_text_by_characters(self, text: str) -> List[str]:
        """
        Fallback method to split text by character count.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        # Rough conversion: 1 token ≈ 4 characters
        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4
        
        if len(text) <= char_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + char_chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
            start = end - char_overlap
        
        logger.info(f"Split text into {len(chunks)} character-based chunks")
        return chunks
    
    def chunk_text_by_sentences(self, text: str, max_chunk_size: Optional[int] = None) -> List[str]:
        """
        Split text into chunks by sentences, respecting token limits.
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum chunk size in tokens (uses self.chunk_size if None)
            
        Returns:
            List of text chunks
        """
        if max_chunk_size is None:
            max_chunk_size = self.chunk_size
        
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed the limit
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if self.count_tokens(potential_chunk) <= max_chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"Split text into {len(chunks)} sentence-based chunks")
        return chunks
    
    def process_pdf_to_chunks(
        self,
        pdf_path: str,
        chunking_strategy: str = "tokens"
    ) -> List[Dict[str, Any]]:
        """
        Process a PDF file and return chunks with metadata.
        
        Args:
            pdf_path: Path to the PDF file
            chunking_strategy: Strategy for chunking ("tokens", "sentences", "characters")
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Extract text from PDF
            raw_text = self.extract_text_from_pdf(pdf_path)
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            
            # Choose chunking strategy
            if chunking_strategy == "tokens":
                chunks = self.chunk_text_by_tokens(cleaned_text)
            elif chunking_strategy == "sentences":
                chunks = self.chunk_text_by_sentences(cleaned_text)
            elif chunking_strategy == "characters":
                chunks = self.chunk_text_by_characters(cleaned_text)
            else:
                raise ValueError(f"Unknown chunking strategy: {chunking_strategy}")
            
            # Create chunk dictionaries with metadata
            chunk_dicts = []
            pdf_name = Path(pdf_path).name
            
            for i, chunk in enumerate(chunks):
                chunk_dict = {
                    "text": chunk,
                    "metadata": {
                        "source": pdf_name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunking_strategy": chunking_strategy,
                        "token_count": self.count_tokens(chunk),
                        "char_count": len(chunk)
                    }
                }
                chunk_dicts.append(chunk_dict)
            
            logger.info(f"Processed PDF '{pdf_name}' into {len(chunk_dicts)} chunks using {chunking_strategy} strategy")
            return chunk_dicts
            
        except Exception as e:
            logger.error(f"Failed to process PDF to chunks: {e}")
            raise


class EmbeddingManager:
    """
    Manager for creating and handling document embeddings.
    """
    
    def __init__(self, vector_store=None):
        """
        Initialize the embedding manager.
        
        Args:
            vector_store: VectorStore instance for storing embeddings
        """
        self.vector_store = vector_store
        self.document_processor = DocumentProcessor()
        
        logger.info("EmbeddingManager initialized")
    
    def process_and_store_pdf(
        self,
        pdf_path: str,
        chunking_strategy: str = "tokens",
        collection_name: Optional[str] = None
    ) -> List[str]:
        """
        Process a PDF file and store its embeddings in the vector store.
        
        Args:
            pdf_path: Path to the PDF file
            chunking_strategy: Strategy for chunking the text
            collection_name: Optional collection name (uses default if None)
            
        Returns:
            List of document IDs that were stored
        """
        try:
            if self.vector_store is None:
                raise ValueError("Vector store not initialized")
            
            # Process PDF to chunks
            chunks = self.document_processor.process_pdf_to_chunks(pdf_path, chunking_strategy)
            
            # Extract texts and metadata
            documents = [chunk["text"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            
            # Store in vector database
            doc_ids = self.vector_store.add_documents(
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(doc_ids)} document chunks from {Path(pdf_path).name}")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to process and store PDF: {e}")
            raise
    
    def search_documents(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using the query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results
        """
        try:
            if self.vector_store is None:
                raise ValueError("Vector store not initialized")
            
            results = self.vector_store.similarity_search(
                query=query,
                n_results=n_results,
                where=filter_metadata
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise


def create_embedding_manager(vector_store=None) -> EmbeddingManager:
    """
    Factory function to create an EmbeddingManager instance.
    
    Args:
        vector_store: VectorStore instance
        
    Returns:
        EmbeddingManager instance
    """
    return EmbeddingManager(vector_store=vector_store)


if __name__ == "__main__":
    # Test the document processor
    print("Testing DocumentProcessor...")
    
    processor = DocumentProcessor(chunk_size=500, chunk_overlap=100)
    
    # Test with sample text
    sample_text = """
    This is a sample document for testing the document processor.
    It contains multiple sentences and paragraphs to test the chunking functionality.
    
    The processor should be able to handle different types of text content.
    It should clean the text and split it into appropriate chunks.
    
    This is another paragraph to make the text longer and test the chunking.
    We want to ensure that the chunks are created properly with the right overlap.
    """
    
    # Test token counting
    token_count = processor.count_tokens(sample_text)
    print(f"Token count: {token_count}")
    
    # Test text cleaning
    cleaned = processor.clean_text(sample_text)
    print(f"Cleaned text length: {len(cleaned)}")
    
    # Test chunking
    chunks = processor.chunk_text_by_tokens(cleaned)
    print(f"Number of chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {len(chunk)} chars, {processor.count_tokens(chunk)} tokens")
        print(f"Preview: {chunk[:100]}...")
        print("---") 