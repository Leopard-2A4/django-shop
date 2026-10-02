from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Product, Image, Tag, Review, Specification, Category


class SubcategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для подкатегорий.
    НЕ включает поле subcategories, чтобы избежать рекурсии.
    """
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", "image")

    def get_image(self, obj: Category):
        if obj.src:
            return {
                "src": obj.src.url,
                "alt": obj.alt or "",
            }
        return None


class CategorySerializer(serializers.ModelSerializer):
    """
    Основной сериализатор для родительских категорий.
    Включает поле subcategories.
    """
    image = serializers.SerializerMethodField()
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ("id", "title", "image", "subcategories")

    def get_image(self, obj: Category):
        if obj.src:
            return {
                "src": obj.src.url,
                "alt": obj.alt or "",
            }
        return None


class ImageSerializer(serializers.ModelSerializer):
    src = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ("src", "alt")

    @extend_schema_field(serializers.CharField)
    def get_src(self, obj) -> str:
        if obj.src:
            return obj.src.url
        return ""


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ("name", "value")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    email = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("author", "email", "text", "rate", "date")

    @extend_schema_field(serializers.CharField)
    def get_email(self, obj) -> str:
        return getattr(obj.author, "email", "")


class ProductSerializer(serializers.ModelSerializer):
    fullDescription = serializers.CharField(source="full_description", read_only=True)
    freeDelivery = serializers.BooleanField(source="free_delivery", read_only=True)

    images = ImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
    )
    reviews = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    specifications = SpecificationSerializer(many=True, read_only=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)

    class Meta:
        model = Product
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

    @extend_schema_field(serializers.IntegerField)
    def get_tags(self, obj):
        return [
            {"id": tag.id, "name": tag.name}
            for tag in obj.tags.all()
        ]

    @extend_schema_field(serializers.IntegerField)
    def get_reviews(self, obj):
        return obj.reviews.count()