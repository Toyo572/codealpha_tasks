from rest_framework import viewsets, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.mixins import SuccessResponseMixin
from core.permissions import IsStaffOrAdmin
from .models import InventoryItem, MenuItemIngredient, StockTransaction
from .serializers import (
    InventoryItemSerializer,
    MenuItemIngredientSerializer,
    StockTransactionSerializer,
    RestockSerializer,
)
from .filters import InventoryItemFilter, StockTransactionFilter


@extend_schema_view(
    list=extend_schema(tags=["Inventory"], summary="List all inventory items"),
    create=extend_schema(tags=["Inventory"], summary="Add inventory item"),
    retrieve=extend_schema(tags=["Inventory"], summary="Get inventory item"),
    partial_update=extend_schema(tags=["Inventory"], summary="Update inventory item"),
    destroy=extend_schema(tags=["Inventory"], summary="Delete inventory item"),
)
class InventoryItemViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for inventory items (stock).
    Staff/admin only. Supports restock shortcut and low-stock filter.
    """

    permission_classes = [IsStaffOrAdmin]
    serializer_class = InventoryItemSerializer
    filterset_class = InventoryItemFilter
    search_fields = ["name", "supplier"]
    ordering_fields = ["name", "quantity_in_stock", "updated_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return InventoryItem.objects.all()

    def get_serializer_class(self):
        if self.action == "restock":
            return RestockSerializer
        return InventoryItemSerializer

    @extend_schema(tags=["Inventory"], summary="Restock an inventory item")
    @action(methods=["post"], detail=True, url_path="restock")
    def restock(self, request, pk=None):
        item = self.get_object()
        serializer = RestockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity_before = item.quantity_in_stock
        item.quantity_in_stock += serializer.validated_data["quantity"]
        item.save(update_fields=["quantity_in_stock"])

        StockTransaction.objects.create(
            inventory_item=item,
            transaction_type=StockTransaction.TransactionType.RESTOCK,
            quantity=serializer.validated_data["quantity"],
            quantity_before=quantity_before,
            quantity_after=item.quantity_in_stock,
            performed_by=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        return self.get_success_response(InventoryItemSerializer(item).data)


@extend_schema_view(
    list=extend_schema(tags=["Inventory"], summary="List ingredient mappings"),
    create=extend_schema(tags=["Inventory"], summary="Map ingredient to menu item"),
    retrieve=extend_schema(tags=["Inventory"], summary="Get ingredient mapping"),
    partial_update=extend_schema(tags=["Inventory"], summary="Update ingredient quantity"),
    destroy=extend_schema(tags=["Inventory"], summary="Remove ingredient mapping"),
)
class MenuItemIngredientViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for mapping menu items to their ingredients (inventory items).
    Used to enable automatic stock deduction on order completion.
    """

    queryset = MenuItemIngredient.objects.select_related(
        "menu_item", "inventory_item"
    ).all()
    serializer_class = MenuItemIngredientSerializer
    permission_classes = [IsStaffOrAdmin]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


@extend_schema_view(
    list=extend_schema(tags=["Inventory"], summary="List stock transactions"),
    create=extend_schema(tags=["Inventory"], summary="Record a stock transaction"),
    retrieve=extend_schema(tags=["Inventory"], summary="Get transaction details"),
)
class StockTransactionViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for stock transaction history.
    Read-only for list/retrieve. Write access for manual adjustments.
    """

    serializer_class = StockTransactionSerializer
    permission_classes = [IsStaffOrAdmin]
    filterset_class = StockTransactionFilter
    search_fields = ["inventory_item__name", "reference"]
    ordering_fields = ["created_at", "transaction_type"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return StockTransaction.objects.select_related(
            "inventory_item", "performed_by"
        ).order_by("-created_at")
