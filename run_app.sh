#!/bin/bash

# Recruitment Chatbot - Application Launcher
# Ensures the app runs in the virtual environment with all dependencies

set -e  # Exit on any error

echo "🚀 Starting Recruitment Chatbot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Verify ChromaDB is available
echo "🔍 Checking dependencies..."
python -c "import chromadb; print('✅ ChromaDB import successful')" || {
    echo "❌ ChromaDB not found. Installing dependencies..."
    pip install -r requirements.txt
}

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please copy .env.example to .env and configure it."
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your OpenAI API key"
fi

# Start the application
echo "🌟 Starting Streamlit application..."
echo "📍 Virtual environment: $(which python)"
echo "🌐 Application will be available at: http://localhost:8501"
echo ""

python -m streamlit run streamlit_app/streamlit_main.py --server.port 8501 