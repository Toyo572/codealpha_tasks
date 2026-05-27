from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.mixins import SuccessResponseMixin
from core.permissions import IsStaffOrAdminOrReadOnly
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer, MenuItemListSerializer
from .filters import MenuItemFilter


@extend_schema_view(
    list=extend_schema(tags=["Menu"], summary="List all categories"),
    create=extend_schema(tags=["Menu"], summary="Create a category (staff/admin)"),
    retrieve=extend_schema(tags=["Menu"], summary="Get category details"),
    partial_update=extend_schema(tags=["Menu"], summary="Update category (staff/admin)"),
    destroy=extend_schema(tags=["Menu"], summary="Delete category (staff/admin)"),
)
class CategoryViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for menu categories.
    Read access for all authenticated users; write access for staff/admin.
    """

    permission_classes = [IsStaffOrAdminOrReadOnly]
    serializer_class = CategorySerializer
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Category.objects.annotate(item_count=Count("items")).order_by("name")


@extend_schema_view(
    list=extend_schema(tags=["Menu"], summary="List menu items"),
    create=extend_schema(tags=["Menu"], summary="Create a menu item (staff/admin)"),
    retrieve=extend_schema(tags=["Menu"], summary="Get menu item details"),
    partial_update=extend_schema(tags=["Menu"], summary="Update menu item (staff/admin)"),
    destroy=extend_schema(tags=["Menu"], summary="Delete menu item (staff/admin)"),
)
class MenuItemViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for menu items.
    Supports filtering by category, price range, dietary preferences, and availability.
    """

    permission_classes = [IsStaffOrAdminOrReadOnly]
    filterset_class = MenuItemFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "created_at", "preparation_time"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return MenuItem.objects.select_related("category").order_by("category", "name")

    def get_serializer_class(self):
        if self.action == "list":
            return MenuItemListSerializer
        return MenuItemSerializer