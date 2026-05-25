from rest_framework import serializers


class TimestampedModelSerializer(serializers.ModelSerializer):
    """
    Base serializer that includes created_at and updated_at as read-only fields.
    Inherit from this for any model that has timestamp fields.
    """

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)