# GAI Final Project

A comprehensive Python project template with virtual environment, development tools, and best practices.

## Project Structure

```
gai_final_project/
├── src/                    # Source code
│   └── __init__.py
├── tests/                  # Test files
│   ├── __init__.py
│   └── test_example.py
├── venv/                   # Virtual environment (created after setup)
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml         # Modern Python project configuration
├── setup.py               # Traditional setup file
├── activate.sh            # Convenience script to activate environment
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Quick Setup

### 1. Clone and Setup Environment

The virtual environment has already been created. To activate it and install dependencies:

```bash
# Activate the virtual environment (Option 1: using the convenience script)
./activate.sh

# Or activate manually (Option 2)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For development dependencies
pip install -r requirements-dev.txt
```

### 2. Environment Variables

Copy the environment template and configure your variables:

```bash
cp .env.example .env
# Edit .env with your actual values
```

### 3. Verify Installation

```bash
# Run tests to verify everything is working
pytest

# Check code formatting
black --check src/ tests/

# Run linting
flake8 src/ tests/
```

## Development Workflow

### Virtual Environment Management

```bash
# Activate environment
source venv/bin/activate
# or
./activate.sh

# Deactivate environment
deactivate

# Recreate environment (if needed)
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Code Quality Tools

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/

# Run all tests with coverage
pytest --cov=src --cov-report=html
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_example.py

# Run tests with verbose output
pytest -v
```

## Installation Options

### Development Installation

```bash
# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Production Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

The project uses python-dotenv to load environment variables. Copy `.env.example` to `.env` and configure:

- `ENVIRONMENT`: Set to 'development' or 'production'
- `DEBUG`: Enable/disable debug mode
- `LOG_LEVEL`: Set logging level (INFO, DEBUG, WARNING, ERROR)

## Contributing

1. Activate the virtual environment
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Make your changes
4. Run tests: `pytest`
5. Format code: `black src/ tests/`
6. Check linting: `flake8 src/ tests/`
7. Commit your changes

## Dependencies

### Core Dependencies
- `python-dotenv`: Environment variable management
- `requests`: HTTP library
- `numpy`: Numerical computing
- `pandas`: Data manipulation

### Development Dependencies
- `pytest`: Testing framework
- `black`: Code formatter
- `flake8`: Linter
- `isort`: Import sorter
- `mypy`: Type checker
- `ipython`: Enhanced Python shell
- `jupyter`: Notebook environment

## License

MIT License