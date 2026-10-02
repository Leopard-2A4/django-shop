from django.urls import path
from .views import OrderListView, OrderDetailView, HistoryOrderView

urlpatterns = [
    path("orders", OrderListView.as_view(), name="orders_list"),
    path("order/<int:pk>", OrderDetailView.as_view(), name="detail1"),
    path("orders/<int:pk>", OrderDetailView.as_view(), name="detail2"),
    path("history-order", HistoryOrderView.as_view()),
]