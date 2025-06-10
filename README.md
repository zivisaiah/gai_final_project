# 🤖 Multi-Agent Python Developer Recruitment Assistant

**GAI Final Project - Complete Multi-Agent System**

An intelligent recruitment chatbot with advanced multi-agent architecture for Python developer recruitment. Features comprehensive information assistance, interview scheduling, conversation analytics, and cloud deployment capabilities. Built with LangChain, OpenAI API, vector databases, and advanced Streamlit UI.

## 🎯 Project Overview

This project implements a sophisticated multi-agent recruitment assistant that can:

### 🎯 **Core Capabilities**
- 💬 **Intelligent Conversations**: Multi-turn dialogue with context awareness and personality
- 🧠 **Smart Decision Making**: 4-option routing (Continue, Schedule, Info, End) with confidence scoring
- 📅 **Interview Scheduling**: Natural language parsing and intelligent slot management
- 📚 **Information Assistant**: RAG-powered Q&A about job descriptions using vector databases
- 📊 **Analytics Dashboard**: Real-time performance monitoring and conversation insights
- 🚀 **Cloud Deployment**: Production-ready Streamlit Cloud integration

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
- Python 3.8+
- OpenAI API key
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/zivisaiah/gai_final_project.git
cd gai_final_project

# Activate virtual environment
source venv/bin/activate
# or use the convenience script
./activate.sh

# Install dependencies
pip install -r requirements.txt
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
# Start Streamlit application
streamlit run streamlit_app/streamlit_main.py
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

👤 User: Hi, I'm Sarah and I have 3 years of Python experience.

🤖 Assistant: Great to meet you, Sarah! Your Python experience sounds excellent. 
              Are you interested in learning more about the role or would you 
              like to schedule an interview?

👤 User: I'd like to schedule an interview for next Friday afternoon.

🤖 Assistant: Perfect! I have several time slots available next Friday:
              1. Friday, January 15th at 2:00 PM with Alice Smith
              2. Friday, January 15th at 3:30 PM with Bob Johnson
              Which time works best for you?

👤 User: [Clicks "Select" on option 1]

🤖 Assistant: 🎉 Interview Confirmed!
              📅 Date & Time: Friday, January 15, 2024 at 2:00 PM
              👤 Interviewer: Alice Smith
              ⏱️ Duration: 45 minutes
```

## 🧪 Testing

### Run All Tests

```bash
# Core Agent tests
python test_core_agent_simple.py

# Database tests  
python test_database_simple.py

# Scheduling Advisor tests
python test_scheduling_advisor_simple.py

# Streamlit UI tests
python test_streamlit_simple.py

# Or run with pytest
pytest tests/
```

### Test Coverage

- ✅ Core Agent decision making
- ✅ Database operations (CRUD)
- ✅ Scheduling logic and time parsing
- ✅ Streamlit UI components
- ✅ End-to-end conversation flows

## 📁 Project Structure

```
gai_final_project/
├── app/                           # Main application code
│   ├── modules/
│   │   ├── agents/               # AI agents
│   │   │   ├── core_agent.py     # Main conversation agent
│   │   │   └── scheduling_advisor.py # Scheduling specialist
│   │   ├── database/             # Database layer
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   └── sql_manager.py    # Database operations
│   │   ├── prompts/              # LLM prompts
│   │   │   ├── phase1_prompts.py # Core agent prompts
│   │   │   └── scheduling_prompts.py # Scheduling prompts
│   │   └── utils/                # Utilities
│   │       ├── conversation.py   # Conversation management
│   │       └── datetime_parser.py # Date/time parsing
├── streamlit_app/                # Streamlit UI
│   ├── components/
│   │   └── chat_interface.py     # Chat UI components
│   └── streamlit_main.py         # Main Streamlit app
├── config/                       # Configuration
│   └── phase1_settings.py        # Settings management
├── data/                         # Data storage
├── tests/                        # Test suite
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `CORE_AGENT_MODEL` | Model for Core Agent | `gpt-3.5-turbo` |
| `EXIT_ADVISOR_FINE_TUNED_MODEL` | Fine-tuned Exit Advisor model (optional) | `ft:gpt-3.5-turbo-0125:org:exit-advisor:id` |
| `EXIT_ADVISOR_FALLBACK_MODEL` | Fallback Exit Advisor model | `gpt-3.5-turbo` |
| `SCHEDULING_ADVISOR_MODEL` | Model for Scheduling Advisor | `gpt-3.5-turbo` |
| `INFO_ADVISOR_MODEL` | Model for Info Advisor (Phase 3) | `gpt-3.5-turbo` |
| `OPENAI_MODEL` | Legacy model setting (deprecated) | `gpt-3.5-turbo` |
| `OPENAI_TEMPERATURE` | Model temperature | `0.7` |
| `OPENAI_MAX_TOKENS` | Max tokens per response | `1000` |
| `DATABASE_URL` | Database connection string | `sqlite:///data/recruitment.db` |

### Model Configuration

```bash
# Required in .env file
OPENAI_API_KEY = "your-openai-api-key"

# Model Configuration (each agent can use different models)
CORE_AGENT_MODEL = "gpt-3.5-turbo"
EXIT_ADVISOR_FINE_TUNED_MODEL = ""  # Set your fine-tuned model ID if available
EXIT_ADVISOR_FALLBACK_MODEL = "gpt-3.5-turbo"
SCHEDULING_ADVISOR_MODEL = "gpt-3.5-turbo"
INFO_ADVISOR_MODEL = "gpt-3.5-turbo"

# Model Parameters
OPENAI_TEMPERATURE = 0.7        # 0.0 = deterministic, 1.0 = creative
OPENAI_MAX_TOKENS = 1000        # Response length limit
```

### Fine-Tuned Model Setup

The system supports fine-tuned models with automatic fallback to standard models:

**Setting up fine-tuned Exit Advisor:**
1. Train your model using `fine_tuning/exit_advisor_tuning.py`
2. Get your model ID from OpenAI (format: `ft:gpt-3.5-turbo-0125:org:name:id`)
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

### Debug Mode

Enable debug mode in Streamlit for detailed error information:

```python
# In streamlit_main.py
if st.checkbox("🐛 Debug Mode"):
    # Shows detailed system information
```

## 📈 Performance Metrics

### Phase 1 Targets (Achieved ✅)
- **Response Time**: < 3 seconds ✅
- **UI Responsiveness**: Smooth chat experience ✅
- **Database Operations**: < 100ms ✅
- **Natural Language Parsing**: 85%+ accuracy ✅

## 🛣️ Roadmap

### Phase 2: Exit Capability (Planned)
- Exit Advisor with fine-tuned model
- 3-action decision system (Continue/Schedule/End)
- Enhanced conversation analytics

### Phase 3: Information Capability (Planned)
- Vector database integration (Chroma)
- Information Advisor for job Q&A
- Complete multi-agent orchestration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add comprehensive tests for new features
- Update documentation for API changes
- Use type hints for better code clarity

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain**: For the excellent agent framework
- **OpenAI**: For powerful language models
- **Streamlit**: For the beautiful UI framework
- **SQLAlchemy**: For robust database ORM

## 📞 Support

For questions or issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review existing [Issues](https://github.com/zivisaiah/gai_final_project/issues)
3. Create a new issue with detailed information

---

**Built with ❤️ for intelligent recruitment automation**