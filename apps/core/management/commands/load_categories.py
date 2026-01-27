"""
Load market food categories. Used by load_dev_data.

Usage:
    python manage.py load_categories
    python manage.py load_categories --reset
"""
from django.core.management.base import BaseCommand
from src.products.models import Category


class Command(BaseCommand):
    help = "Load market food categories into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing categories before loading new ones",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Deleting all existing categories..."))
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("All categories deleted."))

        self.stdout.write(self.style.SUCCESS("Loading market food categories..."))

        categories_data = [
            {"name": "Citrus Fruits", "slug": "citrus-fruits", "description": "Citrus fruits like oranges, lemons, tangerines, grapefruits", "parent": None},
            {"name": "Vegetables", "slug": "vegetables", "description": "Fresh vegetables including leafy greens, root vegetables, and more", "parent": None},
            {"name": "Fruits", "slug": "fruits", "description": "Fresh fruits including seasonal and tropical fruits", "parent": None},
            {"name": "Legumes", "slug": "legumes", "description": "Dried legumes like beans, lentils, chickpeas", "parent": None},
            {"name": "Grains", "slug": "grains", "description": "Grains and cereals like rice, wheat, bulgur, pasta", "parent": None},
            {"name": "Dairy Products", "slug": "dairy-products", "description": "Dairy products including milk, cheese, yogurt, butter", "parent": None},
            {"name": "Meat and Meat Products", "slug": "meat-products", "description": "Fresh meat and meat products including beef, lamb, chicken, turkey", "parent": None},
            {"name": "Fish and Seafood", "slug": "fish-seafood", "description": "Fresh fish and seafood products", "parent": None},
            {"name": "Nuts and Dried Fruits", "slug": "nuts-dried-fruits", "description": "Nuts, seeds, and dried fruits", "parent": None},
            {"name": "Spices and Herbs", "slug": "spices-herbs", "description": "Spices, herbs, and seasonings", "parent": None},
            {"name": "Bakery Products", "slug": "bakery-products", "description": "Bread, pastries, and bakery products", "parent": None},
            {"name": "Beverages", "slug": "beverages", "description": "Non-alcoholic beverages including juices, soft drinks, water", "parent": None},
            {"name": "Oils and Fats", "slug": "oils-fats", "description": "Cooking oils, olive oil, butter, margarine", "parent": None},
            {"name": "Honey and Natural Products", "slug": "honey-natural", "description": "Honey, natural sweeteners, and organic products", "parent": None},
        ]

        subcategories_data = [
            ([{"name": "Leafy Vegetables", "slug": "leafy-vegetables", "description": "Spinach, lettuce, arugula, cabbage, kale"},
             {"name": "Root Vegetables", "slug": "root-vegetables", "description": "Carrots, potatoes, onions, garlic, beets, radishes"},
             {"name": "Nightshade Vegetables", "slug": "nightshade-vegetables", "description": "Tomatoes, peppers, eggplants"},
             {"name": "Cucurbitaceae", "slug": "cucurbitaceae", "description": "Cucumbers, zucchinis, pumpkins, melons"}], "vegetables"),
            ([{"name": "Stone Fruits", "slug": "stone-fruits", "description": "Peaches, plums, apricots, cherries"},
             {"name": "Berries", "slug": "berries", "description": "Strawberries, raspberries, blackberries, blueberries"},
             {"name": "Tropical Fruits", "slug": "tropical-fruits", "description": "Bananas, pineapples, mangoes, avocados"}], "fruits"),
            ([{"name": "Red Meat", "slug": "red-meat", "description": "Beef, lamb, veal"},
             {"name": "Poultry", "slug": "poultry", "description": "Chicken, turkey, duck"},
             {"name": "Processed Meat", "slug": "processed-meat", "description": "Sausages, salami, pastrami"}], "meat-products"),
            ([{"name": "Milk and Cream", "slug": "milk-cream", "description": "Fresh milk, cream, buttermilk"},
             {"name": "Cheese", "slug": "cheese", "description": "Various types of cheese"},
             {"name": "Yogurt and Fermented Products", "slug": "yogurt-fermented", "description": "Yogurt, kefir, ayran"}], "dairy-products"),
        ]

        created_count = 0
        updated_count = 0
        category_map = {}

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={"name": cat_data["name"], "description": cat_data["description"], "parent": cat_data["parent"], "is_active": True},
            )
            if not created:
                category.name = cat_data["name"]
                category.description = cat_data["description"]
                category.is_active = True
                category.save()
                updated_count += 1
            else:
                created_count += 1
            category_map[cat_data["slug"]] = category
            self.stdout.write(f'  {"Created" if created else "Updated"}: {category.name}')

        for sub_list, parent_slug in subcategories_data:
            parent = category_map.get(parent_slug)
            if not parent:
                continue
            for subcat_data in sub_list:
                subcategory, created = Category.objects.get_or_create(
                    slug=subcat_data["slug"],
                    defaults={"name": subcat_data["name"], "description": subcat_data["description"], "parent": parent, "is_active": True},
                )
                if not created:
                    subcategory.name = subcat_data["name"]
                    subcategory.description = subcat_data["description"]
                    subcategory.parent = parent
                    subcategory.is_active = True
                    subcategory.save()
                    updated_count += 1
                else:
                    created_count += 1
                self.stdout.write(f'  {"Created" if created else "Updated"}: {subcategory.name} (under {parent.name})')

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully loaded categories! Created: {created_count}, Updated: {updated_count}"))
