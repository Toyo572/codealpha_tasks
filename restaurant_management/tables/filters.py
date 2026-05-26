import django_filters
from .models import Table, Reservation


class TableFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Table.Status.choices)
    location = django_filters.CharFilter(lookup_expr="icontains")
    min_capacity = django_filters.NumberFilter(field_name="capacity", lookup_expr="gte")

    class Meta:
        model = Table
        fields = ["status", "location", "min_capacity"]


class ReservationFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Reservation.Status.choices)
    reserved_date = django_filters.DateFilter()
    reserved_date_from = django_filters.DateFilter(field_name="reserved_date", lookup_expr="gte")
    reserved_date_to = django_filters.DateFilter(field_name="reserved_date", lookup_expr="lte")
    table = django_filters.NumberFilter(field_name="table__number")

    class Meta:
        model = Reservation
        fields = ["status", "reserved_date", "reserved_date_from", "reserved_date_to", "table"]