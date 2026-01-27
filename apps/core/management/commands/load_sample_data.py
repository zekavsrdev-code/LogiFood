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
from apps.users.models import SupplierProfile, SellerProfile, DriverProfile
from apps.products.models import Category, Product
from apps.orders.models import Deal, DealItem, Delivery, DeliveryItem, RequestToDriver

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
            RequestToDriver.objects.all().delete()
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
                'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
                'delivery_cost_split': 50,  # Split equally
                'status': Deal.Status.DEALING,
                'items': [
                    {'product': created_products[0], 'quantity': 50},  # Oranges
                    {'product': created_products[1], 'quantity': 30},  # Tomatoes
                ]
            },
            {
                'seller': created_sellers[1],
                'supplier': created_suppliers[1],
                'driver': None,
                'delivery_handler': Deal.DeliveryHandler.SUPPLIER,  # Supplier handles delivery (3rd party)
                'delivery_cost_split': 50,  # Not used for 3rd party, but set to default
                'status': Deal.Status.DEALING,
                'items': [
                    {'product': created_products[3], 'quantity': 10},  # Beef
                    {'product': created_products[4], 'quantity': 20},  # Chicken
                ]
            },
            {
                'seller': created_sellers[2],
                'supplier': created_suppliers[2],
                'driver': None,  # No driver initially - will be requested
                'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
                'delivery_cost_split': 50,  # Split equally
                'status': Deal.Status.LOOKING_FOR_DRIVER,  # Looking for driver
                'items': [
                    {'product': created_products[5], 'quantity': 50},  # Milk
                    {'product': created_products[6], 'quantity': 5},   # Cheese
                ]
            },
            {
                'seller': created_sellers[0],
                'supplier': created_suppliers[1],
                'driver': created_drivers[2],
                'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
                'delivery_cost_split': 100,  # Supplier pays all
                'status': Deal.Status.DONE,
                'items': [
                    {'product': created_products[0], 'quantity': 100},  # Oranges
                ]
            },
            {
                'seller': created_sellers[1],
                'supplier': created_suppliers[0],
                'driver': None,
                'delivery_handler': Deal.DeliveryHandler.SYSTEM_DRIVER,
                'delivery_cost_split': 0,  # Seller pays all
                'status': Deal.Status.LOOKING_FOR_DRIVER,  # Looking for driver
                'items': [
                    {'product': created_products[3], 'quantity': 25},  # Beef
                ]
            },
        ]

        created_deals = []
        for deal_data in deals_data:
            items_data = deal_data.pop('items')
            # Set created_by for the deal
            deal_creator = deal_data['seller'].user if 'seller' in deal_data else deal_data['supplier'].user
            deal = Deal.objects.create(**deal_data, created_by=deal_creator)
            
            for item_data in items_data:
                DealItem.objects.create(
                    deal=deal,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['product'].price,
                    created_by=deal_creator
                )
            
            created_deals.append(deal)
            self.stdout.write(f'  Created: Deal #{deal.id} - {deal.seller.business_name} & {deal.supplier.company_name}')

        # ==================== CREATE DRIVER REQUESTS ====================
        self.stdout.write('\n4. Creating driver requests...')
        
        # Find deals with LOOKING_FOR_DRIVER status
        looking_for_driver_deals = [d for d in created_deals if d.status == Deal.Status.LOOKING_FOR_DRIVER]
        created_requests = []
        
        for deal in looking_for_driver_deals:
            # Create requests to different drivers
            for driver in created_drivers:
                # Skip if driver is already assigned to this deal
                if deal.driver == driver:
                    continue
                
                # Create request with different prices based on deal
                requested_price = Decimal('150.00') if deal.delivery_cost_split == 50 else Decimal('200.00')
                
                # Determine who created the request (supplier or seller based on delivery_cost_split)
                if deal.delivery_cost_split == 100:
                    creator = deal.supplier.user
                elif deal.delivery_cost_split == 0:
                    creator = deal.seller.user
                else:
                    # Split - seller creates the request
                    creator = deal.seller.user
                
                request = RequestToDriver.objects.create(
                    deal=deal,
                    driver=driver,
                    requested_price=requested_price,
                    status=RequestToDriver.Status.PENDING,
                    created_by=creator
                )
                created_requests.append(request)
                self.stdout.write(f'  Created: Request #{request.id} - Deal #{deal.id} to Driver {driver.user.username}')
        
        # Simulate some driver responses
        if created_requests:
            # First request: Driver proposes a price
            if len(created_requests) > 0:
                request1 = created_requests[0]
                request1.driver_proposed_price = Decimal('175.00')
                request1.status = RequestToDriver.Status.DRIVER_PROPOSED
                request1.save()
                self.stdout.write(f'  Updated: Request #{request1.id} - Driver proposed price {request1.driver_proposed_price}')
            
            # Second request: Driver approves directly
            if len(created_requests) > 1:
                request2 = created_requests[1]
                request2.driver_approved = True
                request2.supplier_approved = True
                request2.seller_approved = True
                request2.final_price = request2.requested_price
                request2.status = RequestToDriver.Status.ACCEPTED
                request2.save()
                # Assign driver to deal
                request2.deal.driver = request2.driver
                request2.deal.status = Deal.Status.DEALING
                request2.deal.save()
                self.stdout.write(f'  Updated: Request #{request2.id} - All parties approved, driver assigned to deal')
            
            # Third request: Partial approval (only supplier approved)
            if len(created_requests) > 2:
                request3 = created_requests[2]
                request3.supplier_approved = True
                request3.save()
                self.stdout.write(f'  Updated: Request #{request3.id} - Supplier approved, waiting for seller and driver')

        # ==================== CREATE DELIVERIES ====================
        self.stdout.write('\n5. Creating deliveries...')

        # Create delivery from the DONE deal
        done_deals = [d for d in created_deals if d.status == Deal.Status.DONE]
        created_deliveries = []
        
        for done_deal in done_deals:
            # Check if deal is DONE and no deliveries have been created yet
            # delivery_count is the planned count (default is 1), so we check actual count
            if done_deal.status == Deal.Status.DONE and done_deal.deliveries.count() == 0:
                # Get driver information from deal
                driver_profile = None
                driver_name = None
                driver_phone = None
                driver_vehicle_type = None
                driver_vehicle_plate = None
                driver_license_number = None
                
                if done_deal.driver:
                    driver_profile = done_deal.driver
                    driver_name = done_deal.driver.user.get_full_name() or done_deal.driver.user.username
                    driver_phone = done_deal.driver.user.phone_number
                    driver_vehicle_type = done_deal.driver.vehicle_type
                    driver_vehicle_plate = done_deal.driver.vehicle_plate
                    driver_license_number = done_deal.driver.license_number
                
                # Get delivery address and note from deal data (stored separately for sample data)
                delivery_address = 'Alsancak Cad. No:30, Konak, Izmir'  # From deal data
                delivery_note = 'Regular delivery'  # From deal data
                
                # Set driver information based on delivery_handler
                if done_deal.delivery_handler == Deal.DeliveryHandler.SYSTEM_DRIVER:
                    # Use system driver - only set driver_profile, not manual fields
                    final_driver_profile = driver_profile
                    final_driver_name = None
                    final_driver_phone = None
                    final_driver_vehicle_type = None
                    final_driver_vehicle_plate = None
                    final_driver_license_number = None
                else:
                    # For 3rd party deliveries, all driver fields are None
                    final_driver_profile = None
                    final_driver_name = None
                    final_driver_phone = None
                    final_driver_vehicle_type = None
                    final_driver_vehicle_plate = None
                    final_driver_license_number = None
                
                delivery = Delivery.objects.create(
                    deal=done_deal,
                    supplier_share=100,  # Default: all to supplier
                    driver_profile=final_driver_profile,
                    driver_name=final_driver_name,
                    driver_phone=final_driver_phone,
                    driver_vehicle_type=final_driver_vehicle_type,
                    driver_vehicle_plate=final_driver_vehicle_plate,
                    driver_license_number=final_driver_license_number,
                    delivery_address=delivery_address,
                    delivery_note=delivery_note,
                    status=Delivery.Status.ESTIMATED,  # Default status is now ESTIMATED
                    created_by=done_deal.created_by if hasattr(done_deal, 'created_by') and done_deal.created_by else done_deal.seller.user
                )
                
                # Create delivery items from deal items
                for deal_item in done_deal.items.all():
                    DeliveryItem.objects.create(
                        delivery=delivery,
                        product=deal_item.product,
                        quantity=deal_item.quantity,
                        unit_price=deal_item.unit_price,
                        created_by=done_deal.created_by if hasattr(done_deal, 'created_by') and done_deal.created_by else done_deal.seller.user
                    )
                
                # Calculate total
                # Note: delivery_count is now the planned count, not actual count
                # Actual count is tracked via deal.deliveries.count()
                delivery.calculate_total()
                created_deliveries.append(delivery)
                self.stdout.write(f'  Created: Delivery #{delivery.id} from Deal #{done_deal.id}')

        # Note: Standalone deliveries are not supported anymore
        # All deliveries must be created from deals
        # If you need a standalone delivery, create a deal first, then complete it

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
                f'   - Driver Requests: {len(created_requests)}\n'
                f'   - Deliveries: {len(created_deliveries)}\n\n'
                f'Default password for all sample users: sample123'
            )
        )
