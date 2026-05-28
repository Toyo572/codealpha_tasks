from rest_framework import serializers


class DailySalesSummarySerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_tax = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=14, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=14, decimal_places=2)


class OrderTypeBreakdownSerializer(serializers.Serializer):
    order_type = serializers.CharField()
    count = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class TopSellingItemSerializer(serializers.Serializer):
    menu_item__name = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class DailySalesReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    summary = DailySalesSummarySerializer()
    by_order_type = OrderTypeBreakdownSerializer(many=True)
    top_selling_items = TopSellingItemSerializer(many=True)


class DailyBreakdownSerializer(serializers.Serializer):
    day = serializers.DateField()
    orders = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


class MonthlySalesSummarySerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=14, decimal_places=2)


class MonthlySalesReportSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    summary = MonthlySalesSummarySerializer()
    daily_breakdown = DailyBreakdownSerializer(many=True)


class LowStockItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    unit = serializers.CharField()
    quantity_in_stock = serializers.DecimalField(max_digits=12, decimal_places=3)
    low_stock_threshold = serializers.DecimalField(max_digits=10, decimal_places=3)
    supplier = serializers.CharField()


class LowStockAlertSerializer(serializers.Serializer):
    alert_count = serializers.IntegerField()
    items = LowStockItemSerializer(many=True)


class InventoryValuationItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    unit = serializers.CharField()
    quantity_in_stock = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    value = serializers.DecimalField(max_digits=14, decimal_places=2)


class InventoryValuationSerializer(serializers.Serializer):
    total_inventory_value = serializers.DecimalField(max_digits=16, decimal_places=2)
    items = InventoryValuationItemSerializer(many=True)


class ReservationStatsSerializer(serializers.Serializer):
    total_reservations = serializers.IntegerField()
    confirmed = serializers.IntegerField()
    completed = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    no_show = serializers.IntegerField()


class TableUtilizationSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_tables = serializers.IntegerField()
    reservations = ReservationStatsSerializer()


# ── Query param serializers ──────────────────────────────────────────────────

class DailyReportQuerySerializer(serializers.Serializer):
    date = serializers.DateField(
        required=False,
        help_text="Date in YYYY-MM-DD format. Defaults to today.",
    )


class MonthlyReportQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(
        required=False,
        help_text="Year (e.g. 2025). Defaults to current year.",
    )
    month = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=12,
        help_text="Month number 1–12. Defaults to current month.",
    )