from django.db import models
from django.conf import settings
from menu.models import MenuItem


class InventoryItem(models.Model):

    class Unit(models.TextChoices):
        KG = "kg", "Kilogram"
        GRAM = "g", "Gram"
        LITRE = "l", "Litre"
        ML = "ml", "Millilitre"
        PIECE = "pcs", "Piece"
        PORTION = "portion", "Portion"

    name = models.CharField(max_length=200, unique=True)
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.PIECE)
    quantity_in_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    low_stock_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=10,
        help_text="Alert will be raised when stock falls below this level.",
    )
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Cost per unit for reporting purposes."
    )
    supplier = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_items"
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.quantity_in_stock} {self.unit})"

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.low_stock_threshold

    @property
    def stock_value(self):
        return self.quantity_in_stock * self.unit_cost


class MenuItemIngredient(models.Model):
    """
    Links a menu item to the inventory items (ingredients) it uses,
    along with the quantity consumed per serving.
    """

    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.CASCADE, related_name="ingredients"
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT, related_name="used_in"
    )
    quantity_per_serving = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        db_table = "menu_item_ingredients"
        unique_together = [("menu_item", "inventory_item")]

    def __str__(self):
        return (
            f"{self.menu_item.name} uses {self.quantity_per_serving}"
            f" {self.inventory_item.unit} of {self.inventory_item.name}"
        )


class StockTransaction(models.Model):

    class TransactionType(models.TextChoices):
        RESTOCK = "restock", "Restock"
        DEDUCTION = "deduction", "Deduction (Order)"
        ADJUSTMENT = "adjustment", "Manual Adjustment"
        WASTAGE = "wastage", "Wastage"

    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    quantity_before = models.DecimalField(max_digits=12, decimal_places=3)
    quantity_after = models.DecimalField(max_digits=12, decimal_places=3)
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. Order number or restock reference",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_transactions",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stock_transactions"
        verbose_name = "Stock Transaction"
        verbose_name_plural = "Stock Transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.transaction_type}: {self.quantity} {self.inventory_item.unit}"
            f" of {self.inventory_item.name}"
        )