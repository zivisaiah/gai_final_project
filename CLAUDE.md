# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Development Commands

### Virtual Environment Management
```bash
# CRITICAL: Always activate venv before running any Python commands
source venv/bin/activate

# Quick startup using provided script (recommended)
./run_app.sh

# Manual startup (requires venv activation)
python -m streamlit run streamlit_app/streamlit_main.py --server.port 8501
```

### Testing Commands
```bash
# Run specific test files
python tests/test_core_agent.py
python tests/test_database.py
python tests/test_exit_advisor.py
python tests/test_info_advisor.py
python tests/test_vector_db.py

# Run comprehensive evaluation tests
python tests/run_phase3_5_evaluation.py

# Run complete system tests
python test_complete_core_agent.py

# Using pytest (alternative)
pytest tests/
```

### Database Operations
```bash
# Initialize database with sample data
python -c "from app.modules.database.sql_manager import SQLManager; SQLManager().create_sample_data()"

# Create database tables
python -c "from app.modules.database.sql_manager import SQLManager; SQLManager().create_tables()"
```

### Code Quality Tools
```bash
# Format code
black .

# Check code style
flake8

# Sort imports
isort .

# Type checking (if configured)
mypy app/
```

## Multi-Agent Architecture

This is a sophisticated multi-agent recruitment chatbot system with the following architecture:

### Core Agent (Main Orchestrator)
- **Location**: `app/modules/agents/core_agent.py`
- **Purpose**: Main decision-making agent that routes to specialized advisors
- **Decisions**: CONTINUE, SCHEDULE, END, INFO
- **Uses enhanced keyword-based routing for 100% accuracy**

### Specialized Advisory Agents
1. **Exit Advisor** (`app/modules/agents/exit_advisor.py`)
   - Determines when to end conversations 
   - Supports fine-tuned models with fallback
   - Uses conversation context and sentiment analysis

2. **Scheduling Advisor** (`app/modules/agents/scheduling_advisor.py`)
   - Manages interview scheduling
   - Integrates with SQL database for time slots
   - Parses natural language time requests

3. **Info Advisor** (`app/modules/agents/info_advisor.py`)
   - Handles job-related questions using RAG
   - Integrates with vector database (ChromaDB + OpenAI Vector Store)
   - Processes PDF job descriptions

### Data Layer
- **SQL Database**: SQLite with SQLAlchemy ORM (`app/modules/database/`)
- **Vector Database**: ChromaDB for document embeddings (`data/vector_db/`)
- **Models**: `recruiters`, `available_slots`, `appointments` tables

## Key Configuration

### Environment Variables (.env file required)
```bash
OPENAI_API_KEY=your_openai_api_key_here
CORE_AGENT_MODEL=gpt-3.5-turbo
EXIT_ADVISOR_FINE_TUNED_MODEL=  # Optional fine-tuned model ID
SCHEDULING_ADVISOR_MODEL=gpt-3.5-turbo
INFO_ADVISOR_MODEL=gpt-3.5-turbo
```

### MVC Architecture Requirement
- Follow MVC (Model-View-Controller) pattern strictly
- Avoid logic and code duplication
- Maintain clear separation of concerns

## Important Development Notes

### Virtual Environment Usage
- **CRITICAL**: All Python operations MUST be performed within the activated virtual environment
- The system will fail with `ModuleNotFoundError: No module named 'chromadb'` if venv is not activated
- Use `./run_app.sh` script for automatic venv handling

### Agent Decision Flow
1. User input → Core Agent
2. Core Agent consults appropriate advisor (Exit/Scheduling/Info)
3. Advisor provides recommendation
4. Core Agent makes final decision and generates response
5. System tracks conversation state and decision history

### Testing Strategy
- Each agent has dedicated test files
- System performance target: 96%+ (currently achieved)
- Evaluation includes confusion matrices and accuracy metrics
- Test data in `tests/evaluation_results/`

### Database Schema
- `recruiters`: Recruiter information and specializations  
- `available_slots`: Interview time slots with availability status
- `appointments`: Scheduled interviews with candidate details

### Fine-Tuning Support
- Exit Advisor supports fine-tuned models
- Automatic fallback to standard models if fine-tuned unavailable
- Training data in `fine_tuning/data/`

### Streamlit UI Structure
- **Main App**: `streamlit_app/streamlit_main.py`
- **Components**: Registration form, chat interface, admin panel
- **Features**: Real-time analytics, conversation export, debug mode

## Common Workflows

### Adding New Features
1. Update relevant agent in `app/modules/agents/`
2. Add prompts to `app/modules/prompts/`
3. Create/update tests in `tests/`
4. Update UI components in `streamlit_app/components/`
5. Run full test suite to verify functionality

### Debugging Issues
1. Enable debug mode in Streamlit UI
2. Check conversation logs in `data/conversations/`
3. Review agent decision reasoning in UI
4. Verify database state with SQL manager tools

### Performance Monitoring
- System tracks decision accuracy and response times
- Evaluation metrics stored in `tests/evaluation_results/`
- Monitor conversation analytics via admin panel