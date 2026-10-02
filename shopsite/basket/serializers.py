from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import BasketItem
from shopproducts.models import Product
from shopproducts.serializers import ImageSerializer, SpecificationSerializer


class BasketProductSerializer(serializers.ModelSerializer):
    fullDescription = serializers.CharField(source="full_description", read_only=True)
    freeDelivery = serializers.BooleanField(source="free_delivery", read_only=True)

    images = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    rating = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "category", "price", "count", "date", "title",
            "description", "fullDescription", "freeDelivery", "images",
            "tags", "reviews", "specifications", "rating",
        )

    @extend_schema_field(ImageSerializer(many=True))
    def get_images(self, obj: Product):
        return ImageSerializer(obj.images.all(), many=True).data

    @extend_schema_field(serializers.ListField)
    def get_tags(self, obj: Product):
        return [{"id": tag.id, "name": tag.name} for tag in obj.tags.all()]

    @extend_schema_field(serializers.IntegerField)
    def get_reviews(self, obj: Product):
        return obj.reviews.count()

    @extend_schema_field(SpecificationSerializer(many=True))
    def get_specifications(self, obj: Product):
        return SpecificationSerializer(obj.specifications.all(), many=True).data


class BasketItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="product.id", read_only=True)
    category = serializers.IntegerField(source="product.category.id", read_only=True)
    price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)
    count = serializers.IntegerField()
    date = serializers.DateTimeField(source="product.date", read_only=True)
    title = serializers.CharField(source="product.title", read_only=True)
    description = serializers.CharField(source="product.description", read_only=True)
    fullDescription = serializers.CharField(source="product.full_description", read_only=True)
    freeDelivery = serializers.BooleanField(source="product.free_delivery", read_only=True)
    rating = serializers.DecimalField(source="product.rating", max_digits=3, decimal_places=1, read_only=True)

    images = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()

    class Meta:
        model = BasketItem
        fields = (
            "id", "category", "price", "count", "date", "title",
            "description", "fullDescription", "freeDelivery", "images",
            "tags", "reviews", "specifications", "rating",
        )

    @extend_schema_field(ImageSerializer(many=True))
    def get_images(self, obj: BasketItem):
        return ImageSerializer(obj.product.images.all(), many=True).data

    @extend_schema_field(serializers.ListField)
    def get_tags(self, obj: BasketItem):
        return [{"id": tag.id, "name": tag.name} for tag in obj.product.tags.all()]

    @extend_schema_field(serializers.IntegerField)
    def get_reviews(self, obj: BasketItem):
        return obj.product.reviews.count()

    @extend_schema_field(SpecificationSerializer(many=True))
    def get_specifications(self, obj: BasketItem):
        return SpecificationSerializer(obj.product.specifications.all(), many=True).data


class SessionBasketItemSerializer(serializers.Serializer):
    """
    Сериализатор для корзины неавторизованного пользователя.
    Ожидает на вход словарь вида: {'product': Product_instance, 'count': int}
    """
    id = serializers.IntegerField(source="product.id", read_only=True)
    category = serializers.IntegerField(source="product.category.id", read_only=True)
    price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)
    count = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(source="product.date", read_only=True)
    title = serializers.CharField(source="product.title", read_only=True)
    description = serializers.CharField(source="product.description", read_only=True)
    fullDescription = serializers.CharField(source="product.full_description", read_only=True)
    freeDelivery = serializers.BooleanField(source="product.free_delivery", read_only=True)
    rating = serializers.DecimalField(source="product.rating", max_digits=3, decimal_places=1, read_only=True)

    images = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()

    @extend_schema_field(ImageSerializer(many=True))
    def get_images(self, obj: dict):
        return ImageSerializer(obj["product"].images.all(), many=True).data

    @extend_schema_field(serializers.ListField)
    def get_tags(self, obj: dict):
        return [{"id": tag.id, "name": tag.name} for tag in obj["product"].tags.all()]

    @extend_schema_field(serializers.IntegerField)
    def get_reviews(self, obj: dict):
        return obj["product"].reviews.count()

    @extend_schema_field(SpecificationSerializer(many=True))
    def get_specifications(self, obj: dict):
        return SpecificationSerializer(obj["product"].specifications.all(), many=True).data


class BasketActionSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="ID товара")
    count = serializers.IntegerField(
        required=False,
        help_text="Количество товара. Для DELETE: если не указано - удалить полностью"
    )