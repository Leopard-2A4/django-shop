from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiTypes
from orders.models import Order
from .models import Payment, PaymentQueue
from .serializers import PaymentSerializer
import threading
import time
from django.utils import timezone
from basket.models import Basket


@extend_schema(
    tags=["Оплата"],
    summary="Обработка платежей",
    description="Оплата заказов с асинхронной обработкой",
)
class PaymentView(APIView):

    @extend_schema(
        summary="Оплатить заказ",
        description="Принимает данные карты и запускает асинхронную обработку платежа. "
                    "После успешной оплаты заказ переходит в статус 'paid', корзина очищается.",
        parameters=[
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"},
                "description": "ID заказа для оплаты"
            }
        ],
        request=PaymentSerializer,
        responses={
            200: OpenApiResponse(
                description="Платеж принят на обработку",
                examples={
                    "application/json": {
                        "paymentId": 1,
                        "status": "pending"
                    }
                }
            ),
            403: OpenApiResponse(description="Требуется авторизация"),
            404: OpenApiResponse(description="Заказ не найден"),
        },
        examples=[
            OpenApiExample(
                "Пример запроса - оплата картой",
                value={
                    "number": "1234567890123456",
                    "name": "IVAN PETROV",
                    "month": "12",
                    "year": "2028",
                    "code": "123",
                    "paymentType": "card"
                },
                request_only=True,
            ),
            OpenApiExample(
                "Пример ответа",
                value={
                    "paymentId": 1,
                    "status": "pending"
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request, id):
        if not request.user.is_authenticated:
            raise PermissionDenied()

        try:
            order = Order.objects.select_related('user').get(id=id, user=request.user)
        except Order.DoesNotExist:
            raise NotFound("Order not found")

        print("=" * 50)
        print("request.data:", request.data)
        print("paymentType:", request.data.get("paymentType"))
        print("payment_type:", request.data.get("payment_type"))
        print("=" * 50)

        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        print("validated_data:", serializer.validated_data)
        print("=" * 50)

        payment = serializer.save(
            order=order,
            status=Payment.STATUS_PENDING,
        )

        queue = PaymentQueue.objects.create(
            payment=payment,
            user=request.user,
        )

        threading.Thread(
            target=self.process_payment,
            args=(queue.id,),
            daemon=True,
        ).start()

        return Response(
            {"paymentId": payment.id, "status": "pending"},
            status=status.HTTP_200_OK,
        )

    def process_payment(self, queue_id):
        """Обработка платежа в фоне."""
        queue = PaymentQueue.objects.select_related(
            'payment__order',
            'user'
        ).get(id=queue_id)

        payment = queue.payment
        user = queue.user

        time.sleep(2)

        Payment.objects.filter(id=payment.id).update(status=Payment.STATUS_SUCCESS)
        Basket.objects.filter(user=user).delete()
        Order.objects.filter(id=payment.order.id).update(status="paid")

        PaymentQueue.objects.filter(id=queue.id).update(
            status=Payment.STATUS_SUCCESS,
            processed_at=timezone.now()
        )