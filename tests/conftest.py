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
        min_order_quantity=1,
        is_active=True
    )


@pytest.fixture
def deal(seller_user, supplier_user):
    """Create a test deal"""
    from apps.orders.models import Deal
    deal = Deal.objects.create(
        seller=seller_user.seller_profile,
        supplier=supplier_user.supplier_profile,
        delivery_handler=Deal.DeliveryHandler.SYSTEM_DRIVER,
        delivery_cost_split=50,  # Default: split equally
        delivery_count=1,  # Default is 1 (each deal must have at least one delivery)
        status=Deal.Status.DEALING
    )
    # Note: RequestToDriver is not created here to allow tests to create their own
    return deal


@pytest.fixture
def delivery(deal):
    """Create a test delivery from deal"""
    from apps.orders.models import Delivery, Deal, RequestToDriver
    # Set driver based on delivery_handler and accepted RequestToDriver
    # If no accepted request exists, driver_profile will be None
    driver_profile = None
    if deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER:
        accepted_request = deal.driver_requests.filter(status=RequestToDriver.Status.ACCEPTED).first()
        if accepted_request and accepted_request.driver:
            driver_profile = accepted_request.driver
    
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
    """Create a test delivery item (needs deal_item from delivery.deal)"""
    from apps.orders.models import DeliveryItem, DealItem
    deal_item, _ = DealItem.objects.get_or_create(
        deal=delivery.deal, product=product,
        defaults={'quantity': 10, 'unit_price': product.price}
    )
    return DeliveryItem.objects.create(
        delivery=delivery, deal_item=deal_item, quantity=5
    )


@pytest.fixture
def driver_request(deal, driver_user):
    """Create a test driver request"""
    from apps.orders.models import RequestToDriver
    # Get or create to avoid unique constraint violations
    request, created = RequestToDriver.objects.get_or_create(
        deal=deal,
        driver=driver_user.driver_profile,
        defaults={
            'requested_price': Decimal('150.00'),
            'created_by': deal.seller.user
        }
    )
    return request