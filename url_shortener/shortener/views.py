from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from drf_spectacular.utils import extend_schema

from .models import ShortenedURL
from .serializers import ShortenedURLCreateSerializer, ShortenedURLDetailSerializer


@extend_schema(tags=["URLs"])
class URLListCreateView(GenericAPIView):
    """
    GET  /api/urls/  — list the authenticated user's shortened URLs
    POST /api/urls/  — create a new shortened URL
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ShortenedURLCreateSerializer
        return ShortenedURLDetailSerializer

    def get_queryset(self):
        return ShortenedURL.objects.filter(owner=self.request.user)

    @extend_schema(
        summary="List all shortened URLs owned by the authenticated user",
        responses={200: ShortenedURLDetailSerializer(many=True)},
    )
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create a new shortened URL",
        request=ShortenedURLCreateSerializer,
        responses={201: ShortenedURLDetailSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(owner=request.user)
        return Response(
            ShortenedURLDetailSerializer(instance, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["URLs"])
class URLDetailView(GenericAPIView):
    """
    GET    /api/urls/<id>/  — retrieve a single shortened URL
    DELETE /api/urls/<id>/  — delete a shortened URL
    """
    serializer_class = ShortenedURLDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(ShortenedURL, pk=self.kwargs["pk"], owner=self.request.user)

    @extend_schema(summary="Retrieve a single shortened URL by ID")
    def get(self, request, pk):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary="Delete a shortened URL")
    def delete(self, request, pk):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Redirect"])
class RedirectView(GenericAPIView):
    """
    GET /<short_code>/  — resolves the short code and redirects to the original URL.
    This endpoint is public and does not require authentication.
    """
    serializer_class = ShortenedURLDetailSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="redirect_short_code",
        summary="Redirect a short code to its original URL",
        responses={302: None},
    )
    def get(self, request, short_code):
        url_obj = get_object_or_404(ShortenedURL, short_code=short_code)
        url_obj.hits += 1
        url_obj.save(update_fields=["hits"])
        return HttpResponseRedirect(url_obj.original_url)