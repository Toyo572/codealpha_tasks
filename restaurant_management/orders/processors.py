from decimal import Decimal
from rest_framework.exceptions import ValidationError
from .models import Order, OrderItem

TAX_RATE = Decimal("0.075")  # 7.5% VAT


def generate_payment_account(order_number: str) -> str:
    """
    Generates a deterministic mock virtual account number for a delivery order.
    Format: 10-digit number starting with 9 (like Nigerian virtual accounts).
    In production, replace this with a real payment provider API call.
    """
    import hashlib
    hash_val = int(hashlib.md5(order_number.encode()).hexdigest(), 16)
    account = str(hash_val)[:9].zfill(9)
    return f"9{account}"


# Valid status transitions
VALID_TRANSITIONS = {
    Order.Status.PENDING: [Order.Status.CONFIRMED, Order.Status.CANCELLED],
    Order.Status.CONFIRMED: [Order.Status.PREPARING, Order.Status.CANCELLED],
    Order.Status.PREPARING: [Order.Status.READY, Order.Status.CANCELLED],
    Order.Status.READY: [Order.Status.SERVED],
    Order.Status.SERVED: [Order.Status.COMPLETED],
    Order.Status.COMPLETED: [],
    Order.Status.CANCELLED: [],
}


def calculate_order_totals(order: Order) -> Order:
    """
    Recalculate subtotal, tax, and total from order items.
    Saves and returns the updated order.
    """
    items = order.items.all()
    subtotal = sum(item.subtotal for item in items)
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
    total = subtotal + tax - order.discount

    order.subtotal = subtotal
    order.tax = tax
    order.total = total
    order.save(update_fields=["subtotal", "tax", "total"])
    return order


def transition_order_status(order: Order, new_status: str) -> Order:
    """
    Validate and apply a status transition.
    Raises ValidationError if the transition is not allowed.
    """
    allowed = VALID_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        raise ValidationError(
            {
                "status": (
                    f"Cannot transition order from '{order.status}' to '{new_status}'. "
                    f"Allowed transitions: {allowed or ['none']}"
                )
            }
        )
    order.status = new_status
    order.save(update_fields=["status"])

    # Trigger inventory deduction on completion
    if new_status == Order.Status.COMPLETED:
        _deduct_inventory_for_order(order)

    return order


def _deduct_inventory_for_order(order: Order):
    """
    Signal to inventory to deduct stock when an order is completed.
    Decoupled via Django signals (see inventory/signals.py).
    """
    from django.db.models.signals import post_save
    # The actual deduction is handled by inventory signals listening to Order status changes.
    # This function exists as a hook for future direct calls if needed.
    pass