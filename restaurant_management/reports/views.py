from rest_framework import viewsets
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.mixins import SuccessResponseMixin
from core.permissions import IsStaffOrAdmin
from .serializers import (
    DailySalesReportSerializer,
    MonthlySalesReportSerializer,
    LowStockAlertSerializer,
    InventoryValuationSerializer,
    TableUtilizationSerializer,
    DailyReportQuerySerializer,
    MonthlyReportQuerySerializer,
)
from .aggregators import (
    get_daily_sales_report,
    get_monthly_sales_report,
    get_low_stock_alerts,
    get_inventory_valuation,
    get_table_utilization_report,
)


@extend_schema_view(
    daily_sales=extend_schema(
        tags=["Reports"],
        summary="Daily sales report",
        parameters=[DailyReportQuerySerializer],
        responses={200: DailySalesReportSerializer},
    ),
    monthly_sales=extend_schema(
        tags=["Reports"],
        summary="Monthly sales report",
        parameters=[MonthlyReportQuerySerializer],
        responses={200: MonthlySalesReportSerializer},
    ),
    low_stock=extend_schema(
        tags=["Reports"],
        summary="Low stock alerts",
        responses={200: LowStockAlertSerializer},
    ),
    inventory_valuation=extend_schema(
        tags=["Reports"],
        summary="Total inventory valuation",
        responses={200: InventoryValuationSerializer},
    ),
    table_utilization=extend_schema(
        tags=["Reports"],
        summary="Table utilization & reservation stats",
        parameters=[DailyReportQuerySerializer],
        responses={200: TableUtilizationSerializer},
    ),
)
class ReportViewSet(SuccessResponseMixin, viewsets.GenericViewSet):
    """
    Reports ViewSet — all endpoints are read-only custom actions.
    Staff and admin access only.
    """

    permission_classes = [IsStaffOrAdmin]

    def get_queryset(self):
        # Required by router but this ViewSet has no backing model
        if getattr(self, "swagger_fake_view", False):
            from orders.models import Order
            return Order.objects.none()
        return []

    def get_serializer_class(self):
        serializer_map = {
            "daily_sales": DailySalesReportSerializer,
            "monthly_sales": MonthlySalesReportSerializer,
            "low_stock": LowStockAlertSerializer,
            "inventory_valuation": InventoryValuationSerializer,
            "table_utilization": TableUtilizationSerializer,
        }
        return serializer_map.get(self.action, DailySalesReportSerializer)

    @action(methods=["get"], detail=False, url_path="daily-sales")
    def daily_sales(self, request):
        query = DailyReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        date = query.validated_data.get("date")
        data = get_daily_sales_report(date=date)
        serializer = DailySalesReportSerializer(data)
        return self.get_success_response(serializer.data)

    @action(methods=["get"], detail=False, url_path="monthly-sales")
    def monthly_sales(self, request):
        query = MonthlyReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = get_monthly_sales_report(
            year=query.validated_data.get("year"),
            month=query.validated_data.get("month"),
        )
        serializer = MonthlySalesReportSerializer(data)
        return self.get_success_response(serializer.data)

    @action(methods=["get"], detail=False, url_path="low-stock")
    def low_stock(self, request):
        data = get_low_stock_alerts()
        serializer = LowStockAlertSerializer(data)
        return self.get_success_response(serializer.data)

    @action(methods=["get"], detail=False, url_path="inventory-valuation")
    def inventory_valuation(self, request):
        data = get_inventory_valuation()
        serializer = InventoryValuationSerializer(data)
        return self.get_success_response(serializer.data)

    @action(methods=["get"], detail=False, url_path="table-utilization")
    def table_utilization(self, request):
        query = DailyReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        date = query.validated_data.get("date")
        data = get_table_utilization_report(date=date)
        serializer = TableUtilizationSerializer(data)
        return self.get_success_response(serializer.data)