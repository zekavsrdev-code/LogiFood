# Generated manually - Remove stock field from Product

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0004_alter_category_options_alter_product_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(model_name="product", name="stock"),
    ]
