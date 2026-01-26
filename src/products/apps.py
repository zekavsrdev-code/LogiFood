from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.products'
    label = 'products'
    verbose_name = 'Ürünler'
    
    def ready(self):
        """Import signals when app is ready"""
        import src.products.signals  # noqa
