from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Order, OrderProduct
from shopproducts.models import Product
from shopproducts.serializers import (
    ImageSerializer,
    TagSerializer,
    ReviewSerializer,
    SpecificationSerializer,
    CategorySerializer
)


class OrderProductInOrderSerializer(serializers.ModelSerializer):
    fullDescription = serializers.CharField(source="full_description", read_only=True)
    freeDelivery = serializers.BooleanField(source="free_delivery", read_only=True)

    category = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    specifications = serializers.SerializerMethodField()
    rating = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)

    class Meta:
        model = OrderProduct
        fields = (
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "fullDescription",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "specifications",
            "rating",
        )

    @extend_schema_field(CategorySerializer)
    def get_category(self, obj):
        category = obj.category
        return CategorySerializer(category).data

    @extend_schema_field(ImageSerializer(many=True))
    def get_images(self, obj):
        product = obj.product
        return ImageSerializer(product.images.all(), many=True).data

    @extend_schema_field(serializers.ListField)
    def get_tags(self, obj):
        product = obj.product
        return [
            {"id": tag.id, "name": tag.name}
            for tag in product.tags.all()
        ]

    @extend_schema_field(serializers.IntegerField)
    def get_reviews(self, obj):
        return obj.product.reviews.count()

    @extend_schema_field(SpecificationSerializer(many=True))
    def get_specifications(self, obj):
        product = obj.product
        return SpecificationSerializer(product.specifications.all(), many=True).data


class OrderSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    deliveryType = serializers.CharField(source="delivery_type")
    paymentType = serializers.CharField(source="payment_type")
    fullName = serializers.CharField(source="full_name")
    totalCost = serializers.DecimalField(source="total_cost", max_digits=10, decimal_places=2)

    products = OrderProductInOrderSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "createdAt",
            "fullName",
            "email",
            "phone",
            "deliveryType",
            "paymentType",
            "totalCost",
            "status",
            "city",
            "address",
            "products",
        )
        read_only_fields = ("id", "createdAt")


class OrderCreateProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="ID товара")
    count = serializers.IntegerField(min_value=1, help_text="Количество товара")


class OrderCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(help_text="ФИО получателя")
    email = serializers.EmailField(help_text="Email получателя")
    phone = serializers.CharField(help_text="Телефон получателя")
    delivery_type = serializers.CharField(help_text="Тип доставки: ordinary, express")
    payment_type = serializers.CharField(help_text="Тип оплаты: card, cash")
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Итоговая стоимость")
    status = serializers.CharField(required=False, default="new", help_text="Статус заказа")
    city = serializers.CharField(help_text="Город доставки")
    address = serializers.CharField(help_text="Адрес доставки")

    products = OrderCreateProductSerializer(many=True, help_text="Список товаров в заказе")

    def create(self, validated_data):
        products_data = validated_data.pop("products")
        order = Order.objects.create(**validated_data)

        for prod in products_data:
            product_id = prod["id"]
            count = prod["count"]

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                order.delete()
                raise serializers.ValidationError(f"Product {product_id} not found")

            OrderProduct.objects.create(
                order=order,
                product=product,
                title=product.title,
                description=product.description,
                full_description=product.full_description,
                price=product.price,
                category=product.category,
                free_delivery=product.free_delivery,
                rating=product.rating,
                count=count,
            )

        return order


class HistoryOrderSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    deliveryType = serializers.CharField(source="delivery_type")
    paymentType = serializers.CharField(source="payment_type")
    totalCost = serializers.DecimalField(source="total_cost", max_digits=10, decimal_places=2)

    products = OrderProductInOrderSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "createdAt", "deliveryType", "paymentType", "totalCost", "status", "products"]