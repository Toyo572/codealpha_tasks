from django.db import models
from django.conf import settings
from menu.models import MenuItem
from tables.models import Table


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        SERVED = "served", "Served"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class OrderType(models.TextChoices):
        DINE_IN = "dine_in", "Dine In"
        TAKEAWAY = "takeaway", "Takeaway"
        DELIVERY = "delivery", "Delivery"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    order_name = models.CharField(
        max_length=200,
        help_text="Name to identify this order (e.g. customer name or table label)",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    order_type = models.CharField(
        max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    notes = models.TextField(blank=True)
    delivery_address = models.TextField(blank=True)
    payment_account_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Auto-generated virtual account number for delivery payment",
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.order_number} — {self.status}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        import uuid
        from django.utils import timezone
        prefix = timezone.now().strftime("%Y%m%d")
        suffix = uuid.uuid4().hex[:6].upper()
        return f"ORD-{prefix}-{suffix}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = "order_items"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} (Order #{self.order.order_number})"

    def save(self, *args, **kwargs):
        self.unit_price = self.menu_item.price
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)