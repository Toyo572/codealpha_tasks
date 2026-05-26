from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="orders.Order")
def deduct_inventory_on_order_complete(sender, instance, **kwargs):
    """
    When an order status changes to 'completed', automatically deduct
    the required ingredients from inventory based on MenuItemIngredient mappings.
    """
    from inventory.models import InventoryItem, MenuItemIngredient, StockTransaction

    if instance.status != "completed":
        return

    # Avoid re-processing: check if a deduction transaction already exists for this order
    already_processed = StockTransaction.objects.filter(
        reference=instance.order_number,
        transaction_type=StockTransaction.TransactionType.DEDUCTION,
    ).exists()

    if already_processed:
        return

    for order_item in instance.items.select_related("menu_item").all():
        ingredients = MenuItemIngredient.objects.filter(
            menu_item=order_item.menu_item
        ).select_related("inventory_item")

        for ingredient in ingredients:
            total_deduction = ingredient.quantity_per_serving * order_item.quantity
            inv_item = ingredient.inventory_item

            quantity_before = inv_item.quantity_in_stock
            inv_item.quantity_in_stock = max(
                inv_item.quantity_in_stock - total_deduction, 0
            )
            inv_item.save(update_fields=["quantity_in_stock"])

            StockTransaction.objects.create(
                inventory_item=inv_item,
                transaction_type=StockTransaction.TransactionType.DEDUCTION,
                quantity=total_deduction,
                quantity_before=quantity_before,
                quantity_after=inv_item.quantity_in_stock,
                reference=instance.order_number,
                notes=f"Auto-deducted for order #{instance.order_number}",
            )