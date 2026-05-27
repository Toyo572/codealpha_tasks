import django_filters
from .models import Order


class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.Status.choices)
    order_type = django_filters.ChoiceFilter(choices=Order.OrderType.choices)
    payment_status = django_filters.ChoiceFilter(choices=Order.PaymentStatus.choices)
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")
    min_total = django_filters.NumberFilter(field_name="total", lookup_expr="gte")
    max_total = django_filters.NumberFilter(field_name="total", lookup_expr="lte")

    class Meta:
        model = Order
        fields = ["status", "order_type", "payment_status", "date_from", "date_to", "min_total", "max_total"]