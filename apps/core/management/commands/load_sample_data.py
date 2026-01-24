"""
Management command to load sample data for the entire system.
Run this command after initial migrations to populate sample data.

Usage:
    python manage.py load_sample_data
    python manage.py load_sample_data --reset  # Reset and reload all sample data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from src.users.models import SupplierProfile, SellerProfile, DriverProfile
from src.products.models import Category, Product
from src.orders.models import Deal, DealItem, Delivery, DeliveryItem

User = get_user_model()


class Command(BaseCommand):
    help = 'Load sample data for the entire system (users, products, deals, deliveries)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing sample data before loading new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Deleting all existing sample data...'))
            DeliveryItem.objects.all().delete()
            Delivery.objects.all().delete()
            DealItem.objects.all().delete()
            Deal.objects.all().delete()
            Product.objects.all().delete()
            DriverProfile.objects.all().delete()
            SellerProfile.objects.all().delete()
            SupplierProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('All sample data deleted.'))

        self.stdout.write(self.style.SUCCESS('Loading sample data...'))

        # Load categories first (if not exists)
        categories = Category.objects.filter(is_active=True)
        if not categories.exists():
            self.stdout.write(self.style.WARNING('No categories found. Please run: python manage.py load_categories'))
            return

        # Get some categories for products
        citrus_cat = Category.objects.filter(slug='citrus-fruits').first()
        vegetables_cat = Category.objects.filter(slug='vegetables').first()
        fruits_cat = Category.objects.filter(slug='fruits').first()
        meat_cat = Category.objects.filter(slug='meat-products').first()
        dairy_cat = Category.objects.filter(slug='dairy-products').first()
        grains_cat = Category.objects.filter(slug='grains').first()

        # ==================== CREATE USERS ====================
        self.stdout.write('\n1. Creating users...')

        # Suppliers
        suppliers_data = [
            {
                'username': 'fresh_foods_supplier',
                'email': 'supplier1@example.com',
                'first_name': 'Ahmet',
                'last_name': 'Yılmaz',
                'phone_number': '+905551234567',
                'role': User.Role.SUPPLIER,
                'profile': {
                    'company_name': 'Fresh Foods Wholesale',
                    'tax_number': '1234567890',
                    'address': 'Atatürk Cad. No:123, Kadıköy',
                    'city': 'Istanbul',
                    'description': 'Fresh fruits and vegetables supplier',
                }
            },
            {
                'username': 'meat_supplier',
                'email': 'supplier2@example.com',
                'first_name': 'Mehmet',
                'last_name': 'Demir',
                'phone_number': '+905551234568',
                'role': User.Role.SUPPLIER,
                'profile': {
                    'company_name': 'Premium Meat Company',
                    'tax_number': '1234567891',
                    'address': 'İnönü Cad. No:45, Çankaya',
                    'city': 'Ankara',
                    'description': 'Premium quality meat and poultry supplier',
                }
            },
            {
                'username': 'dairy_supplier',
                'email': 'supplier3@example.com',
                'first_name': 'Ayşe',
                'last_name': 'Kaya',
                'phone_number': '+905551234569',
                'role': User.Role.SUPPLIER,
                'profile': {
                    'company_name': 'Dairy Products Co.',
                    'tax_number': '1234567892',
                    'address': 'Cumhuriyet Bul. No:78, Konak',
                    'city': 'Izmir',
                    'description': 'Fresh dairy products supplier',
                }
            },
        ]

        # Sellers
        sellers_data = [
            {
                'username': 'market_istanbul',
                'email': 'seller1@example.com',
                'first_name': 'Fatma',
                'last_name': 'Şahin',
                'phone_number': '+905551234570',
                'role': User.Role.SELLER,
                'profile': {
                    'business_name': 'Istanbul Fresh Market',
                    'business_type': 'Supermarket',
                    'tax_number': '9876543210',
                    'address': 'Bağdat Cad. No:200, Kadıköy',
                    'city': 'Istanbul',
                    'description': 'Large supermarket chain',
                }
            },
            {
                'username': 'restaurant_ankara',
                'email': 'seller2@example.com',
                'first_name': 'Ali',
                'last_name': 'Öztürk',
                'phone_number': '+905551234571',
                'role': User.Role.SELLER,
                'profile': {
                    'business_name': 'Ankara Restaurant',
                    'business_type': 'Restaurant',
                    'tax_number': '9876543211',
                    'address': 'Kızılay Meydanı No:15, Çankaya',
                    'city': 'Ankara',
                    'description': 'Fine dining restaurant',
                }
            },
            {
                'username': 'bakery_izmir',
                'email': 'seller3@example.com',
                'first_name': 'Zeynep',
                'last_name': 'Arslan',
                'phone_number': '+905551234572',
                'role': User.Role.SELLER,
                'profile': {
                    'business_name': 'Izmir Bakery',
                    'business_type': 'Bakery',
                    'tax_number': '9876543212',
                    'address': 'Alsancak Cad. No:30, Konak',
                    'city': 'Izmir',
                    'description': 'Artisan bakery and cafe',
                }
            },
        ]

        # Drivers
        drivers_data = [
            {
                'username': 'driver_istanbul',
                'email': 'driver1@example.com',
                'first_name': 'Mustafa',
                'last_name': 'Çelik',
                'phone_number': '+905551234573',
                'role': User.Role.DRIVER,
                'profile': {
                    'license_number': 'DL123456',
                    'vehicle_type': DriverProfile.VehicleType.VAN,
                    'vehicle_plate': '34ABC123',
                    'city': 'Istanbul',
                    'is_available': True,
                }
            },
            {
                'username': 'driver_ankara',
                'email': 'driver2@example.com',
                'first_name': 'Hasan',
                'last_name': 'Yıldız',
                'phone_number': '+905551234574',
                'role': User.Role.DRIVER,
                'profile': {
                    'license_number': 'DL123457',
                    'vehicle_type': DriverProfile.VehicleType.TRUCK,
                    'vehicle_plate': '06DEF456',
                    'city': 'Ankara',
                    'is_available': True,
                }
            },
            {
                'username': 'driver_izmir',
                'email': 'driver3@example.com',
                'first_name': 'Emre',
                'last_name': 'Doğan',
                'phone_number': '+905551234575',
                'role': User.Role.DRIVER,
                'profile': {
                    'license_number': 'DL123458',
                    'vehicle_type': DriverProfile.VehicleType.CAR,
                    'vehicle_plate': '35GHI789',
                    'city': 'Izmir',
                    'is_available': True,
                }
            },
        ]

        created_users = []
        created_suppliers = []
        created_sellers = []
        created_drivers = []

        # Create suppliers
        for supplier_data in suppliers_data:
            profile_data = supplier_data.pop('profile')
            user, created = User.objects.get_or_create(
                username=supplier_data['username'],
                defaults={**supplier_data, 'password': 'pbkdf2_sha256$600000$dummy$dummy='}  # Dummy password
            )
            if created:
                user.set_password('sample123')
                user.save()
                created_users.append(user)
            
            profile, created = SupplierProfile.objects.get_or_create(
                user=user,
                defaults=profile_data
            )
            if not created:
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.save()
            created_suppliers.append(profile)
            self.stdout.write(f'  {"Created" if created else "Updated"}: Supplier - {profile.company_name}')

        # Create sellers
        for seller_data in sellers_data:
            profile_data = seller_data.pop('profile')
            user, created = User.objects.get_or_create(
                username=seller_data['username'],
                defaults={**seller_data, 'password': 'pbkdf2_sha256$600000$dummy$dummy='}
            )
            if created:
                user.set_password('sample123')
                user.save()
                created_users.append(user)
            
            profile, created = SellerProfile.objects.get_or_create(
                user=user,
                defaults=profile_data
            )
            if not created:
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.save()
            created_sellers.append(profile)
            self.stdout.write(f'  {"Created" if created else "Updated"}: Seller - {profile.business_name}')

        # Create drivers
        for driver_data in drivers_data:
            profile_data = driver_data.pop('profile')
            user, created = User.objects.get_or_create(
                username=driver_data['username'],
                defaults={**driver_data, 'password': 'pbkdf2_sha256$600000$dummy$dummy='}
            )
            if created:
                user.set_password('sample123')
                user.save()
                created_users.append(user)
            
            profile, created = DriverProfile.objects.get_or_create(
                user=user,
                defaults=profile_data
            )
            if not created:
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.save()
            created_drivers.append(profile)
            self.stdout.write(f'  {"Created" if created else "Updated"}: Driver - {user.get_full_name()}')

        # ==================== CREATE PRODUCTS ====================
        self.stdout.write('\n2. Creating products...')

        products_data = [
            # Fresh Foods Supplier products
            {
                'supplier': created_suppliers[0],
                'category': citrus_cat,
                'name': 'Fresh Oranges',
                'description': 'Premium quality fresh oranges',
                'price': Decimal('25.50'),
                'unit': Product.Unit.KG,
                'stock': 500,
                'min_order_quantity': 10,
            },
            {
                'supplier': created_suppliers[0],
                'category': vegetables_cat,
                'name': 'Fresh Tomatoes',
                'description': 'Ripe red tomatoes',
                'price': Decimal('18.00'),
                'unit': Product.Unit.KG,
                'stock': 300,
                'min_order_quantity': 5,
            },
            {
                'supplier': created_suppliers[0],
                'category': fruits_cat,
                'name': 'Fresh Apples',
                'description': 'Crisp red apples',
                'price': Decimal('22.00'),
                'unit': Product.Unit.KG,
                'stock': 400,
                'min_order_quantity': 10,
            },
            # Meat Supplier products
            {
                'supplier': created_suppliers[1],
                'category': meat_cat,
                'name': 'Premium Beef',
                'description': 'High quality beef cuts',
                'price': Decimal('350.00'),
                'unit': Product.Unit.KG,
                'stock': 100,
                'min_order_quantity': 1,
            },
            {
                'supplier': created_suppliers[1],
                'category': meat_cat,
                'name': 'Chicken Breast',
                'description': 'Fresh chicken breast',
                'price': Decimal('85.00'),
                'unit': Product.Unit.KG,
                'stock': 200,
                'min_order_quantity': 1,
            },
            # Dairy Supplier products
            {
                'supplier': created_suppliers[2],
                'category': dairy_cat,
                'name': 'Fresh Milk',
                'description': 'Whole milk 1L',
                'price': Decimal('15.50'),
                'unit': Product.Unit.LITER,
                'stock': 1000,
                'min_order_quantity': 10,
            },
            {
                'supplier': created_suppliers[2],
                'category': dairy_cat,
                'name': 'White Cheese',
                'description': 'Traditional white cheese',
                'price': Decimal('120.00'),
                'unit': Product.Unit.KG,
                'stock': 150,
                'min_order_quantity': 1,
            },
            {
                'supplier': created_suppliers[2],
                'category': dairy_cat,
                'name': 'Yogurt',
                'description': 'Natural yogurt',
                'price': Decimal('18.00'),
                'unit': Product.Unit.KG,
                'stock': 300,
                'min_order_quantity': 5,
            },
            # More products from Fresh Foods
            {
                'supplier': created_suppliers[0],
                'category': grains_cat,
                'name': 'Premium Rice',
                'description': 'High quality basmati rice',
                'price': Decimal('45.00'),
                'unit': Product.Unit.KG,
                'stock': 200,
                'min_order_quantity': 5,
            },
        ]

        created_products = []
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                supplier=product_data['supplier'],
                name=product_data['name'],
                defaults=product_data
            )
            if not created:
                for key, value in product_data.items():
                    if key != 'supplier':
                        setattr(product, key, value)
                product.save()
            created_products.append(product)
            self.stdout.write(f'  {"Created" if created else "Updated"}: {product.name} - {product.supplier.company_name}')

        # ==================== CREATE DEALS ====================
        self.stdout.write('\n3. Creating deals...')

        deals_data = [
            {
                'seller': created_sellers[0],
                'supplier': created_suppliers[0],
                'driver': created_drivers[0],
                'status': Deal.Status.DEALING,
                'delivery_address': 'Bağdat Cad. No:200, Kadıköy, Istanbul',
                'delivery_note': 'Please deliver in the morning',
                'cost_split': False,
                'items': [
                    {'product': created_products[0], 'quantity': 50},  # Oranges
                    {'product': created_products[1], 'quantity': 30},  # Tomatoes
                ]
            },
            {
                'seller': created_sellers[1],
                'supplier': created_suppliers[1],
                'driver': None,
                'status': Deal.Status.LOOKING_FOR_DRIVER,
                'delivery_address': 'Kızılay Meydanı No:15, Çankaya, Ankara',
                'delivery_note': 'Urgent delivery needed',
                'cost_split': True,
                'items': [
                    {'product': created_products[3], 'quantity': 10},  # Beef
                    {'product': created_products[4], 'quantity': 20},  # Chicken
                ]
            },
            {
                'seller': created_sellers[2],
                'supplier': created_suppliers[2],
                'driver': created_drivers[2],
                'status': Deal.Status.DONE,
                'delivery_address': 'Alsancak Cad. No:30, Konak, Izmir',
                'delivery_note': 'Regular delivery',
                'cost_split': False,
                'items': [
                    {'product': created_products[5], 'quantity': 50},  # Milk
                    {'product': created_products[6], 'quantity': 5},   # Cheese
                ]
            },
        ]

        created_deals = []
        for deal_data in deals_data:
            items_data = deal_data.pop('items')
            deal = Deal.objects.create(**deal_data)
            
            for item_data in items_data:
                DealItem.objects.create(
                    deal=deal,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['product'].price
                )
            
            created_deals.append(deal)
            self.stdout.write(f'  Created: Deal #{deal.id} - {deal.seller.business_name} & {deal.supplier.company_name}')

        # ==================== CREATE DELIVERIES ====================
        self.stdout.write('\n4. Creating deliveries...')

        # Create delivery from the DONE deal
        done_deal = created_deals[2]  # The deal with status DONE
        if done_deal.status == Deal.Status.DONE and not done_deal.delivery:
            delivery = Delivery.objects.create(
                seller=done_deal.seller,
                supplier=done_deal.supplier,
                driver=done_deal.driver,
                delivery_address=done_deal.delivery_address,
                delivery_note=done_deal.delivery_note,
                status=Delivery.Status.CONFIRMED
            )
            
            # Create delivery items from deal items
            for deal_item in done_deal.items.all():
                DeliveryItem.objects.create(
                    delivery=delivery,
                    product=deal_item.product,
                    quantity=deal_item.quantity,
                    unit_price=deal_item.unit_price
                )
            
            # Calculate total and link deal to delivery
            delivery.calculate_total()
            done_deal.delivery = delivery
            done_deal.save()
            
            self.stdout.write(f'  Created: Delivery #{delivery.id} from Deal #{done_deal.id}')

        # Create a standalone delivery
        standalone_delivery = Delivery.objects.create(
            seller=created_sellers[0],
            supplier=created_suppliers[0],
            driver=created_drivers[0],
            delivery_address='Bağdat Cad. No:200, Kadıköy, Istanbul',
            delivery_note='Direct delivery order',
            status=Delivery.Status.READY
        )
        
        DeliveryItem.objects.create(
            delivery=standalone_delivery,
            product=created_products[8],  # Rice
            quantity=25,
            unit_price=created_products[8].price
        )
        
        standalone_delivery.calculate_total()
        self.stdout.write(f'  Created: Standalone Delivery #{standalone_delivery.id}')

        # ==================== SUMMARY ====================
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully loaded sample data!\n'
                f'   - Users: {len(created_users)} created\n'
                f'   - Suppliers: {len(created_suppliers)}\n'
                f'   - Sellers: {len(created_sellers)}\n'
                f'   - Drivers: {len(created_drivers)}\n'
                f'   - Products: {len(created_products)}\n'
                f'   - Deals: {len(created_deals)}\n'
                f'   - Deliveries: 2\n\n'
                f'Default password for all sample users: sample123'
            )
        )
