from django.urls import path
from .views import GetTagViewSet

app_name = "tag"

urlpatterns = [
    path("tags/", GetTagViewSet.as_view(), name="tags")
]