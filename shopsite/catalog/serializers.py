from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.conf import settings
from shopproducts.models import Category, Product, Image
from shopproducts.serializers import ImageSerializer
from decimal import Decimal


class CategoryImageFromProductSerializer(serializers.Serializer):
    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_src(self, obj: Category) -> str:
        product = obj.shopproducts.first()
        if not product:
            return ""

        image = product.images.first()
        if image and image.src:
            return image.src.url.replace(settings.MEDIA_URL, "/", 1)
        return ""

    @extend_schema_field(serializers.CharField)
    def get_alt(self, obj: Category) -> str:
        product = obj.shopproducts.first()
        if not product:
            return ""

        image = product.images.first()
        return getattr(image, "alt", "") if image else ""


class SubCategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", "image")

    @extend_schema_field(CategoryImageFromProductSerializer)
    def get_image(self, obj: Category):
        return CategoryImageFromProductSerializer(obj).data


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", "image", "subcategories")

    @extend_schema_field(CategoryImageFromProductSerializer)
    def get_image(self, obj: Category):
        return CategoryImageFromProductSerializer(obj).data

    @extend_schema_field(SubCategorySerializer(many=True))
    def get_subcategories(self, obj: Category):
        subs = obj.subcategories.all()
        return SubCategorySerializer(subs, many=True).data


class SaleItemSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    salePrice = serializers.SerializerMethodField()
    dateFrom = serializers.SerializerMethodField()
    dateTo = serializers.SerializerMethodField()
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'salePrice', 'dateFrom', 'dateTo', 'images']

    @extend_schema_field(serializers.CharField)
    def get_id(self, obj) -> str:
        return str(obj.id)  # В Swagger id должен быть строкой

    @extend_schema_field(serializers.DecimalField)
    def get_salePrice(self, obj):
        discount = obj.discount or 0
        price = obj.price or Decimal('0')

        if discount > 0:
            # Рассчитываем цену со скидкой
            sale_price = price * (1 - Decimal(str(discount)) / 100)
            return round(sale_price, 2)
        return price

    @extend_schema_field(serializers.CharField)
    def get_dateFrom(self, obj) -> str:
        return obj.sale_date_from.strftime('%m-%d') if obj.sale_date_from else ''

    @extend_schema_field(serializers.CharField)
    def get_dateTo(self, obj) -> str:
        return obj.sale_date_to.strftime('%m-%d') if obj.sale_date_to else ''