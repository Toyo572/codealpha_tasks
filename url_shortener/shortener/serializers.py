from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import ShortenedURL
from .utils import generate_short_code


class ShortenedURLCreateSerializer(serializers.ModelSerializer):
    """Used when creating a new shortened URL."""

    class Meta:
        model = ShortenedURL
        fields = ("id", "original_url", "short_code", "created_at")
        read_only_fields = ("id", "short_code", "created_at")

    def create(self, validated_data):
        # Generate a unique short code
        while True:
            code = generate_short_code()
            if not ShortenedURL.objects.filter(short_code=code).exists():
                break
        validated_data["short_code"] = code
        return super().create(validated_data)


class ShortenedURLDetailSerializer(serializers.ModelSerializer):
    """Used for list and detail responses — includes hit count and owner."""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = ShortenedURL
        fields = (
            "id",
            "short_code",
            "short_url",
            "original_url",
            "hits",
            "owner_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    @extend_schema_field(serializers.URLField())
    def get_short_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/{obj.short_code}/")
        return f"/{obj.short_code}/"