import django_filters
from django.db.models import F
from .models import InventoryItem, StockTransaction


class InventoryItemFilter(django_filters.FilterSet):
    low_stock = django_filters.BooleanFilter(
        method="filter_low_stock",
        label="Show only low-stock items",
    )
    supplier = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = InventoryItem
        fields = ["low_stock", "supplier", "unit"]

    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(quantity_in_stock__lte=F("low_stock_threshold"))
        return queryset
    
class StockTransactionFilter(django_filters.FilterSet):
    from .models import StockTransaction
    transaction_type = django_filters.ChoiceFilter(choices=StockTransaction.TransactionType.choices)
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    class Meta:
        model = StockTransaction
        fields = ["transaction_type", "date_from", "date_to"]