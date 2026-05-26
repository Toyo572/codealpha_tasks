from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryItemViewSet, MenuItemIngredientViewSet, StockTransactionViewSet

router = DefaultRouter()
router.register("items", InventoryItemViewSet, basename="inventory-item")
router.register("ingredients", MenuItemIngredientViewSet, basename="ingredient")
router.register("transactions", StockTransactionViewSet, basename="stock-transaction")

urlpatterns = [
    path("", include(router.urls)),
]