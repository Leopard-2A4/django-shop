from django.contrib.auth.models import User
from django.db import models
from orders.models import Order
from django.utils import timezone

class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    PAYMENT_TYPE_CARD = "card"
    PAYMENT_TYPE_RANDOM = "random"

    PAYMENT_TYPE_CHOICES = [
        (PAYMENT_TYPE_CARD, "Online card"),
        (PAYMENT_TYPE_RANDOM, "Online random account"),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
    )
    number = models.CharField(max_length=8)  # номер карты/счёта
    name = models.CharField(max_length=100)  # имя владельца
    month = models.CharField(max_length=2)  # месяц
    year = models.CharField(max_length=4)  # год
    # code не храним в БД (security) — только для валидации

    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPE_CHOICES,
        default=PAYMENT_TYPE_CARD,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for order {self.order_id} - {self.status}"


class PaymentQueue(models.Model):
    """
    Очередь платежей для асинхронной обработки.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="queue",
    )
    status = models.CharField(
        max_length=10,
        choices=Payment.STATUS_CHOICES,
        default=Payment.STATUS_PENDING,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="queue",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Queue for payment {self.payment_id}"