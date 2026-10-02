from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ProductViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r"product", ProductViewSet, basename="product")

product_router = NestedDefaultRouter(
    router,
    r"product",
    lookup="product",
    trailing_slash=False
)
product_router.register(
    r"reviews",
    ReviewViewSet,
    basename="product-review",
)

urlpatterns = router.urls + product_router.urls