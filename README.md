# LogiFood - Professional Django REST API

A professional logistics and product sales platform that enables Suppliers, Sellers, and Drivers to discover and work with each other.

## System Overview

- **Supplier**: Adds products to the system and offers them for sale
- **Seller**: Places orders for products from suppliers
- **Driver**: Delivers orders

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
├── tests/                   # Test suite (layered architecture)
│   ├── conftest.py         # Shared pytest fixtures
│   ├── test_users/         # User module tests
│   │   ├── test_models.py
│   │   ├── test_serializers.py
│   │   ├── test_services.py
│   │   └── test_views.py
│   ├── test_products/      # Product module tests
│   │   ├── test_models.py
│   │   ├── test_serializers.py
│   │   ├── test_services.py
│   │   └── test_views.py
│   ├── test_orders/        # Order module tests
│   │   ├── test_models.py
│   │   ├── test_serializers.py
│   │   ├── test_services.py
│   │   └── test_views.py
│   └── test_core/          # Core utility tests
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

4. Load initial data (market food categories):
```bash
python manage.py load_categories
```

This command loads market food categories including:
- **Main Categories**: Citrus Fruits, Vegetables, Fruits, Legumes, Grains, Dairy Products, Meat and Meat Products, Fish and Seafood, Nuts and Dried Fruits, Spices and Herbs, Bakery Products, Beverages, Oils and Fats, Honey and Natural Products
- **Sub-categories**: Leafy Vegetables, Root Vegetables, Nightshade Vegetables, Cucurbitaceae (under Vegetables); Stone Fruits, Berries, Tropical Fruits (under Fruits); Red Meat, Poultry, Processed Meat (under Meat); Milk and Cream, Cheese, Yogurt and Fermented Products (under Dairy)

To reset and reload all categories:
```bash
python manage.py load_categories --reset
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
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

## 🏛️ Architecture & Design Decisions

### Architectural Approach: Layered Architecture

This project follows a **layered architecture pattern** (also known as **n-tier architecture**), which separates concerns into distinct layers. This approach provides:


### Architecture Layers

#### 1. Models Layer (`models.py`)
**Responsibility**: Data structure and database representation

- **Django ORM**: All database interactions use Django's Object-Relational Mapping
- **Base Models**: `TimeStampedModel` provides automatic `created_at`, `updated_at`, and `created_by` fields
- **Custom User Model**: Extended Django's `AbstractUser` with role-based system
- **Relationships**: Foreign keys, OneToOne, and reverse relationships managed by ORM
- **Business Logic**: Model methods for calculations and validations

**Why Django ORM?**
- Type-safe queries with IDE autocomplete
- Automatic SQL generation and optimization
- Built-in migration system
- Protection against SQL injection
- Database abstraction (works with PostgreSQL, MySQL, SQLite)

#### 2. Serializers Layer (`serializers.py`)
**Responsibility**: Data validation, transformation, and serialization

- **Input Validation**: Validates incoming request data
- **Data Transformation**: Converts between Python objects and JSON
- **Nested Serialization**: Handles complex object relationships
- **Role-based Fields**: Different fields based on user roles

#### 3. Services Layer (`services.py`)
**Responsibility**: Business logic and orchestration

- **Business Rules**: All business logic is centralized here
- **Transaction Management**: Ensures data consistency with `@transaction.atomic`
- **Reusability**: Service methods can be used by views, management commands, or other services
- **Testability**: Business logic can be tested without HTTP layer
- **Error Handling**: Custom `BusinessLogicError` for domain-specific errors

**Why Service Layer?**
- **Separation of Concerns**: Views handle HTTP, services handle business logic
- **SOLID Principles**: Single Responsibility (views = HTTP, services = business logic)
- **Reusability**: Same business logic can be used in API, CLI, or background tasks
- **Testability**: Business logic can be unit tested without HTTP overhead
- **Maintainability**: Changes to business rules are centralized

#### 4. Views Layer (`views.py`)
**Responsibility**: HTTP request/response handling

- **DRF Generic Views**: Uses `ViewSet` and `GenericAPIView` for consistency
- **Permission Control**: Role-based access control via custom permissions
- **Response Formatting**: Standardized success/error responses
- **Minimal Logic**: Views delegate to services, keeping them thin

**Why DRF Generic Views?**
- **Consistency**: Standard patterns across all endpoints
- **Less Boilerplate**: Built-in CRUD operations
- **Best Practices**: Follows Django REST Framework conventions
- **API Documentation**: Automatic schema generation for Swagger/ReDoc

#### 5. Utils Layer (`utils.py`)
**Responsibility**: Helper functions and utilities

- **Response Helpers**: Standardized API response formatting
- **Common Utilities**: Reusable functions across the application

### Design Patterns Used

1. **Repository Pattern**: Service layer acts as repository, abstracting database operations
2. **Factory Pattern**: Fixtures in tests create objects with default values
3. **Strategy Pattern**: Different serializers based on action (create vs. update)
4. **Observer Pattern**: Django signals for automatic profile creation

### SOLID Principles Implementation

- **Single Responsibility**: Each class has one reason to change
  - Models: Data structure
  - Serializers: Data validation/transformation
  - Services: Business logic
  - Views: HTTP handling

- **Open/Closed**: Base classes (`BaseService`, `TimeStampedModel`) are open for extension, closed for modification

- **Liskov Substitution**: All service classes can be used interchangeably through `BaseService`

- **Interface Segregation**: Small, focused interfaces (permissions, serializers)

- **Dependency Inversion**: Views depend on service abstractions, not concrete implementations

### Database Structure

See the [Database Structure](#-database-structure) section below for detailed information about models and relationships.

## 🗄️ Database Structure

### ORM Choice: Django ORM

This project uses **Django ORM** (Object-Relational Mapping) for all database operations. Django ORM provides:

- **Type Safety**: IDE autocomplete and type checking
- **SQL Injection Protection**: Parameterized queries by default
- **Database Abstraction**: Works with PostgreSQL, MySQL, SQLite without code changes
- **Migration System**: Version-controlled database schema changes
- **Query Optimization**: `select_related()` and `prefetch_related()` for efficient queries
- **Relationship Management**: Automatic handling of foreign keys, reverse relationships

### Database Models and Relationships

#### Core Models

**TimeStampedModel** (Abstract Base Model)
- `created_at`: Auto-populated timestamp
- `updated_at`: Auto-updated timestamp
- `created_by`: Foreign key to User (tracks who created the record)
- All models inherit from this for consistent timestamp tracking

#### User Management Models

**User** (Custom User Model)
- Extends Django's `AbstractUser`
- **Role System**: SUPPLIER, SELLER, DRIVER
- **Relationships**:
  - OneToOne → `SupplierProfile`, `SellerProfile`, `DriverProfile` (via reverse relationships)

**SupplierProfile**
- OneToOne with User
- **Relationships**:
  - OneToMany → `Product` (supplier.products)
  - OneToMany → `Deal` (supplier.deals)

**SellerProfile**
- OneToOne with User
- **Relationships**:
  - OneToMany → `Deal` (seller.deals)

**DriverProfile**
- OneToOne with User
- **Relationships**:
  - OneToMany → `Deal` (driver.deals)
  - OneToMany → `Delivery` (driver_profile.deliveries)
  - OneToMany → `RequestToDriver` (driver.requests)

#### Product Models

**Category**
- Self-referential (parent-child hierarchy)
- **Relationships**:
  - OneToMany → `Product` (category.products)
  - Self → `Category` (parent.children)

**Product**
- **Relationships**:
  - ManyToOne → `SupplierProfile` (product.supplier)
  - ManyToOne → `Category` (product.category)
  - OneToMany → `DealItem` (product.deal_items)
  - OneToMany → `DeliveryItem` (product.delivery_items)

#### Order Models

**Deal**
- Represents an agreement between Seller and Supplier
- **Relationships**:
  - ManyToOne → `SellerProfile` (deal.seller)
  - ManyToOne → `SupplierProfile` (deal.supplier)
  - ManyToOne → `DriverProfile` (deal.driver, nullable)
  - OneToMany → `DealItem` (deal.items)
  - OneToMany → `Delivery` (deal.deliveries)
  - OneToMany → `RequestToDriver` (deal.requests)

**DealItem**
- Items within a Deal
- **Relationships**:
  - ManyToOne → `Deal` (item.deal)
  - ManyToOne → `Product` (item.product)

**Delivery**
- Actual delivery instance created from Deal
- **Relationships**:
  - ManyToOne → `Deal` (delivery.deal)
  - ManyToOne → `DriverProfile` (delivery.driver_profile, nullable)
  - OneToMany → `DeliveryItem` (delivery.items)

**DeliveryItem**
- Items within a Delivery
- **Relationships**:
  - ManyToOne → `Delivery` (item.delivery)
  - ManyToOne → `Product` (item.product)

**RequestToDriver**
- Driver request/negotiation for a Deal
- **Relationships**:
  - ManyToOne → `Deal` (request.deal)
  - ManyToOne → `DriverProfile` (request.driver)
  - Unique constraint: One request per driver per deal

### Database Relationships Diagram

```
User (1) ──(1:1)── SupplierProfile (1) ──(1:N)── Product
                    │
                    └──(1:N)── Deal ──(1:N)── Delivery
                                      │
                                      └──(1:N)── RequestToDriver

User (1) ──(1:1)── SellerProfile (1) ──(1:N)── Deal

User (1) ──(1:1)── DriverProfile (1) ──(1:N)── Deal
                    │
                    ├──(1:N)── Delivery
                    │
                    └──(1:N)── RequestToDriver

Category (self-referential)
    │
    └──(1:N)── Product
```

### Query Optimization

Django ORM provides several optimization techniques used in this project:

1. **select_related()**: For ForeignKey and OneToOne relationships
   ```python
   Deal.objects.select_related('seller', 'supplier', 'driver')
   ```

2. **prefetch_related()**: For ManyToMany and reverse ForeignKey relationships
   ```python
   Category.objects.prefetch_related('children')
   ```

3. **only() / defer()**: Load only needed fields
   ```python
   Product.objects.only('name', 'price')
   ```

### Migration Strategy

- **Version Control**: All migrations are committed to git
- **Backward Compatibility**: Migrations are designed to be reversible
- **Data Migrations**: Custom migrations for data transformations (e.g., `load_categories`)
- **Zero Downtime**: Migrations are designed to work with running applications

## 🔐 Authentication

The project uses JWT (JSON Web Tokens) for authentication. **Email is optional; login is done with username.**

### Supplier Registration:
```bash
POST /api/auth/register/
{
    "username": "supplier1",
    "password": "securepassword123",
    "password2": "securepassword123",
    "role": "SUPPLIER",
    "company_name": "ABC Food Ltd.",
    "phone_number": "+15551234567",
    "city": "New York",
    "address": "123 Main St, New York"
}
```

### Seller Registration:
```bash
POST /api/auth/register/
{
    "username": "seller1",
    "password": "securepassword123",
    "password2": "securepassword123",
    "role": "SELLER",
    "business_name": "Central Market",
    "business_type": "Market",
    "phone_number": "+15559876543",
    "city": "Boston",
    "address": "456 Oak Ave, Boston"
}
```

### Driver Registration:
```bash
POST /api/auth/register/
{
    "username": "driver1",
    "password": "securepassword123",
    "password2": "securepassword123",
    "role": "DRIVER",
    "license_number": "34ABC123",
    "vehicle_type": "VAN",
    "vehicle_plate": "34 ABC 123",
    "phone_number": "+15557654321",
    "city": "New York"
}
```

### Login (with username):
```bash
POST /api/auth/login/
{
    "username": "supplier1",
    "password": "securepassword123"
}
```

### Accessing protected endpoints:
Include the JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## 📦 API Endpoints

### Auth Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/auth/register/` | User registration (role-based) |
| POST | `/api/auth/login/` | Login (with username) |
| POST | `/api/auth/logout/` | Logout |
| GET/PUT | `/api/auth/profile/` | View/update profile |
| GET/PUT | `/api/auth/profile/role/` | View/update role profile |
| POST | `/api/auth/change-password/` | Change password |
| PUT | `/api/auth/toggle-availability/` | Driver availability toggle |

### Product Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/products/` | List all products |
| GET | `/api/products/<id>/` | Product detail |
| GET/POST | `/api/my-products/` | Supplier products (own) |
| GET/PUT/DELETE | `/api/my-products/<id>/` | Supplier product management |

### Order Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/orders/` | Orders (role-based) |
| GET | `/api/orders/<id>/` | Order detail |
| PUT | `/api/orders/<id>/status/` | Update order status |
| PUT | `/api/orders/<id>/assign-driver/` | Assign driver |

### Discovery Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/suppliers/` | List suppliers |
| GET | `/api/drivers/` | List available drivers |
| GET | `/api/available-orders/` | Available orders for drivers |
| POST | `/api/accept-order/<id>/` | Driver accept order |

### Category Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/categories/` | List categories |

## 🧪 Testing Strategy

This project follows a comprehensive testing strategy with **90% code coverage**, ensuring reliability and maintainability.

### Testing Philosophy

We use **pytest** as our primary testing framework, following the **AAA pattern** (Arrange-Act-Assert) for clear and readable tests. Our testing strategy covers three main levels:

#### 1. Unit Tests
Test individual components in isolation:
- **Models** (`test_models.py`): Test model methods, validations, relationships, and business logic
- **Serializers** (`test_serializers.py`): Test data validation, transformation, and serialization logic
- **Services** (`test_services.py`): Test business logic, data operations, and service layer methods

**Example Unit Test:**
```python
def test_create_deal(self, seller_user, supplier_user):
    """Test creating a deal"""
    deal = Deal.objects.create(
        seller=seller_user.seller_profile,
        supplier=supplier_user.supplier_profile,
        delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
        status=Deal.Status.DEALING
    )
    assert deal.seller == seller_user.seller_profile
    assert deal.status == Deal.Status.DEALING
```

#### 2. Integration Tests
Test component interactions and API endpoints:
- **Views** (`test_views.py`): Test API endpoints, authentication, permissions, and request/response handling
- **End-to-End Flows**: Test complete user workflows (registration → product creation → deal → delivery)

**Example Integration Test:**
```python
def test_create_deal_as_seller(self, seller_client, supplier_user, product):
    """Test seller can create a deal"""
    response = seller_client.post('/api/orders/deals/', {
        'supplier_id': supplier_user.supplier_profile.id,
        'items': [{'product_id': product.id, 'quantity': 10}]
    })
    assert response.status_code == 201
    assert Deal.objects.count() == 1
```

#### 3. Test Fixtures and Organization

**Shared Fixtures** (`tests/conftest.py`):
- `api_client`: DRF API client for making requests
- `user`, `supplier_user`, `seller_user`, `driver_user`: User fixtures with different roles
- `product`, `category`, `deal`: Domain object fixtures
- `authenticated_client`, `supplier_client`, etc.: Pre-authenticated API clients

**Test Organization:**

The test suite follows a **layered architecture pattern**, mirroring the application structure:

```
tests/
├── conftest.py                    # Shared pytest fixtures
├── test_users/                   # User module tests
│   ├── test_models.py           # User model unit tests
│   ├── test_serializers.py      # User serializer tests
│   ├── test_services.py         # User service layer tests
│   └── test_views.py            # User API integration tests
├── test_products/               # Product module tests
│   ├── test_models.py           # Product/Category model tests
│   ├── test_serializers.py      # Product serializer tests
│   ├── test_services.py         # Product service layer tests
│   └── test_views.py            # Product API integration tests
├── test_orders/                 # Order module tests
│   ├── test_models.py           # Deal/Delivery/RequestToDriver model tests
│   ├── test_serializers.py      # Order serializer tests
│   ├── test_services.py        # Order service layer tests
│   └── test_views.py            # Order API integration tests
├── test_e2e/                    # End-to-end flow tests (API-only)
│   └── test_order_flow.py       # Full order flows via HTTP
└── test_core/                   # Core utility tests
    ├── test_utils.py
    └── test_health_check.py
```

**Test Organization Principles:**
- **One file per layer**: Each module has separate test files for models, serializers, services, and views
- **Consistent structure**: All modules follow the same test organization pattern
- **Clear separation**: Unit tests (models, serializers, services) are separate from integration tests (views)
- **E2E layer**: Full user journeys are tested in `test_e2e/` via API only (no direct DB manipulation)
- **Shared fixtures**: Common test data is defined in `conftest.py` for reusability

This organization ensures:
- **Maintainability**: Easy to find and update tests for specific layers
- **Scalability**: New modules can follow the same pattern
- **Clarity**: Test structure mirrors application architecture
- **Best Practices**: Follows industry-standard testing patterns

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run with coverage report:**
```bash
pytest --cov --cov-report=term-missing
```

**Run specific test file:**
```bash
pytest tests/test_users/test_views.py
```

**Run specific test:**
```bash
pytest tests/test_users/test_views.py::TestUserLogin::test_login_success
```

**Run tests by marker:**
```bash
pytest -m unit          # Run only unit tests
pytest -m integration  # Run only integration tests
pytest -m e2e           # Run only end-to-end flow tests
pytest -m "not slow"    # Skip slow tests
```

### Test Coverage

Current test coverage: **90%**

Coverage is maintained through:
- Comprehensive unit tests for all models and services
- Integration tests for all API endpoints
- Edge case testing for business logic
- Error handling and validation testing

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

### Management Commands

- **Load Categories**: Load market food categories into the database
  ```bash
  python manage.py load_categories
  ```
  To reset and reload all categories:
  ```bash
  python manage.py load_categories --reset
  ```

### Code Quality Tools

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
