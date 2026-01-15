@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

echo.
echo ========================================
echo Environment setup complete!
echo ========================================
echo.
echo To activate the environment, run:
echo   Command Prompt: venv\Scripts\activate.bat
echo   Git Bash: source venv/Scripts/activate
echo.
echo To create .env file, copy .env.example:
echo   copy .env.example .env
echo.
echo Then edit .env with your settings.
echo.
echo To run migrations:
echo   python manage.py migrate
echo.
echo To create superuser:
echo   python manage.py createsuperuser
echo.
echo To run the server:
echo   python manage.py runserver
echo.
