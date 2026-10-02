from django.urls import re_path
from .views import BasketView

app_name = "basket"

urlpatterns = [
    re_path("^basket/?$", BasketView.as_view(), name="basket"),
]