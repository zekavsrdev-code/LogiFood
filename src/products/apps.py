from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.products'
    label = 'products'
    verbose_name = 'Ürünler'
