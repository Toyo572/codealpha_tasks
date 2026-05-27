from rest_framework import serializers
from core.base_serializers import TimestampedModelSerializer
from menu.models import MenuItem
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):

    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    menu_item_price = serializers.DecimalField(
        source="menu_item.price", max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "menu_item_price",
            "quantity",
            "unit_price",
            "subtotal",
            "notes",
        ]
        read_only_fields = ["id", "menu_item_name", "menu_item_price", "unit_price", "subtotal"]

    def validate_menu_item(self, value):
        if value.availability != "available":
            raise serializers.ValidationError(
                f"'{value.name}' is currently not available."
            )
        return value


class OrderItemCreateSerializer(serializers.Serializer):
    """Used only inside OrderCreateSerializer for nested writes."""

    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate_menu_item(self, value):
        if value.availability != "available":
            raise serializers.ValidationError(
                f"'{value.name}' is currently not available."
            )
        return value


class OrderSerializer(TimestampedModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(
        source="customer.email", read_only=True, default=None
    )
    table_number = serializers.IntegerField(
        source="table.number", read_only=True, default=None
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "order_name",
            "customer",
            "customer_email",
            "table",
            "table_number",
            "order_type",
            "status",
            "payment_status",
            "payment_account_number",
            "notes",
            "delivery_address",
            "subtotal",
            "tax",
            "discount",
            "total",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "order_number",
            "customer",
            "customer_email",
            "table_number",
            "payment_account_number",
            "subtotal",
            "tax",
            "total",
            "created_at",
            "updated_at",
        ]


class OrderCreateSerializer(serializers.ModelSerializer):

    items = OrderItemCreateSerializer(many=True, write_only=True)
    discount = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=0, required=False
    )

    class Meta:
        model = Order
        fields = [
            "order_name",
            "table",
            "order_type",
            "notes",
            "delivery_address",
            "discount",
            "items",
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("An order must contain at least one item.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        # Only staff/admin can apply discounts
        if attrs.get("discount", 0) and user.role == "customer":
            raise serializers.ValidationError(
                {"discount": "Customers are not allowed to apply discounts."}
            )

        order_type = attrs.get("order_type", Order.OrderType.DINE_IN)
        if order_type == Order.OrderType.DELIVERY and not attrs.get("delivery_address"):
            raise serializers.ValidationError(
                {"delivery_address": "A delivery address is required for delivery orders."}
            )
        if order_type == Order.OrderType.DINE_IN and not attrs.get("table"):
            raise serializers.ValidationError(
                {"table": "A table must be assigned for dine-in orders."}
            )
        return attrs

    def create(self, validated_data):
        from .processors import calculate_order_totals, generate_payment_account
        items_data = validated_data.pop("items")
        validated_data["customer"] = self.context["request"].user
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            notes = item_data.pop("notes", "")
            OrderItem.objects.create(order=order, notes=notes, **item_data)

        calculate_order_totals(order)

        # Auto-assign virtual account number for delivery orders
        if order.order_type == Order.OrderType.DELIVERY:
            order.payment_account_number = generate_payment_account(order.order_number)
            order.save(update_fields=["payment_account_number"])

        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)


class OrderPaymentSerializer(serializers.Serializer):
    payment_status = serializers.ChoiceField(choices=Order.PaymentStatus.choices)