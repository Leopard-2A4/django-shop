from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .models import Order
from .services import order_payload, create_order_from_basket, confirm_order
from .serializers import OrderSerializer, HistoryOrderSerializer


def can_access(request, order: Order) -> bool:
    """
    Проверка доступа к заказу.
    """
    if request.user.is_authenticated and order.user_id == request.user.id:
        return True
    if request.user.is_authenticated and order.user_id is None:
        return True
    key = request.session.session_key
    return bool(key and order.session_key == key)


@extend_schema(
    tags=["Заказы"],
    summary="Управление заказами",
    description="Получение списка заказов и создание новых заказов",
)
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response([])

        orders = Order.objects.filter(
            user=request.user,
            archived=False,
        ).select_related('user').prefetch_related(
            'shopproducts__product__images',
            'shopproducts__product__tags',
            'shopproducts__product__category',
        )

        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Создать заказ из корзины",
        description="Создает новый заказ на основе списка ID товаров",
        request={
            "application/json": {
                "type": "array",
                "items": {"type": "string"},
                "example": ["1", "2", "3"]
            }
        },
        responses={
            200: OpenApiResponse(
                description="Заказ создан",
                examples={
                    "application/json": {
                        "orderId": 123
                    }
                }
            ),
            400: OpenApiResponse(description="Ошибка валидации"),
        },
    )
    def post(self, request):
        """
        Создание заказа.
        Body: ["1", "2", "3"] — массив ID товаров (строки).
        """
        payload = request.data
        if not isinstance(payload, list):
            return Response(
                {'detail': 'Ожидается массив ID товаров'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = create_order_from_basket(request, payload)

        return Response({'orderId': order.id}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Заказы"],
    summary="Детали заказа и подтверждение",
    description="Получение информации о заказе и его финальное подтверждение",
)
class OrderDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Шаг 4: предпросмотр заказа (только чтение!)"""
        order = Order.objects.filter(pk=pk).select_related('user').prefetch_related(
            'shopproducts__product__images',
            'shopproducts__product__tags',
            'shopproducts__product__category',
        ).first()

        if not order or not can_access(request, order):
            return Response({'detail': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_authenticated and order.user_id is None:
            order.user = request.user
            order.save(update_fields=['user'])

        preview_data = order_payload(order)
        return Response(preview_data)

    def post(self, request, pk):
        """Шаг 4: подтверждение заказа (реальное сохранение)"""
        if not request.user.is_authenticated:
            return Response({'detail': 'Нужна авторизация'}, status=status.HTTP_403_FORBIDDEN)
        order = Order.objects.filter(pk=pk).select_related('user').first()
        if not order:
            return Response({'detail': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Привязываем юзера ПЕРЕД проверкой доступа
        if order.user_id is None:
            order.user = request.user
            order.save(update_fields=['user'])

        if not can_access(request, order):
            return Response({'detail': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data if isinstance(request.data, dict) else {}

        confirm_order(order, data)

        return Response({'orderId': order.id}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Заказы"],
    summary="История заказов",
    description="Получение истории всех заказов пользователя",
)
class HistoryOrderView(APIView):
    """
    GET /history-order — история заказов (для фронтенда).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Получить историю заказов",
        description="Возвращает все заказы пользователя, отсортированные по дате создания",
        responses={
            200: HistoryOrderSerializer(many=True),
            403: OpenApiResponse(description="Требуется авторизация"),
        },
        examples=[
            OpenApiExample(
                "Пример ответа",
                value=[
                    {
                        "id": 1,
                        "createdAt": "2026-09-13T10:00:00Z",
                        "deliveryType": "express",
                        "paymentType": "card",
                        "totalCost": "99990.00",
                        "status": "delivered",
                        "products": []
                    }
                ],
                response_only=True,
            )
        ],
    )
    def get(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied()

        orders = Order.objects.filter(
            user=request.user,
            archived=False,
        ).select_related('user').prefetch_related(
            'shopproducts__product__images',
            'shopproducts__product__tags',
            'shopproducts__product__category',
        ).order_by("-created_at")

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)