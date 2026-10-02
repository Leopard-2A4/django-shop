from django.urls import path
from .views import (
    CategoriesView,
    CatalogView,
    PopularProductsView,
    LimitedProductsView,
    SalesView,
    BannersView,
)

app_name = "catalog"

urlpatterns = [
    path("categories", CategoriesView.as_view(), name="categories"),
    path("catalog", CatalogView.as_view(), name="catalog"),
    path("products/popular", PopularProductsView.as_view(), name="products-popular"),
    path("products/limited", LimitedProductsView.as_view(), name="products-limited"),
    path("sales", SalesView.as_view(), name="sales"),
    path("banners", BannersView.as_view(), name="banners"),
]