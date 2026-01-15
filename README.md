# LogiFood - Professional Django REST API

A professionally structured Django REST API project with layered architecture, environment configuration, and best practices.

## 🏗️ Project Structure

```
LogiFood/
├── apps/                    # Core utilities and base classes
│   └── core/               # Core app with base classes only
│       ├── models.py       # Base models (TimeStampedModel)
│       ├── serializers.py  # Base serializers
│       ├── views.py        # Base viewsets
│       ├── services.py     # Base service layer
│       ├── utils.py        # Utility functions
│       ├── exceptions.py   # Custom exceptions
│       ├── permissions.py  # Custom permissions
│       ├── pagination.py   # Custom pagination
│       ├── filters.py      # Custom filters
│       └── urls.py         # Core URLs (health check)
├── src/                     # Application modules
│   └── users/              # User management module
│       ├── models.py       # User model
│       ├── serializers.py  # User serializers
│       ├── views.py        # User views
│       ├── urls.py         # User URLs
│       ├── services.py     # User service layer
│       ├── utils.py        # User utilities
│       └── admin.py        # User admin
├── tests/                   # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_users/         # User module tests
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   ├── test_serializers.py
│   │   └── test_services.py
│   └── test_core/          # Core tests
│       ├── test_utils.py
│       └── test_health_check.py
├── config/                 # Project configuration
│   ├── settings/           # Settings modules
│   │   ├── base.py        # Base settings
│   │   ├── development.py # Development settings
│   │   └── production.py  # Production settings
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── static/                 # Static files
├── media/                  # Media files
├── templates/              # Template files
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── pytest.ini             # Pytest configuration
├── manage.py              # Django management script
├── setup_env.bat          # Windows setup script
└── setup_env.sh           # Linux/Mac setup script
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL (recommended) or SQLite
- pip

### Quick Terminal Reference

| Action | Windows (CMD) | Windows (Git Bash) | Linux/Mac |
|--------|---------------|---------------------|-----------|
| Setup | `setup_env.bat` | `bash setup_env.sh` | `./setup_env.sh` |
| Activate venv | `venv\Scripts\activate.bat` | `source venv/Scripts/activate` | `source venv/bin/activate` |
| Copy .env | `copy .env.example .env` | `cp .env.example .env` | `cp .env.example .env` |
| Run server | `python manage.py runserver` | `python manage.py runserver` | `python manage.py runserver` |

### Installation

#### Windows (Command Prompt)

1. Run the setup script:
```cmd
setup_env.bat
```

2. Activate the virtual environment:
```cmd
venv\Scripts\activate.bat
```

#### Windows (Git Bash) / Linux / Mac

1. Make the setup script executable (Linux/Mac only):
```bash
chmod +x setup_env.sh
```

2. Run the setup script:
```bash
# Windows (Git Bash)
bash setup_env.sh

# Linux/Mac
./setup_env.sh
```

3. Activate the virtual environment:
```bash
# Windows (Git Bash)
source venv/Scripts/activate

# Linux/Mac
source venv/bin/activate
```

### Configuration

1. Copy the environment example file:
```bash
# Windows (Command Prompt)
copy .env.example .env

# Windows (Git Bash) / Linux / Mac
cp .env.example .env
```

2. Edit `.env` file with your settings:
   - Set `SECRET_KEY` (generate a new one for production)
   - Configure database credentials
   - Set `DEBUG=True` for development
   - Configure other settings as needed

3. Run migrations:
```bash
# Make sure virtual environment is activated first
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

**Note:** Always activate the virtual environment before running Django commands:
- **Windows (Command Prompt):** `venv\Scripts\activate.bat`
- **Windows (Git Bash):** `source venv/Scripts/activate`
- **Linux/Mac:** `source venv/bin/activate`

The API will be available at `http://localhost:8000/`

## 📚 API Documentation

Once the server is running, access the API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema JSON**: http://localhost:8000/api/schema/

## 🏛️ Architecture Layers

### 1. Models Layer (`models.py`)
- Database models using Django ORM
- Base `TimeStampedModel` for automatic timestamps
- Custom User model

### 2. Serializers Layer (`serializers.py`)
- Data validation and serialization
- Base serializer with common fields
- Request/response transformation

### 3. Views Layer (`views.py`)
- API endpoints
- Request handling
- Response formatting
- Base viewsets for common operations

### 4. Services Layer (`services.py`)
- Business logic
- Database operations
- Reusable service methods
- Base service class

### 5. Utils Layer (`utils.py`)
- Helper functions
- Common utilities
- Response formatters

## 🔐 Authentication

The project uses JWT (JSON Web Tokens) for authentication.

### Register a new user:
```bash
POST /api/auth/register/
{
    "email": "user@example.com",
    "username": "username",
    "password": "securepassword",
    "password2": "securepassword",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Login:
```bash
POST /api/auth/login/
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

### Access protected endpoints:
Include the JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## 🧪 Testing

The project uses pytest for testing. Tests are organized in the `tests/` directory.

### Run all tests:
```bash
# Make sure virtual environment is activated
pytest
```

### Run with coverage:
```bash
pytest --cov
```

### Run specific test file:
```bash
pytest tests/test_users/test_views.py
```

### Run specific test:
```bash
pytest tests/test_users/test_views.py::TestUserLogin::test_login_success
```

**Note:** Ensure your virtual environment is activated before running tests.

### Test Structure:
- `tests/conftest.py` - Shared fixtures
- `tests/test_users/` - User module tests
- `tests/test_core/` - Core utility tests

## 📦 Key Features

- ✅ Professional project structure with `src/` for modules
- ✅ Environment-based configuration
- ✅ Layered architecture (Models, Views, Serializers, Services)
- ✅ JWT Authentication
- ✅ Custom User Model
- ✅ API Documentation (Swagger/ReDoc)
- ✅ CORS support
- ✅ Database abstraction (PostgreSQL ready)
- ✅ Logging configuration
- ✅ Development/Production settings separation
- ✅ Base classes for reusability
- ✅ Custom exceptions and permissions
- ✅ Pagination support
- ✅ Comprehensive test suite with pytest

## 🛠️ Development Tools

All commands below require the virtual environment to be activated.

- **Django Debug Toolbar**: Available in development mode
- **Black**: Code formatting
  ```bash
  black .
  ```
- **isort**: Import sorting
  ```bash
  isort .
  ```
- **flake8**: Linting
  ```bash
  flake8 .
  ```
- **pytest**: Testing framework (see Testing section above)

## 📝 Adding New Modules

1. Create a new module in `src/`:
```bash
mkdir -p src/<module_name>
```

2. Create the module structure:
   - `__init__.py`
   - `apps.py` - Django app config (set `name = 'src.<module_name>'` and `label = '<module_name>'`)
   - `models.py` - Database models
   - `serializers.py` - Data serialization
   - `views.py` - API views
   - `urls.py` - URL routing
   - `services.py` - Business logic
   - `admin.py` - Admin configuration
   - `utils.py` - Module utilities

3. Add the module to `INSTALLED_APPS` in `config/settings/base.py`:
```python
LOCAL_APPS = [
    'apps.core',
    'src.users',
    'src.<module_name>',  # Add your new module
]
```

4. Include URLs in `config/urls.py`:
```python
path('api/<module_path>/', include('src.<module_name>.urls')),
```

5. Create tests in `tests/test_<module_name>/`:
   - `test_models.py`
   - `test_views.py`
   - `test_serializers.py`
   - `test_services.py`

## 🔒 Security Notes

- Never commit `.env` file to version control
- Use strong `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` properly
- Use HTTPS in production
- Keep dependencies updated

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
