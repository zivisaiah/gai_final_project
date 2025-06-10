# 🔧 API Reference - Multi-Agent Recruitment System

## 📋 Overview

This document provides comprehensive API documentation for all modules, classes, and interfaces in the multi-agent recruitment system.

---

## 🤖 Core Agents

### **CoreAgent** (`app/modules/agents/core_agent.py`)

The main orchestrator agent that manages conversation flow and routes decisions to specialized advisors.

#### **Class: CoreAgent**

```python
class CoreAgent:
    def __init__(self, 
                 openai_api_key: str,
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.7,
                 max_tokens: int = 1000)
```

**Parameters:**
- `openai_api_key`: OpenAI API key for model access
- `model`: GPT model to use for responses
- `temperature`: Response creativity (0.0-1.0)
- `max_tokens`: Maximum response length

#### **Key Methods**

##### `async process_message(message: str, conversation_history: List[Dict]) -> Dict`

Processes user messages and returns agent decisions.

**Parameters:**
- `message`: User input message
- `conversation_history`: List of previous conversation turns

**Returns:**
```python
{
    "decision": "CONTINUE" | "SCHEDULE" | "INFO" | "END",
    "response": str,
    "confidence": float,
    "advisor_used": str | None,
    "metadata": Dict
}
```

**Example:**
```python
result = await core_agent.process_message(
    "I'd like to know about the Python requirements",
    conversation_history
)
# Returns: {"decision": "INFO", "response": "...", "confidence": 0.85}
```

##### `_route_to_advisor(decision: str, message: str, history: List) -> Dict`

Routes messages to appropriate specialized advisors.

**Parameters:**
- `decision`: Routing decision (INFO/SCHEDULE/END)
- `message`: User message to process
- `history`: Conversation context

**Returns:** Advisor response with metadata

---

### **InfoAdvisor** (`app/modules/agents/info_advisor.py`)

RAG-powered agent for answering job-related questions using vector databases.

#### **Class: InfoAdvisor**

```python
class InfoAdvisor:
    def __init__(self,
                 openai_api_key: str,
                 vector_store_type: str = "openai",
                 model: str = "gpt-3.5-turbo")
```

**Parameters:**
- `openai_api_key`: OpenAI API key
- `vector_store_type`: "openai" or "local" vector store
- `model`: GPT model for response generation

#### **Key Methods**

##### `async answer_question(question: str, conversation_context: List = None) -> Dict`

Answers job-related questions using RAG pipeline.

**Parameters:**
- `question`: User question about the job
- `conversation_context`: Previous conversation for context

**Returns:**
```python
{
    "answer": str,
    "confidence": float,
    "sources": List[str],
    "source_documents": List[Dict],
    "question_category": str
}
```

**Example:**
```python
result = await info_advisor.answer_question(
    "What are the Python experience requirements?"
)
# Returns comprehensive answer with source attribution
```

##### `_classify_question(question: str) -> str`

Categorizes questions for better response handling.

**Returns:** Question category (technical, responsibilities, qualifications, etc.)

---

### **SchedulingAdvisor** (`app/modules/agents/scheduling_advisor.py`)

Specialized agent for interview scheduling and time slot management.

#### **Class: SchedulingAdvisor**

```python
class SchedulingAdvisor:
    def __init__(self,
                 openai_api_key: str,
                 sql_manager: SQLManager,
                 model: str = "gpt-3.5-turbo")
```

#### **Key Methods**

##### `async analyze_scheduling_intent(message: str, conversation_history: List) -> Dict`

Analyzes user messages for scheduling intentions.

**Returns:**
```python
{
    "wants_to_schedule": bool,
    "time_preferences": List[str],
    "confidence": float,
    "parsed_times": List[Dict]
}
```

##### `async get_available_slots(preferences: List = None, limit: int = 3) -> List[Dict]`

Retrieves available interview time slots.

**Parameters:**
- `preferences`: User time preferences
- `limit`: Maximum slots to return

**Returns:** List of available time slots with recruiter information

##### `async book_appointment(slot_id: int, candidate_info: Dict) -> Dict`

Books an interview appointment.

**Parameters:**
- `slot_id`: Database ID of the time slot
- `candidate_info`: Candidate details for booking

**Returns:** Booking confirmation with details

---

## 🗄️ Database Layer

### **SQLManager** (`app/modules/database/sql_manager.py`)

Main database interface for SQL operations.

#### **Class: SQLManager**

```python
class SQLManager:
    def __init__(self, database_url: str = None)
```

#### **Key Methods**

##### `get_available_slots(start_date: datetime = None, end_date: datetime = None) -> List[Dict]`

Retrieves available interview time slots.

**Parameters:**
- `start_date`: Filter start date (optional)
- `end_date`: Filter end date (optional)

**Returns:** List of available slots with recruiter information

##### `book_slot(slot_id: int, candidate_name: str, candidate_email: str = None) -> bool`

Books an interview slot for a candidate.

**Returns:** `True` if booking successful, `False` otherwise

##### `create_sample_data() -> None`

Creates sample recruiters and time slots for testing.

---

### **VectorStore** (`app/modules/database/vector_store.py`)

Local ChromaDB vector database interface.

#### **Class: VectorStore**

```python
class VectorStore:
    def __init__(self, 
                 persist_directory: str = "data/vector_db",
                 embedding_function: str = "openai")
```

#### **Key Methods**

##### `add_documents(documents: List[str], metadatas: List[Dict] = None) -> None`

Adds documents to the vector database.

**Parameters:**
- `documents`: List of text documents
- `metadatas`: Associated metadata for each document

##### `search(query: str, n_results: int = 3) -> Dict`

Performs semantic search on stored documents.

**Parameters:**
- `query`: Search query text
- `n_results`: Number of results to return

**Returns:**
```python
{
    "documents": List[str],
    "metadatas": List[Dict],
    "distances": List[float]
}
```

---

### **OpenAIVectorStore** (`app/modules/database/openai_vector_store.py`)

Cloud-based OpenAI Vector Store interface.

#### **Class: OpenAIVectorStore**

```python
class OpenAIVectorStore:
    def __init__(self, 
                 openai_api_key: str,
                 assistant_id: str = None,
                 file_id: str = None)
```

#### **Key Methods**

##### `async search_documents(query: str, max_results: int = 3) -> List[Dict]`

Searches documents using OpenAI's vector search.

**Parameters:**
- `query`: Search query
- `max_results`: Maximum results to return

**Returns:** List of relevant document chunks with metadata

##### `upload_document(file_path: str, purpose: str = "assistants") -> str`

Uploads a document to OpenAI Vector Store.

**Returns:** File ID for the uploaded document

---

## 🎨 UI Components

### **ChatInterface** (`streamlit_app/components/chat_interface.py`)

Main chat interface component for Streamlit.

#### **Functions**

##### `render_chat_interface() -> None`

Renders the main chat interface with message history and input.

##### `handle_user_input(user_input: str) -> None`

Processes user input and updates conversation state.

##### `display_time_slots(slots: List[Dict]) -> int | None`

Displays available time slots as clickable buttons.

**Returns:** Selected slot ID or None

##### `export_conversation() -> str`

Exports conversation history as JSON string.

---

### **AdminPanel** (`streamlit_app/components/admin_panel.py`)

Administrative dashboard component.

#### **Functions**

##### `render_admin_panel() -> None`

Renders the complete admin panel with analytics and monitoring.

##### `show_conversation_analytics() -> None`

Displays conversation statistics and decision distribution.

##### `show_agent_performance() -> None`

Shows performance metrics for each agent.

##### `export_analytics_data() -> Dict`

Exports analytics data for external analysis.

---

## ⚙️ Configuration

### **Settings** (`config/settings.py`)

Application configuration management.

#### **Class: Settings**

```python
class Settings(BaseSettings):
    # API Configuration
    openai_api_key: str
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000
    
    # Database Configuration
    database_url: str = "sqlite:///data/recruitment.db"
    vector_store_type: str = "openai"
    
    # Agent Models
    core_agent_model: str = "gpt-3.5-turbo"
    info_advisor_model: str = "gpt-3.5-turbo"
    scheduling_advisor_model: str = "gpt-3.5-turbo"
    
    # Vector Store Configuration
    openai_assistant_id: str = None
    openai_file_id: str = None
    
    # Application Settings
    debug_mode: bool = False
```

#### **Usage**

```python
from config.settings import Settings

settings = Settings()
api_key = settings.openai_api_key
model = settings.core_agent_model
```

---

## 🧪 Testing Interfaces

### **Test Utilities** (`tests/test_utils.py`)

Common testing utilities and fixtures.

#### **Functions**

##### `create_test_conversation() -> List[Dict]`

Creates a sample conversation for testing.

##### `mock_openai_response(content: str) -> Dict`

Creates mock OpenAI API responses.

##### `assert_agent_response(response: Dict, expected_decision: str) -> None`

Validates agent response format and content.

---

## 📊 Monitoring & Analytics

### **Analytics** (`app/modules/utils/analytics.py`)

System monitoring and analytics utilities.

#### **Class: ConversationAnalytics**

```python
class ConversationAnalytics:
    def __init__(self, sql_manager: SQLManager)
```

#### **Key Methods**

##### `get_decision_distribution(start_date: datetime = None) -> Dict`

Gets distribution of agent decisions over time.

**Returns:**
```python
{
    "CONTINUE": int,
    "SCHEDULE": int,
    "INFO": int,
    "END": int,
    "total": int
}
```

##### `get_performance_metrics() -> Dict`

Calculates system performance metrics.

**Returns:**
```python
{
    "avg_response_time": float,
    "success_rate": float,
    "booking_rate": float,
    "error_rate": float
}
```

---

## 🚀 Deployment

### **Environment Variables**

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `OPENAI_API_KEY` | str | Yes | OpenAI API key |
| `DATABASE_URL` | str | No | Database connection URL |
| `VECTOR_STORE_TYPE` | str | No | "openai" or "local" |
| `OPENAI_ASSISTANT_ID` | str | No | OpenAI Assistant ID |
| `OPENAI_FILE_ID` | str | No | OpenAI Vector Store file ID |
| `DEBUG_MODE` | bool | No | Enable debug logging |

### **Initialization Example**

```python
from app.modules.agents.core_agent import CoreAgent
from app.modules.database.sql_manager import SQLManager
from config.settings import Settings

# Load settings
settings = Settings()

# Initialize database
sql_manager = SQLManager(settings.database_url)

# Initialize core agent
core_agent = CoreAgent(
    openai_api_key=settings.openai_api_key,
    model=settings.core_agent_model,
    temperature=settings.openai_temperature
)

# Process message
result = await core_agent.process_message(
    "Hello, I'm interested in the Python position",
    []
)
```

---

## 🔄 Error Handling

### **Common Exceptions**

#### **AgentError**
Base exception for agent-related errors.

#### **DatabaseError**
Database connection or query errors.

#### **VectorStoreError**
Vector database operation errors.

#### **APIError**
OpenAI API communication errors.

### **Error Response Format**

```python
{
    "error": True,
    "error_type": str,
    "message": str,
    "details": Dict,
    "fallback_response": str | None
}
```

---

## 📈 Performance Considerations

### **Response Time Optimization**
- Use async/await for concurrent operations
- Cache frequently accessed data
- Implement connection pooling for databases
- Optimize vector search queries

### **Resource Management**
- Monitor OpenAI API usage and costs
- Implement rate limiting for API calls
- Use efficient data structures for conversation history
- Clean up unused vector embeddings

### **Scalability**
- Design for horizontal scaling
- Use database connection pooling
- Implement caching strategies
- Monitor memory usage and optimize

---

**🔧 This API reference provides the foundation for extending and customizing the multi-agent recruitment system.** 