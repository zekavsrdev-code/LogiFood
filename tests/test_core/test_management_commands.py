"""Tests for management commands (load_categories, load_sample_data, load_dev_data)."""
import pytest
from django.core.management import call_command

from apps.orders.models import Deal, Delivery
from apps.products.models import Category

pytestmark = pytest.mark.integration


@pytest.mark.django_db
class TestLoadCategories:
    def test_load_categories_runs_without_error(self):
        call_command("load_categories")
        assert Category.objects.filter(is_active=True).exists()

    def test_load_categories_reset_runs_without_error(self):
        call_command("load_categories")
        call_command("load_categories", reset=True)
        call_command("load_categories")
        assert Category.objects.filter(is_active=True).exists()


@pytest.mark.django_db
class TestLoadSampleData:
    def test_load_sample_data_requires_categories(self):
        Category.objects.all().delete()
        call_command("load_sample_data")
        assert not Deal.objects.exists()

    def test_load_sample_data_runs_after_load_categories(self):
        call_command("load_categories")
        call_command("load_sample_data")
        assert Deal.objects.exists()
        assert Category.objects.filter(is_active=True).exists()

    def test_load_sample_data_delivery_supplier_share_from_deal(self):
        call_command("load_categories")
        call_command("load_sample_data")
        done_deals = Deal.objects.filter(status=Deal.Status.DONE)
        for deal in done_deals:
            for d in deal.deliveries.all():
                assert d.supplier_share == deal.delivery_cost_split

    def test_load_sample_data_reset_runs_without_error(self):
        call_command("load_categories")
        call_command("load_sample_data")
        call_command("load_sample_data", reset=True)
        call_command("load_categories")
        call_command("load_sample_data")
        assert Deal.objects.exists()


@pytest.mark.django_db
class TestLoadDevData:
    def test_load_dev_data_runs_without_error(self):
        call_command("load_dev_data")
        assert Category.objects.filter(is_active=True).exists()
        assert Deal.objects.exists()

    def test_load_dev_data_reset_runs_without_error(self):
        call_command("load_dev_data")
        call_command("load_dev_data", reset=True)
        call_command("load_dev_data")
        assert Category.objects.filter(is_active=True).exists()
        assert Deal.objects.exists()
