"""
Pytest configuration and fixtures
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from decimal import Decimal

User = get_user_model()


@pytest.fixture
def api_client():
    """API client fixture"""
    return APIClient()


@pytest.fixture
def user():
    """Create a test user"""
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123',
        first_name='Test',
        last_name='User',
        role=User.Role.SELLER,
    )


@pytest.fixture
def supplier_user():
    """Create a supplier user"""
    return User.objects.create_user(
        email='supplier@example.com',
        username='supplier',
        password='supplier123',
        first_name='Supplier',
        last_name='User',
        role=User.Role.SUPPLIER,
    )


@pytest.fixture
def seller_user():
    """Create a seller user"""
    return User.objects.create_user(
        email='seller@example.com',
        username='seller',
        password='seller123',
        first_name='Seller',
        last_name='User',
        role=User.Role.SELLER,
    )


@pytest.fixture
def driver_user():
    """Create a driver user"""
    return User.objects.create_user(
        email='driver@example.com',
        username='driver',
        password='driver123',
        first_name='Driver',
        last_name='User',
        role=User.Role.DRIVER,
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def supplier_client(supplier_user):
    """Authenticated supplier API client"""
    client = APIClient()
    client.force_authenticate(user=supplier_user)
    return client


@pytest.fixture
def seller_client(seller_user):
    """Authenticated seller API client"""
    client = APIClient()
    client.force_authenticate(user=seller_user)
    return client


@pytest.fixture
def driver_client(driver_user):
    """Authenticated driver API client"""
    client = APIClient()
    client.force_authenticate(user=driver_user)
    return client


@pytest.fixture
def admin_user():
    """Create an admin user"""
    return User.objects.create_superuser(
        email='admin@example.com',
        username='admin',
        password='adminpass123',
    )


# ==================== PRODUCTS FIXTURES ====================

@pytest.fixture
def category():
    """Create a test category"""
    from apps.products.models import Category
    return Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='Test category description',
        is_active=True
    )


@pytest.fixture
def parent_category():
    """Create a parent category"""
    from apps.products.models import Category
    return Category.objects.create(
        name='Parent Category',
        slug='parent-category',
        description='Parent category',
        is_active=True
    )


@pytest.fixture
def child_category(parent_category):
    """Create a child category"""
    from apps.products.models import Category
    return Category.objects.create(
        name='Child Category',
        slug='child-category',
        description='Child category',
        parent=parent_category,
        is_active=True
    )


@pytest.fixture
def product(supplier_user, category):
    """Create a test product"""
    from apps.products.models import Product
    return Product.objects.create(
        supplier=supplier_user.supplier_profile,
        category=category,
        name='Test Product',
        description='Test product description',
        price=Decimal('99.99'),
        unit=Product.Unit.KG,
        stock=100,
        min_order_quantity=1,
        is_active=True
    )


@pytest.fixture
def deal(seller_user, supplier_user, driver_user):
    """Create a test deal"""
    from apps.orders.models import Deal
    return Deal.objects.create(
        seller=seller_user.seller_profile,
        supplier=supplier_user.supplier_profile,
        driver=driver_user.driver_profile,
        delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
        delivery_cost_split=50,  # Default: split equally
        delivery_count=1,  # Default is 1 (each deal must have at least one delivery)
        status=Deal.Status.DEALING
    )


@pytest.fixture
def delivery(deal):
    """Create a test delivery from deal"""
    from apps.orders.models import Delivery, Deal
    # Set driver based on delivery_handler
    driver_profile = None
    if deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER and deal.driver:
        driver_profile = deal.driver
    
    return Delivery.objects.create(
        deal=deal,
        delivery_address='Test Address',
        delivery_note='Test note',
        status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
        supplier_share=100,
        driver_profile=driver_profile,
        # Manual driver fields should be None when using system driver
        driver_name=None,
        driver_phone=None,
        driver_vehicle_type=None,
        driver_vehicle_plate=None,
        driver_license_number=None
    )




@pytest.fixture
def delivery_item(delivery, product):
    """Create a test delivery item"""
    from apps.orders.models import DeliveryItem
    return DeliveryItem.objects.create(
        delivery=delivery,
        product=product,
        quantity=5,
        unit_price=product.price
    )


@pytest.fixture
def driver_request(deal, driver_user):
    """Create a test driver request"""
    from apps.orders.models import RequestToDriver
    return RequestToDriver.objects.create(
        deal=deal,
        driver=driver_user.driver_profile,
        requested_price=Decimal('150.00'),
        created_by=deal.seller.user
    )
