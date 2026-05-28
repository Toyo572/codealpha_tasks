from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, TruncMonth


def get_daily_sales_report(date=None):
    """
    Returns sales summary for a given date (defaults to today).
    """
    from orders.models import Order

    if date is None:
        date = timezone.localdate()

    orders = Order.objects.filter(
        created_at__date=date,
        status=Order.Status.COMPLETED,
    )

    summary = orders.aggregate(
        total_orders=Count("id"),
        total_revenue=Sum("total"),
        total_tax=Sum("tax"),
        total_discount=Sum("discount"),
        average_order_value=Avg("total"),
    )

    # Per order type breakdown
    by_type = (
        orders.values("order_type")
        .annotate(count=Count("id"), revenue=Sum("total"))
        .order_by("order_type")
    )

    # Top selling items for the day
    from orders.models import OrderItem
    top_items = (
        OrderItem.objects.filter(order__in=orders)
        .values("menu_item__name")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("subtotal"))
        .order_by("-total_quantity")[:10]
    )

    return {
        "date": str(date),
        "summary": {
            "total_orders": summary["total_orders"] or 0,
            "total_revenue": summary["total_revenue"] or Decimal("0.00"),
            "total_tax": summary["total_tax"] or Decimal("0.00"),
            "total_discount": summary["total_discount"] or Decimal("0.00"),
            "average_order_value": summary["average_order_value"] or Decimal("0.00"),
        },
        "by_order_type": list(by_type),
        "top_selling_items": list(top_items),
    }


def get_monthly_sales_report(year=None, month=None):
    """
    Returns daily breakdowns and totals for a given month.
    """
    from orders.models import Order

    today = timezone.localdate()
    year = year or today.year
    month = month or today.month

    orders = Order.objects.filter(
        created_at__year=year,
        created_at__month=month,
        status=Order.Status.COMPLETED,
    )

    summary = orders.aggregate(
        total_orders=Count("id"),
        total_revenue=Sum("total"),
        average_order_value=Avg("total"),
    )

    daily_breakdown = (
        orders.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(orders=Count("id"), revenue=Sum("total"))
        .order_by("day")
    )

    return {
        "year": year,
        "month": month,
        "summary": {
            "total_orders": summary["total_orders"] or 0,
            "total_revenue": summary["total_revenue"] or Decimal("0.00"),
            "average_order_value": summary["average_order_value"] or Decimal("0.00"),
        },
        "daily_breakdown": [
            {"day": str(d["day"]), "orders": d["orders"], "revenue": d["revenue"]}
            for d in daily_breakdown
        ],
    }


def get_low_stock_alerts():
    """
    Returns inventory items that are at or below their low stock threshold.
    """
    from inventory.models import InventoryItem
    from django.db.models import F

    low_stock_items = InventoryItem.objects.filter(
        quantity_in_stock__lte=F("low_stock_threshold")
    ).values(
        "id", "name", "unit", "quantity_in_stock", "low_stock_threshold", "supplier"
    )

    return {
        "alert_count": low_stock_items.count(),
        "items": list(low_stock_items),
    }


def get_inventory_valuation():
    """
    Returns total inventory value and per-item breakdown.
    """
    from inventory.models import InventoryItem

    items = InventoryItem.objects.annotate(
        value=F("quantity_in_stock") * F("unit_cost")
    ).values("id", "name", "unit", "quantity_in_stock", "unit_cost", "value")

    total_value = sum(item["value"] or 0 for item in items)

    return {
        "total_inventory_value": total_value,
        "items": list(items),
    }


def get_table_utilization_report(date=None):
    """
    Returns reservation and occupancy stats for a given date.
    """
    from tables.models import Reservation, Table

    if date is None:
        date = timezone.localdate()

    reservations = Reservation.objects.filter(reserved_date=date)

    summary = reservations.aggregate(
        total_reservations=Count("id"),
        confirmed=Count("id", filter=Q(status="confirmed")),
        completed=Count("id", filter=Q(status="completed")),
        cancelled=Count("id", filter=Q(status="cancelled")),
        no_show=Count("id", filter=Q(status="no_show")),
    )

    total_tables = Table.objects.count()

    return {
        "date": str(date),
        "total_tables": total_tables,
        "reservations": summary,
    }