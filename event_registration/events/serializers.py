from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.utils.text import slugify
import uuid

from core.serializers import BaseSerializer
from accounts.serializers import UserSerializer
from .models import Event, EventCategory


class EventCategorySerializer(BaseSerializer):
    class Meta:
        model = EventCategory
        fields = ["id", "name", "slug", "description"]


class EventListSerializer(BaseSerializer):
    """Lightweight serializer for list views."""
    organizer = serializers.StringRelatedField()
    category = EventCategorySerializer(read_only=True)
    spots_remaining = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    @extend_schema_field(serializers.IntegerField())
    def get_spots_remaining(self, obj):
        return obj.spots_remaining

    @extend_schema_field(serializers.BooleanField())
    def get_is_full(self, obj):
        return obj.is_full

    class Meta:
        model = Event
        fields = [
            "id", "title", "slug", "organizer", "category",
            "location", "is_online", "banner_image",
            "start_datetime", "end_datetime", "capacity",
            "spots_remaining", "is_full", "price", "status", "tags",
        ]


class EventDetailSerializer(BaseSerializer):
    """Full serializer for detail views — includes organizer object."""
    organizer = UserSerializer(read_only=True)
    category = EventCategorySerializer(read_only=True)
    spots_remaining = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    @extend_schema_field(serializers.IntegerField())
    def get_spots_remaining(self, obj):
        return obj.spots_remaining

    @extend_schema_field(serializers.BooleanField())
    def get_is_full(self, obj):
        return obj.is_full

    class Meta:
        model = Event
        fields = [
            "id", "title", "slug", "description", "organizer", "category",
            "location", "is_online", "online_link", "banner_image",
            "start_datetime", "end_datetime", "capacity",
            "spots_remaining", "is_full", "price", "status",
            "tags", "created_at", "updated_at",
        ]


class EventWriteSerializer(BaseSerializer):
    """Used by organizers when creating or updating an event."""
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=EventCategory.objects.all(),
        source="category",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Event
        fields = [
            "title", "description", "category_id",
            "location", "is_online", "online_link", "banner_image",
            "start_datetime", "end_datetime", "capacity", "price",
            "status", "tags",
        ]

    def validate(self, attrs):
        start = attrs.get("start_datetime") or (
            self.instance.start_datetime if self.instance else None
        )
        end = attrs.get("end_datetime") or (
            self.instance.end_datetime if self.instance else None
        )
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_datetime": "End datetime must be after start datetime."}
            )
        if attrs.get("is_online") and not attrs.get("online_link"):
            if not (self.instance and self.instance.online_link):
                raise serializers.ValidationError(
                    {"online_link": "Online link is required for online events."}
                )
        return attrs

    def create(self, validated_data):
        validated_data["organizer"] = self.context["request"].user
        # Auto-generate a unique slug from the title
        base_slug = slugify(validated_data["title"])
        validated_data["slug"] = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        return super().create(validated_data)

    def to_representation(self, instance):
        return EventDetailSerializer(instance, context=self.context).data