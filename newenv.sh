#!/bin/bash

# Exit on error
set -e

# Function to detect OS and set BASE_DIR
set_base_dir() {
  case "$(uname -s)" in
    Darwin)
      BASE_DIR="$HOME/Documents/Workspace"
      ;;
    Linux)
      BASE_DIR="$HOME/workspace"
      ;;
    MINGW*|CYGWIN*|MSYS*)
      BASE_DIR="$HOME/Documents/Workspace"
      ;;
    *)
      BASE_DIR="$HOME/workspace"
      ;;
  esac
}

# Function to find Python 3
find_python() {
  if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
  elif command -v python &> /dev/null; then
    if python --version 2>&1 | grep -q "Python 3"; then
      PYTHON_CMD="python"
    else
      echo "Error: Python 3 is required but not found"
      exit 1
    fi
  else
    echo "Error: Python is not installed"
    exit 1
  fi
}

# Function to find pip
find_pip() {
  if [ "$PYTHON_CMD" = "python3" ]; then
    PIP_CMD="pip3"
  else
    PIP_CMD="pip"
  fi
  
  if ! command -v $PIP_CMD &> /dev/null; then
    echo "Error: pip is not installed"
    exit 1
  fi
}

# Main logic
set_base_dir
find_python
find_pip

# Detect if we are inside a Git repo
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  PROJECT_PATH="$(pwd)"
  PROJECT_NAME="$(basename "$PROJECT_PATH")"
  echo "🔎 Detected Git repo. Using current directory: $PROJECT_PATH"
else
  if [ -z "$1" ]; then
    echo "Usage: ./newenv.sh <project_name>  (or run inside an existing Git repo)"
    exit 1
  fi
  PROJECT_NAME="$1"
  PROJECT_PATH="$BASE_DIR/$PROJECT_NAME"
  mkdir -p "$PROJECT_PATH"
  cd "$PROJECT_PATH"
  echo "📂 Created new project directory: $PROJECT_PATH"
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
$PYTHON_CMD -m venv .venv

# Activate venv
if [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
  VENV_PYTHON=".venv/Scripts/python.exe"
  VENV_PIP=".venv/Scripts/pip.exe"
else
  source .venv/bin/activate
  VENV_PYTHON=".venv/bin/python"
  VENV_PIP=".venv/bin/pip"
fi

# Update pip
echo "⬆️  Upgrading pip..."
$VENV_PYTHON -m pip install --upgrade pip

# Create .env if missing
if [ ! -f ".env" ]; then
  echo "SECRET_KEY=your_secret_key_here" > .env
  echo "✅ Created .env"
fi

# Create requirements.txt if missing
if [ ! -f "requirements.txt" ]; then
  touch requirements.txt
  echo "✅ Created requirements.txt"
fi

# Create .gitignore if missing
if [ ! -f ".gitignore" ]; then
cat <<EOL > .gitignore
.venv/
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
dist/
.eggs/
*.egg-info/
.DS_Store
.idea/
.vscode/
*.swp
*.swo
*~
EOL
  echo "✅ Created .gitignore"
fi

# Create starter main.py if missing
if [ ! -f "main.py" ]; then
cat <<EOL > main.py
import os
from dotenv import load_dotenv

load_dotenv()
secret = os.getenv("SECRET_KEY")

print(f"Hello from $PROJECT_NAME!")
print(f"Loaded secret key: {secret}")
EOL
  echo "✅ Created main.py"
fi

# Install basic package
$VENV_PIP install --quiet python-dotenv
$VENV_PIP freeze > requirements.txt

# Open in VS Code if available
if command -v code &> /dev/null; then
  code .
fi

echo ""
echo "✅ Project '$PROJECT_NAME' set up at '$PROJECT_PATH'"
echo ""
echo "To activate the virtual environment later:"
if [ -f ".venv/Scripts/activate" ]; then
  echo "   source .venv/Scripts/activate"
else
  echo "   source .venv/bin/activate"
fi
echo "🚀 Happy coding!"
