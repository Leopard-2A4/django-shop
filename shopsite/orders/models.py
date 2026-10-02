from django.db import models
from django.contrib.auth.models import User

class SoftDeleteManager(models.Manager):
    """
    Менеджер для мягкого удаления.
    Возвращает только объекты с archived=False.
    """
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)

    def all_with_deleted(self):
        """
        Получить все объекты, включая удалённые.
        """
        return super().get_queryset()

    def deleted_only(self):
        """
        Получить только удалённые объекты.
        """
        return super().get_queryset().filter(archived=True)

class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders",
        null=False,
        blank=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    delivery_type = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=50)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    address = models.TextField()
    archived = models.BooleanField(default=False)
    STEP_CHOICES = [
        ('cart', 'Корзина'),
        ('user_info', 'Параметры пользователя'),
        ('delivery', 'Способ доставки'),
        ('payment', 'Способ оплаты'),
        ('confirmed', 'Подтверждён'),
    ]
    step = models.CharField(max_length=20, choices=STEP_CHOICES, default='cart')
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def recalculate_total(self):
        """
        Пересчитывает итоговую стоимость заказа.
        Обычная доставка: 200р (бесплатно если >= 2000р)
        Экспресс доставка: 500р (всегда платно)
        """
        # Сумма товаров
        items_total = sum(
            item.price * item.count
            for item in self.shopproducts.all()
        )

        # Стоимость доставки
        if self.delivery_type == 'express':
            delivery_cost = 500
        elif self.delivery_type == 'ordinary':
            delivery_cost = 0 if items_total >= 2000 else 200
        else:
            delivery_cost = 0  # Если доставка ещё не выбрана

        self.total_cost = items_total + delivery_cost

    def soft_delete(self):
        self.archived = True
        self.products.update(archived=True)
        self.save()

    def restore(self):

        self.archived = False
        self.save()

    def __str__(self):
        return f"Order {self.id} by {self.full_name}"


class OrderProduct(models.Model):
    """
    Товар внутри заказа.
    Хранит копию основных данных продукта на момент заказа + количество.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="shopproducts",
    )
    product = models.ForeignKey(
        "shopproducts.Product",
        on_delete=models.PROTECT,
        related_name="order_products",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    full_description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        "shopproducts.Category",
        on_delete=models.PROTECT,
        related_name="order_category",
    )
    free_delivery = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    count = models.IntegerField(default=1)
    date = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.archived = True
        self.save()

    def restore(self):

        self.archived = False
        self.save()

    def __str__(self):
        return f"{self.count} x {self.title} in order {self.order_id}"