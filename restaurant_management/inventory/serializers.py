from decimal import Decimal
from rest_framework import serializers
from core.base_serializers import TimestampedModelSerializer
from .models import InventoryItem, MenuItemIngredient, StockTransaction


class InventoryItemSerializer(TimestampedModelSerializer):

    is_low_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "name",
            "unit",
            "quantity_in_stock",
            "low_stock_threshold",
            "unit_cost",
            "supplier",
            "notes",
            "is_low_stock",
            "stock_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_low_stock", "stock_value", "created_at", "updated_at"]


class MenuItemIngredientSerializer(serializers.ModelSerializer):

    inventory_item_name = serializers.CharField(
        source="inventory_item.name", read_only=True
    )
    inventory_item_unit = serializers.CharField(
        source="inventory_item.unit", read_only=True
    )
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = MenuItemIngredient
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "inventory_item",
            "inventory_item_name",
            "inventory_item_unit",
            "quantity_per_serving",
        ]
        read_only_fields = ["id", "menu_item_name", "inventory_item_name", "inventory_item_unit"]


class StockTransactionSerializer(serializers.ModelSerializer):

    inventory_item_name = serializers.CharField(
        source="inventory_item.name", read_only=True
    )
    performed_by_email = serializers.CharField(
        source="performed_by.email", read_only=True, default=None
    )

    class Meta:
        model = StockTransaction
        fields = [
            "id",
            "inventory_item",
            "inventory_item_name",
            "transaction_type",
            "quantity",
            "quantity_before",
            "quantity_after",
            "reference",
            "performed_by",
            "performed_by_email",
            "notes",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "inventory_item_name",
            "performed_by",
            "performed_by_email",
            "quantity_before",
            "quantity_after",
            "created_at",
        ]

    def create(self, validated_data):
        inv_item = validated_data["inventory_item"]
        qty = validated_data["quantity"]
        t_type = validated_data["transaction_type"]

        quantity_before = inv_item.quantity_in_stock

        if t_type == StockTransaction.TransactionType.RESTOCK:
            inv_item.quantity_in_stock += qty
        elif t_type in (
            StockTransaction.TransactionType.DEDUCTION,
            StockTransaction.TransactionType.WASTAGE,
        ):
            if inv_item.quantity_in_stock < qty:
                raise serializers.ValidationError(
                    {"quantity": f"Insufficient stock. Available: {inv_item.quantity_in_stock} {inv_item.unit}."}
                )
            inv_item.quantity_in_stock -= qty
        elif t_type == StockTransaction.TransactionType.ADJUSTMENT:
            inv_item.quantity_in_stock = qty

        inv_item.save(update_fields=["quantity_in_stock"])
        validated_data["quantity_before"] = quantity_before
        validated_data["quantity_after"] = inv_item.quantity_in_stock
        validated_data["performed_by"] = self.context["request"].user

        return super().create(validated_data)


class RestockSerializer(serializers.Serializer):
    """Quick restock shortcut — just supply quantity and optional note."""
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    notes = serializers.CharField(max_length=300, required=False, allow_blank=True)