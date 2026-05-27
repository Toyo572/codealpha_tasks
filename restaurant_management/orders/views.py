from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.mixins import SuccessResponseMixin
from core.permissions import IsStaffOrAdmin
from .models import Order
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
    OrderPaymentSerializer,
)
from .processors import transition_order_status
from .filters import OrderFilter


@extend_schema_view(
    list=extend_schema(tags=["Orders"], summary="List orders"),
    create=extend_schema(tags=["Orders"], summary="Place a new order"),
    retrieve=extend_schema(tags=["Orders"], summary="Get order details"),
    partial_update=extend_schema(tags=["Orders"], summary="Update order (staff/admin)"),
    destroy=extend_schema(tags=["Orders"], summary="Delete order (admin only)"),
)
class OrderViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for orders.
    Customers see only their own orders. Staff/admin see all.
    Supports status transitions and payment updates via custom actions.
    """

    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter
    search_fields = ["order_number", "order_name", "customer__email", "customer__first_name"]
    ordering_fields = ["created_at", "status", "total", "order_type"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        user = self.request.user
        qs = Order.objects.select_related(
            "customer", "table"
        ).prefetch_related("items__menu_item").order_by("-created_at")
        if user.role in ("admin", "staff"):
            return qs
        return qs.filter(customer=user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "update_status":
            return OrderStatusUpdateSerializer
        if self.action == "update_payment":
            return OrderPaymentSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsStaffOrAdmin()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        # Re-fetch with all relations for the full response
        order = Order.objects.select_related(
            "customer", "table"
        ).prefetch_related("items__menu_item").get(pk=order.pk)
        return self.get_success_response(
            OrderSerializer(order).data, status.HTTP_201_CREATED
        )

    @extend_schema(tags=["Orders"], summary="Transition order status (staff/admin)")
    @action(methods=["patch"], detail=True, url_path="status")
    def update_status(self, request, pk=None):
        if request.user.role not in ("admin", "staff"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff or admin can update order status.")
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_order = transition_order_status(order, serializer.validated_data["status"])
        return self.get_success_response(OrderSerializer(updated_order).data)

    @extend_schema(tags=["Orders"], summary="Update payment status (staff/admin)")
    @action(methods=["patch"], detail=True, url_path="payment")
    def update_payment(self, request, pk=None):
        if request.user.role not in ("admin", "staff"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff or admin can update payment status.")
        order = self.get_object()
        serializer = OrderPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order.payment_status = serializer.validated_data["payment_status"]
        order.save(update_fields=["payment_status"])
        return self.get_success_response(OrderSerializer(order).data)