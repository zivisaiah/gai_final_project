from typing import Dict, List, Optional, Tuple, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fallback for older langchain versions
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        from langchain.chat_models import ChatOpenAI

try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
except ImportError:
    # Fallback for older langchain versions
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.schema import SystemMessage, HumanMessage, AIMessage

from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool
from pydantic import BaseModel
import json
import logging

from ..prompts.info_prompts import (
    INFO_SYSTEM_PROMPT,
    INFO_RAG_TEMPLATE,
    INFO_NO_CONTEXT_TEMPLATE,
    classify_question,
    get_search_keywords,
    format_response
)
from ..database.vector_store import VectorStore


class InfoResponse(BaseModel):
    """Model for info advisor's response"""
    answer: str
    confidence: float
    sources_used: List[str]
    question_type: str
    has_context: bool


class InfoAdvisor:
    """Agent responsible for answering job-related questions using RAG"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.3,
        memory: Optional[ConversationBufferMemory] = None,
        vector_store: Optional[any] = None,
        vector_store_type: str = "local"  # "local" or "openai"
    ):
        """Initialize the Info Advisor agent
        
        Args:
            model_name: The OpenAI model to use
            temperature: Model temperature (lower for more consistent answers)
            memory: Optional conversation memory
            vector_store: Pre-initialized vector store (local VectorStore or OpenAIVectorStore)
            vector_store_type: Type of vector store to use ("local" or "openai")
        """
        # Import settings here to avoid circular imports
        from config.phase1_settings import settings
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Use configuration-based model selection if not explicitly provided
        if model_name is None:
            model_name = settings.get_core_agent_model()
            
        self.model_name = model_name
        self.vector_store_type = vector_store_type
        
        # Initialize ChatOpenAI with conservative temperature for factual responses
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature
        )
        
        self.memory = memory or ConversationBufferMemory(
            memory_key="chat_history",
            input_key="input",
            return_messages=True
        )
        
        # Initialize vector store for document retrieval
        self.vector_store = vector_store or self._initialize_vector_store()
        
        # Store conversation history for tool access
        self.current_conversation_history = []
        
        # Initialize tools for information retrieval
        self.tools = self._create_tools()
        
        # Initialize the agent
        self._initialize_agent()

    def _initialize_vector_store(self):
        """Initialize vector store based on type"""
        try:
            if self.vector_store_type == "openai":
                # Import OpenAI Vector Store
                from ..database.openai_vector_store import OpenAIVectorStore
                
                self.logger.info("Initializing OpenAI Vector Store...")
                return OpenAIVectorStore(
                    vector_store_name="job_description_docs"
                )
            else:
                # Default to local ChromaDB
                self.logger.info("Initializing local ChromaDB Vector Store...")
                return VectorStore(
                    collection_name="job_description_docs",
                    embedding_function="sentence_transformers"  # Use local embeddings for reliability
                )
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.vector_store_type} vector store: {e}")
            # Return None if vector store initialization fails
            return None

    def _create_tools(self) -> List[Tool]:
        """Create tools for information retrieval and processing"""
        return [
            Tool(
                name="search_job_documents",
                func=self._search_documents,
                description="Search job description documents for relevant information"
            ),
            Tool(
                name="classify_question_type",
                func=self._classify_question_wrapper,
                description="Classify the type of question being asked"
            ),
            Tool(
                name="extract_search_keywords",
                func=self._extract_keywords_wrapper,
                description="Extract relevant keywords for document search"
            )
        ]

    def _search_documents(self, query: str) -> Dict[str, Any]:
        """Search documents in vector store for relevant information"""
        if not self.vector_store:
            return {
                "context": "",
                "sources": [],
                "found_results": False,
                "error": "Vector store not available"
            }
        
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search(
                query=query,
                n_results=3,  # Get top 3 most relevant results
                where=None
            )
            
            if not results:
                return {
                    "context": "",
                    "sources": [],
                    "found_results": False,
                    "message": "No relevant information found"
                }
            
            # Extract context and sources
            context_parts = []
            sources = []
            
            for result in results:
                # Handle single document result format
                if result.get('document'):
                    context_parts.append(result['document'])
                # Handle batch documents format (if needed)
                elif result.get('documents'):
                    context_parts.extend(result['documents'])
                
                # Extract source from metadata
                if result.get('metadata') and 'source' in result['metadata']:
                    sources.append(result['metadata']['source'])
                elif result.get('metadatas'):
                    for metadata in result['metadatas']:
                        if metadata and 'source' in metadata:
                            sources.append(metadata['source'])
            
            # Combine context
            context = "\n\n".join(context_parts) if context_parts else ""
            
            return {
                "context": context,
                "sources": list(set(sources)),  # Remove duplicates
                "found_results": len(context_parts) > 0,
                "num_results": len(context_parts)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return {
                "context": "",
                "sources": [],
                "found_results": False,
                "error": str(e)
            }

    def _classify_question_wrapper(self, question: str) -> str:
        """Wrapper for question classification tool"""
        return classify_question(question)

    def _extract_keywords_wrapper(self, question: str) -> List[str]:
        """Wrapper for keyword extraction tool"""
        return get_search_keywords(question)

    def _initialize_agent(self):
        """Initialize the LangChain agent"""
        try:
            # Create the agent
            self.agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=INFO_RAG_TEMPLATE
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize info agent: {e}")
            raise

    async def answer_question(
        self,
        question: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> InfoResponse:
        """Answer a job-related question using RAG"""
        try:
            # Store conversation history for tool access
            self.current_conversation_history = conversation_history or []
            
            # Classify question type
            question_type = classify_question(question)
            
            # Search for relevant context
            search_results = self._search_documents(question)
            context = search_results.get("context", "")
            sources = search_results.get("sources", [])
            has_context = search_results.get("found_results", False)
            
            # Choose appropriate template based on context availability
            if has_context and context.strip():
                # Use RAG template with context
                prompt_input = {
                    "context": context,
                    "question": question,
                    "input": question,
                    "chat_history": self._format_chat_history(conversation_history)
                }
                response = await self.agent_executor.ainvoke(prompt_input)
                confidence = 0.8  # High confidence when we have context
                
            else:
                # Use no-context template
                no_context_prompt = INFO_NO_CONTEXT_TEMPLATE.format(question=question)
                response = await self.llm.ainvoke([HumanMessage(content=no_context_prompt)])
                confidence = 0.3  # Lower confidence without context
                
                # Extract text from response
                if hasattr(response, 'content'):
                    response = {"output": response.content}
                else:
                    response = {"output": str(response)}
            
            # Extract the answer from response
            answer = response.get("output", str(response))
            
            return InfoResponse(
                answer=answer,
                confidence=confidence,
                sources_used=sources,
                question_type=question_type,
                has_context=has_context
            )
            
        except Exception as e:
            self.logger.error(f"Error answering question: {e}")
            
            # Return error response
            return InfoResponse(
                answer=f"I apologize, but I encountered an error while trying to answer your question. Please try asking again or rephrase your question.",
                confidence=0.0,
                sources_used=[],
                question_type="error",
                has_context=False
            )

    def _format_chat_history(self, conversation_history: List[Dict[str, str]]) -> List:
        """Format conversation history for prompt"""
        if not conversation_history:
            return []
        
        formatted_history = []
        for msg in conversation_history[-5:]:  # Keep last 5 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'user':
                formatted_history.append(HumanMessage(content=content))
            elif role == 'assistant':
                formatted_history.append(AIMessage(content=content))
        
        return formatted_history

    def get_vector_store_status(self) -> Dict[str, Any]:
        """Get information about the vector store status"""
        if not self.vector_store:
            return {
                "available": False,
                "error": "Vector store not initialized",
                "type": self.vector_store_type
            }
        
        try:
            if self.vector_store_type == "openai":
                # OpenAI Vector Store status
                info = self.vector_store.get_vector_store_info()
                return {
                    "available": True,
                    "type": "openai",
                    "vector_store_name": info.get("name", "Unknown"),
                    "vector_store_id": info.get("id", "Unknown"),
                    "file_count": info.get("file_count", 0),
                    "status": info.get("status", "Unknown"),
                    "usage_bytes": info.get("usage_bytes", 0)
                }
            else:
                # Local ChromaDB status
                info = self.vector_store.get_collection_info()
                return {
                    "available": True,
                    "type": "local",
                    "collection_name": self.vector_store.collection_name,
                    "document_count": info.get("count", 0),
                    "status": "operational"
                }
        except Exception as e:
            return {
                "available": False,
                "type": self.vector_store_type,
                "error": str(e)
            }

    def test_retrieval(self, test_queries: List[str] = None) -> Dict[str, Any]:
        """Test the document retrieval functionality"""
        if test_queries is None:
            test_queries = [
                "What programming languages are required?",
                "What are the main responsibilities?",
                "What experience is needed?",
                "What technologies should I know?"
            ]
        
        results = {}
        for query in test_queries:
            search_result = self._search_documents(query)
            results[query] = {
                "found_results": search_result.get("found_results", False),
                "num_results": search_result.get("num_results", 0),
                "context_length": len(search_result.get("context", "")),
                "sources": search_result.get("sources", [])
            }
        
        return {
            "test_queries": test_queries,
            "results": results,
            "vector_store_status": self.get_vector_store_status()
        } 