import django_filters
from .models import MenuItem, Category


class MenuItemFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    availability = django_filters.ChoiceFilter(choices=MenuItem.Availability.choices)
    is_vegetarian = django_filters.BooleanFilter()
    is_vegan = django_filters.BooleanFilter()
    is_gluten_free = django_filters.BooleanFilter()

    class Meta:
        model = MenuItem
        fields = [
            "category",
            "availability",
            "is_vegetarian",
            "is_vegan",
            "is_gluten_free",
            "min_price",
            "max_price",
        ]