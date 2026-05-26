from django.db import models
from django.conf import settings


class Table(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        RESERVED = "reserved", "Reserved"
        MAINTENANCE = "maintenance", "Maintenance"

    number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. Indoor, Outdoor, Rooftop, VIP",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tables"
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        ordering = ["number"]

    def __str__(self):
        return f"Table {self.number} (capacity: {self.capacity})"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE


class TableOccupancy(models.Model):
    """
    Created by staff/admin when they manually mark a table as occupied.
    Stores the booking window so availability checks can exclude this table
    for that date/time range.
    """
    table = models.ForeignKey(
        Table, on_delete=models.CASCADE, related_name="occupancies"
    )
    customer_name = models.CharField(max_length=200)
    occupied_date = models.DateField()
    occupied_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="table_occupancies",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "table_occupancies"
        ordering = ["occupied_date", "occupied_time"]

    def __str__(self):
        return (
            f"Table {self.table.number} occupied by {self.customer_name} "
            f"on {self.occupied_date} at {self.occupied_time} "
            f"for {self.duration_minutes} mins"
        )


class Reservation(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SEATED = "seated", "Seated"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, related_name="reservations"
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
    )
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    party_size = models.PositiveIntegerField()
    reserved_date = models.DateField()
    reserved_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(
        default=90, help_text="Expected duration in minutes"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reservations"
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ["reserved_date", "reserved_time"]

    def __str__(self):
        return (
            f"Reservation for {self.customer_name} on "
            f"{self.reserved_date} at {self.reserved_time} — Table {self.table.number}"
        )