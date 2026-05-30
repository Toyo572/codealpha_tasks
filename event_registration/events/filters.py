import django_filters
from .models import Event


class EventFilter(django_filters.FilterSet):
    start_after = django_filters.DateTimeFilter(field_name="start_datetime", lookup_expr="gte")
    start_before = django_filters.DateTimeFilter(field_name="start_datetime", lookup_expr="lte")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    is_online = django_filters.BooleanFilter()
    status = django_filters.ChoiceFilter(choices=Event.Status.choices)
    category = django_filters.CharFilter(field_name="category__slug")

    class Meta:
        model = Event
        fields = ["status", "is_online", "category"]
