"""
Management command to load market food categories.
Run this command after initial migrations to populate category data.

Usage:
    python manage.py load_categories
    python manage.py load_categories --reset  # Reset and reload all categories
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from src.products.models import Category


class Command(BaseCommand):
    help = 'Load market food categories into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing categories before loading new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Deleting all existing categories...'))
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All categories deleted.'))

        self.stdout.write(self.style.SUCCESS('Loading market food categories...'))

        categories_data = [
            # Main Categories
            {
                'name': 'Citrus Fruits',
                'name_tr': 'Turunçgiller',
                'slug': 'citrus-fruits',
                'description': 'Citrus fruits like oranges, lemons, tangerines, grapefruits',
                'parent': None,
            },
            {
                'name': 'Vegetables',
                'name_tr': 'Sebzeler',
                'slug': 'vegetables',
                'description': 'Fresh vegetables including leafy greens, root vegetables, and more',
                'parent': None,
            },
            {
                'name': 'Fruits',
                'name_tr': 'Meyveler',
                'slug': 'fruits',
                'description': 'Fresh fruits including seasonal and tropical fruits',
                'parent': None,
            },
            {
                'name': 'Legumes',
                'name_tr': 'Baklagiller',
                'slug': 'legumes',
                'description': 'Dried legumes like beans, lentils, chickpeas',
                'parent': None,
            },
            {
                'name': 'Grains',
                'name_tr': 'Tahıllar',
                'slug': 'grains',
                'description': 'Grains and cereals like rice, wheat, bulgur, pasta',
                'parent': None,
            },
            {
                'name': 'Dairy Products',
                'name_tr': 'Süt Ürünleri',
                'slug': 'dairy-products',
                'description': 'Dairy products including milk, cheese, yogurt, butter',
                'parent': None,
            },
            {
                'name': 'Meat and Meat Products',
                'name_tr': 'Et ve Et Ürünleri',
                'slug': 'meat-products',
                'description': 'Fresh meat and meat products including beef, lamb, chicken, turkey',
                'parent': None,
            },
            {
                'name': 'Fish and Seafood',
                'name_tr': 'Balık ve Deniz Ürünleri',
                'slug': 'fish-seafood',
                'description': 'Fresh fish and seafood products',
                'parent': None,
            },
            {
                'name': 'Nuts and Dried Fruits',
                'name_tr': 'Kuruyemiş ve Kuru Meyveler',
                'slug': 'nuts-dried-fruits',
                'description': 'Nuts, seeds, and dried fruits',
                'parent': None,
            },
            {
                'name': 'Spices and Herbs',
                'name_tr': 'Baharatlar ve Otlar',
                'slug': 'spices-herbs',
                'description': 'Spices, herbs, and seasonings',
                'parent': None,
            },
            {
                'name': 'Bakery Products',
                'name_tr': 'Unlu Mamuller',
                'slug': 'bakery-products',
                'description': 'Bread, pastries, and bakery products',
                'parent': None,
            },
            {
                'name': 'Beverages',
                'name_tr': 'İçecekler',
                'slug': 'beverages',
                'description': 'Non-alcoholic beverages including juices, soft drinks, water',
                'parent': None,
            },
            {
                'name': 'Oils and Fats',
                'name_tr': 'Yağlar',
                'slug': 'oils-fats',
                'description': 'Cooking oils, olive oil, butter, margarine',
                'parent': None,
            },
            {
                'name': 'Honey and Natural Products',
                'name_tr': 'Bal ve Doğal Ürünler',
                'slug': 'honey-natural',
                'description': 'Honey, natural sweeteners, and organic products',
                'parent': None,
            },
        ]

        # Sub-categories for Vegetables
        vegetable_subcategories = [
            {
                'name': 'Leafy Vegetables',
                'name_tr': 'Yapraklı Sebzeler',
                'slug': 'leafy-vegetables',
                'description': 'Spinach, lettuce, arugula, cabbage, kale',
                'parent_slug': 'vegetables',
            },
            {
                'name': 'Root Vegetables',
                'name_tr': 'Kök Sebzeler',
                'slug': 'root-vegetables',
                'description': 'Carrots, potatoes, onions, garlic, beets, radishes',
                'parent_slug': 'vegetables',
            },
            {
                'name': 'Nightshade Vegetables',
                'name_tr': 'Solanaceae Sebzeleri',
                'slug': 'nightshade-vegetables',
                'description': 'Tomatoes, peppers, eggplants',
                'parent_slug': 'vegetables',
            },
            {
                'name': 'Cucurbitaceae',
                'name_tr': 'Kabakgiller',
                'slug': 'cucurbitaceae',
                'description': 'Cucumbers, zucchinis, pumpkins, melons',
                'parent_slug': 'vegetables',
            },
        ]

        # Sub-categories for Fruits
        fruit_subcategories = [
            {
                'name': 'Stone Fruits',
                'name_tr': 'Sert Çekirdekli Meyveler',
                'slug': 'stone-fruits',
                'description': 'Peaches, plums, apricots, cherries',
                'parent_slug': 'fruits',
            },
            {
                'name': 'Berries',
                'name_tr': 'Çilek ve Böğürtlen',
                'slug': 'berries',
                'description': 'Strawberries, raspberries, blackberries, blueberries',
                'parent_slug': 'fruits',
            },
            {
                'name': 'Tropical Fruits',
                'name_tr': 'Tropikal Meyveler',
                'slug': 'tropical-fruits',
                'description': 'Bananas, pineapples, mangoes, avocados',
                'parent_slug': 'fruits',
            },
        ]

        # Sub-categories for Meat
        meat_subcategories = [
            {
                'name': 'Red Meat',
                'name_tr': 'Kırmızı Et',
                'slug': 'red-meat',
                'description': 'Beef, lamb, veal',
                'parent_slug': 'meat-products',
            },
            {
                'name': 'Poultry',
                'name_tr': 'Kanatlı Hayvan Etleri',
                'slug': 'poultry',
                'description': 'Chicken, turkey, duck',
                'parent_slug': 'meat-products',
            },
            {
                'name': 'Processed Meat',
                'name_tr': 'İşlenmiş Et Ürünleri',
                'slug': 'processed-meat',
                'description': 'Sausages, salami, pastrami',
                'parent_slug': 'meat-products',
            },
        ]

        # Sub-categories for Dairy
        dairy_subcategories = [
            {
                'name': 'Milk and Cream',
                'name_tr': 'Süt ve Krema',
                'slug': 'milk-cream',
                'description': 'Fresh milk, cream, buttermilk',
                'parent_slug': 'dairy-products',
            },
            {
                'name': 'Cheese',
                'name_tr': 'Peynir',
                'slug': 'cheese',
                'description': 'Various types of cheese',
                'parent_slug': 'dairy-products',
            },
            {
                'name': 'Yogurt and Fermented Products',
                'name_tr': 'Yoğurt ve Fermente Ürünler',
                'slug': 'yogurt-fermented',
                'description': 'Yogurt, kefir, ayran',
                'parent_slug': 'dairy-products',
            },
        ]

        # Create main categories
        created_count = 0
        updated_count = 0
        category_map = {}

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'parent': cat_data['parent'],
                    'is_active': True,
                }
            )
            
            if not created:
                # Update existing category
                category.name = cat_data['name']
                category.description = cat_data['description']
                category.is_active = True
                category.save()
                updated_count += 1
            else:
                created_count += 1
            
            category_map[cat_data['slug']] = category
            self.stdout.write(f'  {"Created" if created else "Updated"}: {category.name}')

        # Create sub-categories
        all_subcategories = [
            (vegetable_subcategories, 'vegetables'),
            (fruit_subcategories, 'fruits'),
            (meat_subcategories, 'meat-products'),
            (dairy_subcategories, 'dairy-products'),
        ]

        for subcategories, parent_slug in all_subcategories:
            parent = category_map.get(parent_slug)
            if not parent:
                continue

            for subcat_data in subcategories:
                subcategory, created = Category.objects.get_or_create(
                    slug=subcat_data['slug'],
                    defaults={
                        'name': subcat_data['name'],
                        'description': subcat_data['description'],
                        'parent': parent,
                        'is_active': True,
                    }
                )
                
                if not created:
                    subcategory.name = subcat_data['name']
                    subcategory.description = subcat_data['description']
                    subcategory.parent = parent
                    subcategory.is_active = True
                    subcategory.save()
                    updated_count += 1
                else:
                    created_count += 1
                
                self.stdout.write(f'  {"Created" if created else "Updated"}: {subcategory.name} (under {parent.name})')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully loaded categories! '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
