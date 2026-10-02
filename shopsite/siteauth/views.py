import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from django.contrib.auth import authenticate, login, logout
from .serializers import SignInSerializer, SignUpSerializer
from basket.utils import merge_session_cart_to_db


@extend_schema(
    tags=["Авторизация"],
    summary="Аутентификация пользователей",
    description="Вход, регистрация и выход из системы",
)
class SignInView(APIView):
    """
    POST /sign-in
    body: { "username": "...", "password": "..." }
    """

    @extend_schema(
        summary="Вход в систему",
        description="Аутентифицирует пользователя по логину и паролю. Создает сессию.",
        request=SignInSerializer,
        responses={
            200: OpenApiResponse(
                description="Успешная авторизация",
                examples={
                    "application/json": {
                        "id": 1,
                        "username": "buyer1",
                        "name": "Иван"
                    }
                }
            ),
            401: OpenApiResponse(description="Неверные учетные данные"),
            400: OpenApiResponse(description="Некорректный JSON"),
        },
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={
                    "username": "buyer1",
                    "password": "123456"
                },
                request_only=True,
            ),
            OpenApiExample(
                "Пример ответа",
                value={
                    "id": 1,
                    "username": "buyer1",
                    "name": "Иван"
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        # Парсим данные
        if request.content_type == 'application/json':
            data = request.data
        else:
            # Если пришло как строка в QueryDict
            try:
                json_string = list(request.data.keys())[0]
                data = json.loads(json_string)
            except (json.JSONDecodeError, IndexError):
                return Response(
                    {"detail": "Invalid JSON"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Используем data вместо request.data
        serializer = SignInSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)

        # Слияние корзины из сессии в БД после успешной авторизации
        session_cart = request.session.get('cart', {})
        if session_cart:
            merge_session_cart_to_db(user, session_cart)
            del request.session['cart']
            request.session.save()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "name": user.first_name,
            },
            status=status.HTTP_200_OK,
        )


class SignUpView(APIView):
    """
    POST /sign-up
    body: { "name": "...", "username": "...", "password": "..." }
    """

    @extend_schema(
        summary="Регистрация нового пользователя",
        description="Создает нового пользователя и автоматически авторизует его. Создает профиль.",
        request=SignUpSerializer,
        responses={
            200: OpenApiResponse(
                description="Успешная регистрация",
                examples={
                    "application/json": {
                        "id": 5,
                        "username": "newuser",
                        "name": "Новый Пользователь"
                    }
                }
            ),
            400: OpenApiResponse(description="Ошибка валидации"),
        },
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={
                    "name": "Новый Пользователь",
                    "username": "newuser",
                    "password": "securepass123"
                },
                request_only=True,
            ),
            OpenApiExample(
                "Пример ответа",
                value={
                    "id": 5,
                    "username": "newuser",
                    "name": "Новый Пользователь"
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        login(request, user)

        # Слияние корзины из сессии в БД после регистрации
        session_cart = request.session.get('cart', {})
        if session_cart:
            merge_session_cart_to_db(user, session_cart)
            del request.session['cart']
            request.session.save()

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "name": user.first_name,
            },
            status=status.HTTP_200_OK,
        )


class SignOutView(APIView):
    """
    POST /sign-out
    """

    @extend_schema(
        summary="Выход из системы",
        description="Завершает сессию пользователя",
        responses={
            200: OpenApiResponse(
                description="Успешный выход",
                examples={
                    "application/json": {
                        "detail": "Logged out"
                    }
                }
            ),
        },
        examples=[
            OpenApiExample(
                "Пример ответа",
                value={
                    "detail": "Logged out"
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        logout(request)
        return Response(
            {"detail": "Logged out"},
            status=status.HTTP_200_OK,
        )