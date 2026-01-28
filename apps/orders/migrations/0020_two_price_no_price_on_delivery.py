# Two-price system: (1) goods = Deal.calculate_total, (2) delivery_fee = RequestToDriver.final_price
# split by delivery_cost_split. No price on Delivery/DeliveryItem; DeliveryItem links to DealItem.

from django.db import migrations, models
import django.db.models.deletion


def backfill_delivery_item_deal_item(apps, schema_editor):
    DeliveryItem = apps.get_model('orders', 'DeliveryItem')
    DealItem = apps.get_model('orders', 'DealItem')
    for di in DeliveryItem.objects.select_related('delivery', 'product').all():
        deal_item = DealItem.objects.filter(
            deal_id=di.delivery.deal_id, product_id=di.product_id
        ).first()
        if deal_item:
            di.deal_item_id = deal_item.id
            di.save(update_fields=['deal_item_id'])
        else:
            di.delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0019_requesttodriver_driver_approved"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliveryitem",
            name="deal_item",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="delivery_items",
                to="orders.dealitem",
                verbose_name="Deal Item",
            ),
        ),
        migrations.RunPython(backfill_delivery_item_deal_item, noop),
        migrations.RemoveField(model_name="deliveryitem", name="product"),
        migrations.RemoveField(model_name="deliveryitem", name="unit_price"),
        migrations.AlterField(
            model_name="deliveryitem",
            name="deal_item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="delivery_items",
                to="orders.dealitem",
                verbose_name="Deal Item",
            ),
        ),
        migrations.RemoveField(model_name="delivery", name="total_amount"),
    ]
