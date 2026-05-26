from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.mixins import SuccessResponseMixin
from core.permissions import IsStaffOrAdmin, IsStaffOrAdminOrReadOnly
from .models import Table, Reservation
from .serializers import (
    TableSerializer,
    TableStatusSerializer,
    ReservationSerializer,
    AvailableTablesQuerySerializer,
    AvailableTablesByDateQuerySerializer,
)
from .availability import get_available_tables, get_available_tables_by_date
from .filters import TableFilter, ReservationFilter


@extend_schema_view(
    list=extend_schema(tags=["Tables"], summary="List all tables"),
    create=extend_schema(tags=["Tables"], summary="Add a table (staff/admin)"),
    retrieve=extend_schema(tags=["Tables"], summary="Get table details"),
    partial_update=extend_schema(tags=["Tables"], summary="Update table (staff/admin)"),
    destroy=extend_schema(tags=["Tables"], summary="Remove table (staff/admin)"),
)
class TableViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for restaurant tables.
    Includes a custom action to check real-time availability.
    """

    queryset = Table.objects.all().order_by("number")
    permission_classes = [IsStaffOrAdminOrReadOnly]
    filterset_class = TableFilter
    search_fields = ["number", "location"]
    ordering_fields = ["number", "capacity", "status"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "update_status":
            return TableStatusSerializer
        if self.action in ("available", "available_by_date"):
            return AvailableTablesQuerySerializer
        return TableSerializer

    @extend_schema(
        tags=["Tables"],
        summary="Check available tables for a time slot",
        parameters=[AvailableTablesQuerySerializer],
    )
    @action(methods=["get"], detail=False, url_path="available")
    def available(self, request):
        query_serializer = AvailableTablesQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        tables = get_available_tables(
            date=params["date"],
            time=params["time"],
            party_size=params["party_size"],
            duration_minutes=params.get("duration_minutes", 90),
        )
        serializer = TableSerializer(tables, many=True)
        return self.get_success_response(serializer.data)

    @extend_schema(tags=["Tables"], summary="Update table status with booking details (staff/admin)")
    @action(methods=["patch"], detail=True, url_path="status",
            permission_classes=[IsStaffOrAdmin])
    def update_status(self, request, pk=None):
        table = self.get_object()
        serializer = TableStatusSerializer(
            table, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response(TableSerializer(table).data)

    @extend_schema(
        tags=["Tables"],
        summary="Check tables available on a specific date (customer view)",
        parameters=[AvailableTablesByDateQuerySerializer],
    )
    @action(methods=["get"], detail=False, url_path="available-by-date")
    def available_by_date(self, request):
        query = AvailableTablesByDateQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)  # returns 400 if date or party_size missing
        data = get_available_tables_by_date(
            date=query.validated_data["date"],
            party_size=query.validated_data["party_size"],
        )
        return self.get_success_response(data)


@extend_schema_view(
    list=extend_schema(tags=["Reservations"], summary="List reservations"),
    create=extend_schema(tags=["Reservations"], summary="Create a reservation"),
    retrieve=extend_schema(tags=["Reservations"], summary="Get reservation details"),
    partial_update=extend_schema(tags=["Reservations"], summary="Update reservation"),
    destroy=extend_schema(tags=["Reservations"], summary="Cancel/delete reservation"),
)
class ReservationViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for table reservations.
    Customers see only their own reservations. Staff/admin see all.
    """

    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ReservationFilter
    search_fields = ["customer_name", "customer_phone", "customer_email"]
    ordering_fields = ["reserved_date", "reserved_time", "status", "created_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Reservation.objects.none()
        user = self.request.user
        qs = Reservation.objects.select_related("table", "customer").order_by(
            "reserved_date", "reserved_time"
        )
        if user.role in ("admin", "staff"):
            return qs
        return qs.filter(customer=user)

    @extend_schema(tags=["Reservations"], summary="Update reservation status (staff/admin)")
    @action(methods=["patch"], detail=True, url_path="status")
    def update_status(self, request, pk=None):
        if request.user.role not in ("admin", "staff"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only staff or admin can update reservation status.")
        reservation = self.get_object()
        serializer = self.get_serializer(reservation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get_success_response(serializer.data)