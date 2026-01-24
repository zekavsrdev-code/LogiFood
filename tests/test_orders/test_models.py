"""
Tests for Order models
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from src.orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
class TestOrderModel:
    """Test Order model"""
    
    def test_create_order(self, seller_user, supplier_user):
        """Test creating an order"""
        order = Order.objects.create(
            seller=seller_user.seller_profile,
            supplier=supplier_user.supplier_profile,
            delivery_address='Test Address',
            delivery_note='Test note',
            status=Order.Status.PENDING
        )
        assert order.seller == seller_user.seller_profile
        assert order.supplier == supplier_user.supplier_profile
        assert order.status == Order.Status.PENDING
        assert order.total_amount == Decimal('0.00')
        assert order.delivery_address == 'Test Address'
    
    def test_order_str(self, order):
        """Test order string representation"""
        assert 'Order #' in str(order)
        assert order.seller.business_name in str(order)
    
    def test_order_calculate_total(self, order, product):
        """Test order total calculation"""
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2,
            unit_price=product.price
        )
        total = order.calculate_total()
        expected_total = product.price * 2
        assert total == expected_total
        assert order.total_amount == expected_total
    
    def test_order_status_choices(self, seller_user, supplier_user):
        """Test order status choices"""
        for status_value, status_label in Order.Status.choices:
            order = Order.objects.create(
                seller=seller_user.seller_profile,
                supplier=supplier_user.supplier_profile,
                delivery_address='Test Address',
                status=status_value
            )
            assert order.status == status_value
            assert order.get_status_display() == status_label


@pytest.mark.django_db
class TestOrderItemModel:
    """Test OrderItem model"""
    
    def test_create_order_item(self, order, product):
        """Test creating an order item"""
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            unit_price=product.price
        )
        assert order_item.order == order
        assert order_item.product == product
        assert order_item.quantity == 5
        assert order_item.unit_price == product.price
    
    def test_order_item_total_price(self, order, product):
        """Test order item total price calculation"""
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=3,
            unit_price=Decimal('10.00')
        )
        expected_total = Decimal('30.00')
        assert order_item.total_price == expected_total
    
    def test_order_item_auto_unit_price(self, order, product):
        """Test automatic unit price from product"""
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=2
        )
        assert order_item.unit_price == product.price
    
    def test_order_item_str(self, order_item):
        """Test order item string representation"""
        assert order_item.product.name in str(order_item)
        assert str(order_item.quantity) in str(order_item)
