from django.db import models
from django.contrib.auth.models import User

class Basket(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="basket",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Basket of {self.user.username}"


class BasketItem(models.Model):
    basket = models.ForeignKey(
        Basket,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "shopproducts.Product",
        on_delete=models.CASCADE,
        related_name="basket_items",
    )
    count = models.IntegerField(default=1)

    class Meta:
        unique_together = ("basket", "product")  # один товар в корзине один раз

    def __str__(self):
        return f"{self.count} x {self.product.title} in basket {self.basket_id}"