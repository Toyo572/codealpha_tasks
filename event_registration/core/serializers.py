from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer.  All project serializers extend this.
    Centralises any future cross-cutting field logic (e.g. audit timestamps).
    """
    pass
