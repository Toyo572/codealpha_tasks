from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from django.shortcuts import render
from drf_spectacular.utils import extend_schema


class EmptySerializer(serializers.Serializer):
    """Placeholder serializer — required so the view is consistent with the rest of the project."""
    pass


@extend_schema(exclude=True)
class FrontendAppView(GenericAPIView):
    """Serves the single-page frontend application. Excluded from API schema."""
    serializer_class = EmptySerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return render(request, "frontend/index.html")