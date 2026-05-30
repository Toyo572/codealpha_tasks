from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.utils import timezone
from events.models import Event
from core.serializers import BaseSerializer
from events.serializers import EventListSerializer
from .models import Registration


class RegistrationSerializer(BaseSerializer):
    """Used for creating a registration and reading registration data."""
    event_detail = EventListSerializer(source="event", read_only=True)
    attendee_email = serializers.SerializerMethodField()
    attendee_name = serializers.SerializerMethodField()

    @extend_schema_field(serializers.EmailField())
    def get_attendee_email(self, obj):
        return obj.attendee.email

    @extend_schema_field(serializers.CharField())
    def get_attendee_name(self, obj):
        return obj.attendee.full_name

    class Meta:
        model = Registration
        fields = [
            "id", "event", "event_detail",
            "attendee_email", "attendee_name",
            "status", "notes",
            "registered_at", "updated_at", "cancelled_at",
        ]
        read_only_fields = [
            "id", "status", "registered_at", "updated_at", "cancelled_at",
            "event_detail", "attendee_email", "attendee_name",
        ]

    def validate_event(self, event):
        if event.status != Event.Status.PUBLISHED:
            raise serializers.ValidationError("You can only register for published events.")
        user = self.context["request"].user
        if Registration.objects.filter(attendee=user, event=event).exists():
            raise serializers.ValidationError("You are already registered for this event.")
        if event.is_full:
            raise serializers.ValidationError(
                "This event is fully booked. No spots remaining."
            )
        return event

    def create(self, validated_data):
        validated_data["attendee"] = self.context["request"].user
        return super().create(validated_data)


class RegistrationCancelSerializer(BaseSerializer):
    """Serializer used purely for the cancel action — accepts no input, just confirms intent."""
    confirm = serializers.BooleanField(
        write_only=True,
        help_text="Must be true to confirm cancellation.",
    )

    class Meta:
        model = Registration
        fields = ["confirm"]

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm the cancellation.")
        return value

    def validate(self, attrs):
        registration = self.context["registration"]
        if registration.status == Registration.Status.CANCELLED:
            raise serializers.ValidationError(
                {"confirm": "This registration is already cancelled."}
            )
        return attrs

    def save(self, **kwargs):
        registration = self.context["registration"]
        registration.status = Registration.Status.CANCELLED
        registration.cancelled_at = timezone.now()
        registration.save(update_fields=["status", "cancelled_at", "updated_at"])
        return registration


class OrganizerRegistrationSerializer(BaseSerializer):
    """Read-only serializer for organizers to view registrations on their events."""
    attendee_email = serializers.SerializerMethodField()
    attendee_name = serializers.SerializerMethodField()
    event_title = serializers.SerializerMethodField()

    @extend_schema_field(serializers.EmailField())
    def get_attendee_email(self, obj):
        return obj.attendee.email

    @extend_schema_field(serializers.CharField())
    def get_attendee_name(self, obj):
        return obj.attendee.full_name

    @extend_schema_field(serializers.CharField())
    def get_event_title(self, obj):
        return obj.event.title

    class Meta:
        model = Registration
        fields = [
            "id", "event_title", "attendee_email", "attendee_name",
            "status", "notes", "registered_at", "cancelled_at",
        ]