from django.core.paginator import Paginator
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiTypes
from shopproducts.models import Category, Product
from .serializers import CategorySerializer, SaleItemSerializer
from django.db import models
from shopproducts.serializers import ProductSerializer
from django.utils import timezone
from django.db.models import Q


class CategoriesView(APIView):
    serializer_class = CategorySerializer

    @extend_schema(
        summary="Получить список категорий",
        description="Возвращает список родительских категорий с подкатегориями и изображениями",
        responses={
            200: CategorySerializer(many=True),
        }
    )
    def get(self, request):
        categories = Category.objects.filter(
            parent__isnull=True,
            archived=False
        ).prefetch_related(
            'subcategories',
        )

        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Каталог"])
class CatalogView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Получить каталог товаров с фильтрацией",
        description="Возвращает отфильтрованный и отсортированный список товаров с пагинацией",
        parameters=[
            OpenApiParameter(
                name="filter[name]",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Поиск по названию или описанию товара"
            ),
            OpenApiParameter(
                name="filter[minPrice]",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Минимальная цена"
            ),
            OpenApiParameter(
                name="filter[maxPrice]",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description="Максимальная цена"
            ),
            OpenApiParameter(
                name="filter[freeDelivery]",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Только товары с бесплатной доставкой"
            ),
            OpenApiParameter(
                name="filter[available]",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Только доступные товары"
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="ID категории"
            ),
            OpenApiParameter(
                name="tags",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="ID тегов через запятую (можно указать несколько раз)"
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Поле сортировки: date, reviews, rating, price",
                enum=["date", "reviews", "rating", "price"]
            ),
            OpenApiParameter(
                name="sortType",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Тип сортировки: inc (по возрастанию), dec (по убыванию)",
                enum=["inc", "dec"]
            ),
            OpenApiParameter(
                name="currentPage",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Номер страницы"
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Количество товаров на странице"
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Список товаров с пагинацией",
                examples={
                    "application/json": {
                        "items": [],
                        "currentPage": 1,
                        "lastPage": 10
                    }
                }
            ),
        }
    )
    def get(self, request):
        qs = Product.objects.select_related('category').prefetch_related(
            'images',
            'tags',
            'specifications',
            'reviews'
        )

        # filter[name] — поиск по title/description
        filter_name = request.query_params.get("filter[name]", "")
        if filter_name:
            qs = qs.filter(
                models.Q(title__icontains=filter_name) |
                models.Q(description__icontains=filter_name)
            )

        # filter[minPrice], filter[maxPrice]
        min_price = request.query_params.get("filter[minPrice]", 0)
        max_price = request.query_params.get("filter[maxPrice]", 50000)

        if min_price:
            qs = qs.filter(price__gte=float(min_price))

        if max_price:
            qs = qs.filter(price__lte=float(max_price))

        # filter[freeDelivery]
        free_delivery = request.query_params.get("filter[freeDelivery]", "false") == "true"
        if free_delivery:
            qs = qs.filter(free_delivery=True)

        # filter[available]
        available = request.query_params.get("filter[available]", "true") == "true"
        if available:
            qs = qs.filter(available=True)

        # category
        category_id = request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        # tags
        tags_param = request.query_params.getlist("tags")
        if tags_param:
            tag_ids = []
            for t in tags_param:
                tag_ids.extend(map(int, t.split(",")))
            qs = qs.filter(tags__id__in=tag_ids).distinct()

        # sort + sortType
        sort = request.query_params.get("sort", "date")
        sort_type = request.query_params.get("sortType", "dec")

        if sort == "reviews":
            qs = qs.annotate(reviews_count=Count("reviews"))
            order_field = "reviews_count"
        elif sort == "rating":
            order_field = "rating"
        elif sort == "price":
            order_field = "price"
        else:
            order_field = "date"

        if sort_type == "inc":
            qs = qs.order_by(order_field)
        else:
            qs = qs.order_by(f"-{order_field}")

        # pagination
        page = int(request.query_params.get("currentPage", 1))
        limit = int(request.query_params.get("limit", 20))

        paginator = Paginator(qs, limit)
        page_obj = paginator.page(page)

        items_serializer = ProductSerializer(page_obj.object_list, many=True)

        return Response(
            {
                "items": items_serializer.data,
                "currentPage": page_obj.number,
                "lastPage": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Каталог"])
class PopularProductsView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Получить популярные товары",
        description="Возвращает топ-8 популярных товаров по рейтингу",
        responses={
            200: ProductSerializer(many=True),
        }
    )
    def get(self, request):
        qs = Product.objects.filter(available=True).select_related('category').prefetch_related(
            'images',
            'tags',
            'specifications',
            'reviews'
        ).order_by("-rating", "-count")[:8]

        serializer = ProductSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Каталог"])
class LimitedProductsView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Получить лимитированные товары",
        description="Возвращает топ-16 лимитированных товаров по остатку",
        responses={
            200: ProductSerializer(many=True),
        }
    )
    def get(self, request):
        qs = Product.objects.filter(limited_edition=True, available=True).select_related('category').prefetch_related(
            'images',
            'tags',
            'specifications',
            'reviews'
        ).order_by("count")[:16]

        serializer = ProductSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Каталог"])
class SalesView(APIView):
    serializer_class = SaleItemSerializer

    @extend_schema(
        summary="Получить товары со скидками",
        description="Возвращает список товаров со скидками с пагинацией",
        parameters=[
            OpenApiParameter(
                name="currentPage",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Номер страницы",
                default=1
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Список товаров со скидками",
                examples={
                    "application/json": {
                        "items": [],
                        "currentPage": 1,
                        "lastPage": 5
                    }
                }
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        queryset = Product.objects.filter(
            Q(discount__gt=0) &
            Q(sale_date_from__lte=today) &
            Q(sale_date_to__gte=today) &
            Q(available=True)
        ).select_related('category').prefetch_related(
            'images',
            'tags',
            'specifications',
            'reviews'
        )

        # Пагинация
        page_number = request.query_params.get('currentPage', 1)
        page_size = 10

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        serializer = self.serializer_class(page, many=True)

        return Response({
            "items": serializer.data,
            "currentPage": page.number,
            "lastPage": paginator.num_pages
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["Каталог"])
class BannersView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Получить баннеры",
        description="Возвращает топ-10 товаров с бесплатной доставкой для баннеров",
        responses={
            200: ProductSerializer(many=True),
        }
    )
    def get(self, request):
        qs = Product.objects.filter(free_delivery=True, available=True).select_related('category').prefetch_related(
            'images',
            'tags',
            'specifications',
            'reviews'
        )[:10]

        serializer = ProductSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)