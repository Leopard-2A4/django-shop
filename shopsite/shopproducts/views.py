from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from .models import Product, Review
from .serializers import ProductSerializer, ReviewSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly


@extend_schema(
    tags=["Товары"],
    summary="Управление товарами",
    description="CRUD операции для товаров магазина",
)
class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = "pk"

    def get_queryset(self):
        # ОПТИМИЗАЦИЯ: select_related для ForeignKey, prefetch_related для обратных связей
        return Product.objects.select_related('category').prefetch_related(
            'images',
            'tags',
            'specifications',
            'reviews'
        )

    @extend_schema(
        summary="Список всех товаров",
        description="Возвращает список всех товаров с пагинацией",
        responses={
            200: ProductSerializer(many=True),
        },
        examples=[
            OpenApiExample(
                "Пример ответа",
                value=[
                    {
                        "id": 1,
                        "category": {"id": 1, "title": "Электроника"},
                        "price": "99990.00",
                        "count": 50,
                        "title": "iPhone 15 Pro",
                        "description": "Флагманский смартфон",
                        "fullDescription": "Подробное описание...",
                        "freeDelivery": True,
                        "rating": "4.8",
                        "images": [],
                        "tags": [],
                        "reviews": 5,
                        "specifications": []
                    }
                ],
                response_only=True,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получить товар по ID",
        description="Возвращает детальную информацию о товаре",
        parameters=[
            {
                "name": "pk",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
                "description": "ID товара"
            }
        ],
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Товар не найден"),
        },
        examples=[
            OpenApiExample(
                "Пример ответа",
                value={
                    "id": 1,
                    "category": {"id": 1, "title": "Электроника"},
                    "price": "99990.00",
                    "count": 50,
                    "title": "iPhone 15 Pro",
                    "description": "Флагманский смартфон",
                    "fullDescription": "Подробное описание...",
                    "freeDelivery": True,
                    "rating": "4.8",
                    "images": [],
                    "tags": [],
                    "reviews": 5,
                    "specifications": []
                },
                response_only=True,
            )
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Создать товар",
        description="Создает новый товар",
        request=ProductSerializer,
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Обновить товар",
        description="Полностью обновляет товар",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
            404: OpenApiResponse(description="Товар не найден"),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить товар",
        description="Частично обновляет товар",
        request=ProductSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
            404: OpenApiResponse(description="Товар не найден"),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить товар",
        description="Удаляет товар",
        responses={
            204: OpenApiResponse(description="Товар удален"),
            404: OpenApiResponse(description="Товар не найден"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    tags=["Отзывы"],
    summary="Управление отзывами",
    description="CRUD операции для отзывов к товарам",
)
class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.select_related('author', 'product')

    @extend_schema(
        summary="Список всех отзывов",
        description="Возвращает список всех отзывов",
        responses={
            200: ReviewSerializer(many=True),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получить отзыв по ID",
        description="Возвращает детальную информацию об отзыве",
        parameters=[
            {
                "name": "pk",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
                "description": "ID отзыва"
            }
        ],
        responses={
            200: ReviewSerializer,
            404: OpenApiResponse(description="Отзыв не найден"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Создать отзыв",
        description="Создает новый отзыв к товару. Требуется авторизация.",
        request=ReviewSerializer,
        parameters=[
            {
                "name": "product_pk",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
                "description": "ID товара"
            }
        ],
        responses={
            201: ReviewSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
            401: OpenApiResponse(description="Требуется авторизация"),
        },
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={
                    "text": "Отличный товар!",
                    "rate": 5
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        product_pk = self.kwargs.get("product_pk")
        serializer.save(
            product_id=product_pk,
            author=self.request.user,  # ← ДОБАВЛЕНО: передаём текущего пользователя
        )

    @extend_schema(
        summary="Обновить отзыв",
        description="Полностью обновляет отзыв",
        request=ReviewSerializer,
        responses={
            200: ReviewSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
            404: OpenApiResponse(description="Отзыв не найден"),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частично обновить отзыв",
        description="Частично обновляет отзыв",
        request=ReviewSerializer,
        responses={
            200: ReviewSerializer,
            400: OpenApiResponse(description="Ошибка валидации"),
            404: OpenApiResponse(description="Отзыв не найден"),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удалить отзыв",
        description="Удаляет отзыв",
        responses={
            204: OpenApiResponse(description="Отзыв удален"),
            404: OpenApiResponse(description="Отзыв не найден"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)