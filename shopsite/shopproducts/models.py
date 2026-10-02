from django.contrib.auth.models import User
from django.db import models

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

class ProductManager(models.Manager):
    """
    Менеджер для продуктов.
    Возвращает только объекты с available=True.
    """
    def get_queryset(self):
        return super().get_queryset().filter(available=True)

    def all_with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(available=False)


class Category(models.Model):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subcategories",
    )
    title = models.CharField(max_length=100)
    src = models.ImageField(upload_to="categories/", blank=True, null=True)
    alt = models.CharField(max_length=255, blank=True, null=True)
    archived = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.archived = True
        self.save()

    def restore(self):
        self.archived = False
        self.save()

class Image(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="images",
    )
    src = models.ImageField(upload_to="products/")
    alt = models.CharField(max_length=255, blank=True)
    archived = models.BooleanField(default=False)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.alt or f"Image {self.pk}"

    def soft_delete(self):
        self.archived = True
        self.save()

    def restore(self):
        self.archived = False
        self.save()


class Specification(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="specifications",
    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.name}: {self.value}"

    def soft_delete(self):
        self.archived = True
        self.save()

    def restore(self):
        self.archived = False
        self.save()


class Tag(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.archived = True
        self.save()

    def restore(self):
        self.archived = False
        self.save()


class Review(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="reviews",
    )
    text = models.TextField()
    rate = models.SmallIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def __str__(self):
        return f"Review by {self.author} for product {self.product_id}"

    def soft_delete(self):
        self.archived = True
        self.save()

    def restore(self):
        self.archived = False
        self.save()


class Product(models.Model):
    full_description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="shopproducts",
    )

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.SmallIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    free_delivery = models.BooleanField(default=False)
    count = models.IntegerField(default=1)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    limited_edition = models.BooleanField(default=False)
    available = models.BooleanField(default=True)
    sale_date_from = models.DateField('скидка с', blank=True, null=True)
    sale_date_to = models.DateField('скидка по', blank=True, null=True)
    objects = ProductManager()
    all_objects = models.Manager()  # все объекты

    def __str__(self):
        return f"Product={self.title},pk={self.pk}"

    def soft_delete(self):
        """
        Мягкое удаление продукта.
        """
        self.available = False
        self.save()

    def restore(self):
        """
        Восстановление продукта.
        """
        self.available = True
        self.save()