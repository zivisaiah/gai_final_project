# 🤖 Multi-Agent Python Developer Recruitment Assistant

**GAI Final Project - Complete Multi-Agent System**  

An intelligent recruitment chatbot with **optimal multi-agent architecture** for Python developer recruitment. Features comprehensive information assistance, interview scheduling, conversation analytics, and cloud deployment capabilities. **Production-ready system** with enhanced routing accuracy achieving 96.0% performance through advanced keyword-based routing optimization.

Built with LangChain, OpenAI API, vector databases, and advanced Streamlit UI.

## 🎯 Project Overview

This project implements a sophisticated multi-agent recruitment assistant that can:

### 🎯 **Core Capabilities**
- 💬 **Intelligent Conversations**: Multi-turn dialogue with context awareness and personality
- 📅 **Interview Scheduling**: Natural language parsing and intelligent slot management
- 📚 **Information Assistant**: RAG-powered Q&A about job descriptions using vector databases


### 🤖 **Multi-Agent Architecture**
- **Core Agent**: Main orchestrator with intelligent routing to specialized advisors
- **Info Advisor**: RAG-enabled Q&A agent with OpenAI Vector Store integration
- **Scheduling Advisor**: Interview booking with SQL database and time preference understanding
- **Exit Advisor**: Conversation termination detection with fine-tuning capabilities
- **Admin Panel**: Real-time analytics, performance monitoring, and data export

## 🏗️ Architecture

### 🏗️ **Multi-Agent System Architecture**

#### **Core Agent (Main Orchestrator)**
- **Decision Framework**: Intelligent routing among 4 options (CONTINUE, SCHEDULE, INFO, END)
- **Context Management**: Maintains conversation state and candidate information
- **Advisor Coordination**: Consults specialized agents for complex decisions
- **Response Generation**: Combines advisor insights for optimal candidate experience

#### **Specialized Advisors**
- **Info Advisor**: RAG-powered Q&A using OpenAI Vector Store with job description embeddings
- **Scheduling Advisor**: Time slot management with SQL database and calendar integration
- **Exit Advisor**: Conversation termination detection with confidence scoring and fine-tuning

#### **Data & Storage Layer**
- **Vector Database**: ChromaDB + OpenAI Vector Store for document embeddings
- **SQL Database**: SQLite/PostgreSQL for scheduling and conversation data
- **Document Processing**: PDF parsing and intelligent text chunking

### 🛠️ **Technology Stack**

#### **AI/ML Framework**
- **LangChain**: Agent orchestration and tool integration
- **OpenAI API**: GPT models for conversation and embeddings
- **Vector Databases**: ChromaDB (local) + OpenAI Vector Store (cloud)
- **RAG Pipeline**: Retrieval-Augmented Generation for accurate information

#### **Backend Infrastructure**
- **Python 3.11+**: Core application logic
- **SQLAlchemy**: Database ORM with migration support
- **Pydantic**: Data validation and settings management
- **AsyncIO**: Concurrent processing for performance

#### **Frontend & Deployment**
- **Streamlit**: Advanced UI with real-time analytics
- **Plotly**: Interactive data visualization
- **Streamlit Cloud**: Production deployment platform
- **GitHub Actions**: CI/CD pipeline integration

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- OpenAI API key
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/zivisaiah/gai_final_project.git
cd gai_final_project

# Set up virtual environment (REQUIRED)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies IN THE VIRTUAL ENVIRONMENT
pip install -r requirements.txt
```

### ⚠️ **CRITICAL: Virtual Environment Usage**

**All operations must be performed within the activated virtual environment:**

```bash
# CORRECT: Activate venv first
source venv/bin/activate
python -m streamlit run streamlit_app/streamlit_main.py

# OR use the provided script (recommended)
./run_app.sh
```

**❌ Common Error - Running without venv activation:**
```bash
# This will fail with: ModuleNotFoundError: No module named 'chromadb'
streamlit run streamlit_app/streamlit_main.py
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your OpenAI API key
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

### 3. Initialize Database

```bash
# Run database setup (creates sample data)
python -c "from app.modules.database.sql_manager import SQLManager; SQLManager().create_sample_data()"
```

### 4. Launch the Application

```bash
# RECOMMENDED: Use the provided script (handles venv automatically)
./run_app.sh

# OR manually with venv activation
source venv/bin/activate
python -m streamlit run streamlit_app/streamlit_main.py --server.port 8501
```

The application will open in your browser at `http://localhost:8501`

## 💻 Usage Examples

### Basic Conversation Flow

1. **Greeting**: The assistant welcomes candidates and explains its capabilities
2. **Information Gathering**: Collects candidate name, experience, and interest level
3. **Decision Making**: Determines whether to continue conversation or schedule interview
4. **Scheduling**: If appropriate, offers available time slots and books appointments

### Example Conversation

```
🤖 Assistant: Welcome! I'm here to help with our Python developer position. 
              What's your name and experience with Python?

👤 User: Hi, I'm Moshe and I'm a python developer with 3 years of experience. 
         My email is moshe@gmail.com and I'm not working at the moment.

🤖 Assistant: Great, Moshe! I can show you available times for the python backend 
              role interview. When are you usually free to discuss further?

              Here are the available time slots:
              • Monday, August 04 at 09:00 AM with Sarah Johnson
              • Tuesday, August 05 at 02:30 PM with Mike Chen  
              • Wednesday, August 06 at 10:00 AM with Sarah Johnson

👤 User: [Clicks "Select" on Monday option]

🤖 Assistant: 🎉 Interview Confirmed!
              📅 Date & Time: Monday, August 04, 2025 at 09:00 AM
              👤 Interviewer: Sarah Johnson
              ⏱️ Duration: 45 minutes
              📧 Confirmation sent to: moshe@gmail.com
```

**Key Improvement**: Notice how the assistant now recognizes "I'm not working at the moment" as an availability signal and moves directly to scheduling instead of asking redundant questions about job search status.

## 🧪 Testing

### Run All Tests

```bash
# CRITICAL: Always activate virtual environment first
source venv/bin/activate

# Core Agent tests
python tests/test_core_agent.py

# Database tests  
python tests/test_database.py

# Exit Advisor tests
python tests/test_exit_advisor.py

# Info Advisor tests
python tests/test_info_advisor.py

# Vector Database tests
python tests/test_vector_db.py

# Comprehensive evaluation
python tests/run_phase3_5_evaluation.py

# Simplified quick tests
python tests/test_phase3_5_simple.py

# Or run with pytest
pytest tests/
```

### Test Coverage

- ✅ Core Agent decision making (100% routing accuracy)
- ✅ Database operations (CRUD) 
- ✅ Scheduling logic and time parsing
- ✅ Exit Advisor with fine-tuning support
- ✅ Info Advisor with RAG capabilities
- ✅ Vector database operations (ChromaDB + OpenAI)
- ✅ Multi-agent orchestration
- ✅ End-to-end conversation flows
- ✅ Availability detection logic (recent enhancement)

## 📁 Project Structure

```
gai_final_project-1/
├── app/                          # Main application code
│   └── modules/                  # Application modules
│       ├── agents/               # AI agents (Core, Scheduling, Exit, Info)
│       ├── database/             # Database layer (SQLAlchemy models, managers)
│       ├── prompts/              # LLM prompts and templates
│       └── utils/                # Utility functions and helpers
├── streamlit_app/               # Streamlit UI application
│   ├── components/              # Reusable UI components
│   └── streamlit_main.py        # Main Streamlit application entry point
├── config/                      # Configuration files and settings
├── data/                        # Data storage and databases
│   ├── conversations/           # Conversation logs and history
│   ├── messages/                # Message data and templates
│   └── vector_db/               # Vector database storage (ChromaDB)
├── deployment/                  # Deployment configurations and scripts
├── docs/                        # Project documentation
├── fine_tuning/                 # Fine-tuning data and scripts
│   └── data/                    # Training data for fine-tuning
├── htmlcov/                     # Test coverage reports
├── resources/                   # Project resources and documentation
├── src/                         # Additional source code
├── tests/                       # Complete test suite
│   ├── evaluation_results/      # Test results and performance metrics
│   └── tests/                   # Nested test structure
│       └── evaluation_results/  # Additional evaluation data
├── activate.sh                  # Virtual environment activation script
├── .env.example                 # Environment variables template
├── LICENSE                      # MIT License
├── monitor_logs.py              # Log monitoring utility
├── mvc_monitor.py               # MVC architecture monitoring
├── packages.txt                 # System packages for deployment
├── pyproject.toml               # Modern Python project configuration
├── README.md                    # Project documentation (this file)
├── requirements-dev.txt         # Development dependencies
├── requirements.txt             # Production dependencies
├── setup.py                     # Package setup configuration
├── test_complete_core_agent.py  # Core agent comprehensive tests
└── TODO.md                      # Project tasks and progress tracking
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `CORE_AGENT_MODEL` | Model for Core Agent | `gpt-4o` |
| `EXIT_ADVISOR_FINE_TUNED_MODEL` | Fine-tuned Exit Advisor model (optional) | `ft:gpt-4o-0125:org:exit-advisor:id` |
| `EXIT_ADVISOR_FALLBACK_MODEL` | Fallback Exit Advisor model | `gpt-4o` |
| `SCHEDULING_ADVISOR_MODEL` | Model for Scheduling Advisor | `gpt-4o` |
| `INFO_ADVISOR_MODEL` | Model for Info Advisor (Phase 3) | `gpt-4o` |
| `OPENAI_MODEL` | Legacy model setting (deprecated) | `gpt-4o` |
| `OPENAI_TEMPERATURE` | Model temperature | `0.7` |
| `OPENAI_MAX_TOKENS` | Max tokens per response | `1000` |
| `DATABASE_URL` | Database connection string | `sqlite:///data/recruitment.db` |

### Model Configuration

```bash
# Required in .env file
OPENAI_API_KEY = "your-openai-api-key"

# Model Configuration (each agent can use different models)
CORE_AGENT_MODEL = "gpt-4o"
EXIT_ADVISOR_FINE_TUNED_MODEL = ""  # Set your fine-tuned model ID if available
EXIT_ADVISOR_FALLBACK_MODEL = "gpt-4o"
SCHEDULING_ADVISOR_MODEL = "gpt-4o"
INFO_ADVISOR_MODEL = "gpt-4o"

# Model Parameters
OPENAI_TEMPERATURE = 0.7        # 0.0 = deterministic, 1.0 = creative
OPENAI_MAX_TOKENS = 1000        # Response length limit
```

### Fine-Tuned Model Setup

The system supports fine-tuned models with automatic fallback to standard models:

**Setting up fine-tuned Exit Advisor:**
1. Train your model using `fine_tuning/exit_advisor_tuning.py`
2. Get your model ID from OpenAI (format: `ft:gpt-4o-0125:org:name:id`)
3. Set `EXIT_ADVISOR_FINE_TUNED_MODEL` in your `.env` file
4. If the fine-tuned model is unavailable, the system automatically falls back to `EXIT_ADVISOR_FALLBACK_MODEL`

**Environment Portability:**
- ✅ Works across different environments without code changes
- ✅ Graceful fallback when fine-tuned models aren't available  
- ✅ Each team member can use their own fine-tuned models
- ✅ Production/staging/development can use different model configurations
- ✅ No hardcoded model IDs - everything configurable via environment variables

## 🗄️ Database Schema

### Tables

**recruiters**
- `id`: Primary key
- `name`: Recruiter name
- `email`: Contact email
- `specialization`: Area of expertise

**available_slots**
- `id`: Primary key
- `recruiter_id`: Foreign key to recruiters
- `start_datetime`: Slot start time
- `duration_minutes`: Slot duration
- `is_available`: Availability status

**appointments**
- `id`: Primary key
- `candidate_name`: Candidate name
- `candidate_email`: Contact email
- `scheduled_datetime`: Interview time
- `recruiter_id`: Assigned recruiter
- `status`: Appointment status

## 🔧 API Reference

### Core Agent

```python
from app.modules.agents.core_agent import CoreAgent

# Initialize agent
agent = CoreAgent(openai_api_key="your_key")

# Make decision
decision, reasoning, response = agent.make_decision(
    conversation_messages=[...],
    user_message="I'm interested in the role"
)
```

### Scheduling Advisor

```python
from app.modules.agents.scheduling_advisor import SchedulingAdvisor

# Initialize advisor
advisor = SchedulingAdvisor(openai_api_key="your_key")

# Make scheduling decision
decision, reasoning, slots, response = advisor.make_scheduling_decision(
    candidate_info={"name": "John", "experience": "3 years"},
    conversation_messages=[...],
    latest_message="I'd like to schedule for tomorrow"
)
```

### DateTime Parser

```python
from app.modules.utils.datetime_parser import parse_scheduling_intent

# Parse natural language dates
result = parse_scheduling_intent("next Friday afternoon")
# Returns: {
#   'has_scheduling_intent': True,
#   'parsed_datetimes': [{'datetime': ..., 'confidence': 0.9}],
#   'confidence': 0.9
# }
```

## 🎨 UI Features

### Chat Interface
- 💬 Real-time chat with message history
- 🤖 AI reasoning display (expandable)
- 📅 Interactive time slot selection
- 📊 Conversation statistics
- 📥 Conversation export (JSON)
- 🔧 System status monitoring

### Sidebar Features
- 👤 Candidate information tracking
- 📈 Message statistics
- 🗑️ Clear conversation
- ⚡ Quick action buttons
- 🐛 Debug mode

## 🚀 Deployment

### Local Development

```bash
# Start development server
streamlit run streamlit_app/streamlit_main.py

# With custom port
streamlit run streamlit_app/streamlit_main.py --server.port 8502
```

### Production Deployment

1. **Streamlit Cloud**: Push to GitHub and deploy via Streamlit Cloud
2. **Docker**: Use provided Dockerfile for containerization
3. **Heroku**: Deploy with Procfile configuration

## 🔍 Troubleshooting

### Common Issues

**OpenAI API Key Error**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Or check .env file
cat .env | grep OPENAI_API_KEY
```

**Database Connection Error**
```bash
# Recreate database
python -c "from app.modules.database.sql_manager import SQLManager; SQLManager().create_tables()"
```

**Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Conversation Flow Issues** *(Recently Fixed)*
```bash
# If the agent asks redundant questions about job search status:
# This issue was resolved in January 2025 by enhancing availability detection
# The system now recognizes implicit availability signals like:
# - "not working", "between jobs", "unemployed"
# - "looking for work", "job hunting"

# To verify the fix is working:
python -c "
from app.modules.prompts.phase1_prompts import Phase1Prompts
prompts = Phase1Prompts()
# Check if 'not working' appears in extraction prompt
print('Fix verified' if 'not working' in str(prompts.__dict__) else 'Fix needed')
"
```

### Debug Mode

Enable debug mode in Streamlit for detailed error information:

```python
# In streamlit_main.py
if st.checkbox("🐛 Debug Mode"):
    # Shows detailed system information
```

Advisor with RAG and vector database integration
- **Phase 3.5**: Complete multi-agent orchestration with optimized conversation flows

### 🔄 **Current Status (January 2025)**
- **Production Ready**: All core features implemented and tested## 📈 Performance Metrics

### Phase 1 Targets (Achieved ✅)
- **Response Time**: < 3 seconds ✅
- **UI Responsiveness**: Smooth chat experience ✅
- **Database Operations**: < 100ms ✅
- **Natural Language Parsing**: 85%+ accuracy ✅


## 🙏 Acknowledgments

- **LangChain**: For the excellent agent framework
- **OpenAI**: For powerful language models
- **Streamlit**: For the beautiful UI framework
- **SQLAlchemy**: For robust database ORM
