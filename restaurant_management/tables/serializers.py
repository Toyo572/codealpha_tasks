from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.utils import timezone
from core.base_serializers import TimestampedModelSerializer
from .models import Table, Reservation
from .availability import check_table_availability


class TableSerializer(TimestampedModelSerializer):

    is_available = serializers.SerializerMethodField()

    @extend_schema_field(serializers.BooleanField())
    def get_is_available(self, obj):
        return obj.status == Table.Status.AVAILABLE

    class Meta:
        model = Table
        fields = [
            "id",
            "number",
            "capacity",
            "status",
            "location",
            "is_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_available", "created_at", "updated_at"]


class TableStatusSerializer(serializers.ModelSerializer):
    """
    Staff/admin use this to mark a table occupied/available/maintenance.
    When marking occupied, date/time/duration/customer_name are required
    so availability checks can block that window for other bookings.
    """
    customer_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    occupied_date = serializers.DateField(write_only=True, required=False)
    occupied_time = serializers.TimeField(write_only=True, required=False)
    duration_minutes = serializers.IntegerField(write_only=True, required=False, default=60)
    notes = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Table
        fields = ["id", "status", "customer_name", "occupied_date", "occupied_time", "duration_minutes", "notes"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs.get("status") == Table.Status.OCCUPIED:
            for field in ("customer_name", "occupied_date", "occupied_time"):
                if not attrs.get(field):
                    raise serializers.ValidationError(
                        {field: f"{field} is required when marking a table as occupied."}
                    )
        return attrs

    def update(self, instance, validated_data):
        from tables.models import TableOccupancy
        customer_name = validated_data.pop("customer_name", None)
        occupied_date = validated_data.pop("occupied_date", None)
        occupied_time = validated_data.pop("occupied_time", None)
        duration_minutes = validated_data.pop("duration_minutes", 60)
        notes = validated_data.pop("notes", "")

        instance = super().update(instance, validated_data)

        if instance.status == Table.Status.OCCUPIED and occupied_date and occupied_time:
            TableOccupancy.objects.create(
                table=instance,
                customer_name=customer_name,
                occupied_date=occupied_date,
                occupied_time=occupied_time,
                duration_minutes=duration_minutes,
                notes=notes,
                created_by=self.context["request"].user,
            )
        return instance


class TableOccupancySerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source="table.number", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = None  # set dynamically below
        fields = [
            "id", "table", "table_number", "customer_name",
            "occupied_date", "occupied_time", "duration_minutes",
            "notes", "created_by_email", "created_at",
        ]
        read_only_fields = ["id", "table_number", "created_by_email", "created_at"]

    def __init__(self, *args, **kwargs):
        from tables.models import TableOccupancy
        self.Meta.model = TableOccupancy
        super().__init__(*args, **kwargs)


class ReservationSerializer(TimestampedModelSerializer):

    table_number = serializers.IntegerField(source="table.number", read_only=True)
    table_capacity = serializers.IntegerField(source="table.capacity", read_only=True)
    customer_email_display = serializers.CharField(
        source="customer.email", read_only=True, default=None
    )

    class Meta:
        model = Reservation
        fields = [
            "id",
            "table",
            "table_number",
            "table_capacity",
            "customer",
            "customer_email_display",
            "customer_name",
            "customer_phone",
            "customer_email",
            "party_size",
            "reserved_date",
            "reserved_time",
            "duration_minutes",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "table_number",
            "table_capacity",
            "customer_email_display",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        table = attrs.get("table", getattr(self.instance, "table", None))
        reserved_date = attrs.get(
            "reserved_date", getattr(self.instance, "reserved_date", None)
        )
        reserved_time = attrs.get(
            "reserved_time", getattr(self.instance, "reserved_time", None)
        )
        party_size = attrs.get(
            "party_size", getattr(self.instance, "party_size", None)
        )
        duration_minutes = attrs.get("duration_minutes", 90)

        if reserved_date and reserved_date < timezone.localdate():
            raise serializers.ValidationError(
                {"reserved_date": "Cannot make a reservation in the past."}
            )

        if table and party_size and table.capacity < party_size:
            raise serializers.ValidationError(
                {
                    "party_size": (
                        f"Table {table.number} has capacity for {table.capacity} "
                        f"guests, but party size is {party_size}."
                    )
                }
            )

        if table and reserved_date and reserved_time:
            exclude_id = self.instance.pk if self.instance else None
            is_available, message = check_table_availability(
                table, reserved_date, reserved_time, duration_minutes, exclude_id
            )
            if not is_available:
                raise serializers.ValidationError({"table": message})

        return attrs

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)


class AvailableTablesQuerySerializer(serializers.Serializer):
    """Staff/admin: check availability for a specific date + time slot."""
    date = serializers.DateField()
    time = serializers.TimeField()
    party_size = serializers.IntegerField(min_value=1)
    duration_minutes = serializers.IntegerField(default=90, min_value=15)


class AvailableTablesByDateQuerySerializer(serializers.Serializer):
    """Customer-facing: check which tables are available on a date and for how many people."""
    date = serializers.DateField()
    party_size = serializers.IntegerField(min_value=1)


class BlockedWindowSerializer(serializers.Serializer):
    from_time = serializers.CharField(source="from")
    until = serializers.CharField()
    reason = serializers.CharField()


class TableAvailabilityByDateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.IntegerField()
    capacity = serializers.IntegerField()
    location = serializers.CharField()
    blocked_windows = BlockedWindowSerializer(many=True)