from rest_framework import serializers
from core.base_serializers import TimestampedModelSerializer
from .models import Category, MenuItem


class CategorySerializer(TimestampedModelSerializer):

    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "item_count", "created_at", "updated_at"]


class MenuItemSerializer(TimestampedModelSerializer):

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "image",
            "availability",
            "preparation_time",
            "calories",
            "is_vegetarian",
            "is_vegan",
            "is_gluten_free",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "category_name", "created_at", "updated_at"]


class MenuItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "category_name",
            "price",
            "availability",
            "preparation_time",
            "is_vegetarian",
            "is_vegan",
            "is_gluten_free",
        ]