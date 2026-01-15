#!/bin/bash

echo "Creating virtual environment..."
# Use python3 on Linux/Mac, python on Windows (Git Bash)
if command -v python3 &> /dev/null; then
    python3 -m venv venv
else
    python -m venv venv
fi

echo "Activating virtual environment..."
# Detect OS and use appropriate activation script
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash)
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

echo "Installing dependencies..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

echo ""
echo "========================================"
echo "Environment setup complete!"
echo "========================================"
echo ""
echo "To activate the environment, run:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "  source venv/Scripts/activate"
else
    echo "  source venv/bin/activate"
fi
echo ""
echo "To create .env file, copy .env.example:"
echo "  cp .env.example .env"
echo ""
echo "Then edit .env with your settings."
echo ""
echo "To run migrations:"
echo "  python manage.py migrate"
echo ""
echo "To create superuser:"
echo "  python manage.py createsuperuser"
echo ""
echo "To run the server:"
echo "  python manage.py runserver"
echo ""
