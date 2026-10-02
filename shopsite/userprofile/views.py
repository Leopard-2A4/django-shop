from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import update_session_auth_hash
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiTypes
from .serializers import UserProfileSerializer
from siteauth.models import Profile, Avatar


@extend_schema(tags=["Профиль"])
class UserProfileView(APIView):
    """
    GET /profile — получить профиль текущего пользователя.
    POST /profile — обновить профиль (fullName, email, phone).
    """
    permission_classes = [IsAuthenticated]

    def get_profile(self, user):
        # ОПТИМИЗАЦИЯ: select_related для связи с User
        return Profile.objects.select_related('user').filter(
            user=user,
            archived=False
        ).first()

    @extend_schema(
        summary="Получить профиль",
        description="Возвращает профиль авторизованного пользователя.",
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="Профиль пользователя",
            ),
            404: OpenApiResponse(
                description="Профиль не найден",
                examples={
                    "application/json": OpenApiExample(
                        "Not Found",
                        value={"detail": "Profile not found or archived"}
                    )
                }
            ),
        }
    )
    def get(self, request):
        profile = self.get_profile(request.user)
        if not profile:
            return Response(
                {"detail": "Profile not found or archived"},
                status=HTTP_404_NOT_FOUND,
            )

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=HTTP_200_OK)

    @extend_schema(
        summary="Обновить профиль",
        description="Обновляет данные профиля (fullName, email, phone) авторизованного пользователя.",
        request=UserProfileSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="Обновлённый профиль",
            ),
            404: OpenApiResponse(
                description="Профиль не найден",
                examples={
                    "application/json": OpenApiExample(
                        "Not Found",
                        value={"detail": "Profile not found or archived"}
                    )
                }
            ),
        }
    )
    def post(self, request):
        profile = self.get_profile(request.user)
        if not profile:
            return Response(
                {"detail": "Profile not found or archived"},
                status=HTTP_404_NOT_FOUND,
            )

        serializer = UserProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_200_OK)


@extend_schema(tags=["Профиль"])
class ChangePasswordView(APIView):
    """POST /profile/password — смена пароля."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Изменить пароль",
        description=(
                "Принимает текущий и новый пароль. Проверяет корректность текущего пароля, "
                "устанавливает новый и обновляет сессию, чтобы пользователь остался авторизованным."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "currentPassword": {"type": "string", "example": "old_password123"},
                    "newPassword": {"type": "string", "example": "new_password456"},
                },
                "required": ["currentPassword", "newPassword"],
            }
        },
        responses={
            200: OpenApiResponse(
                description="Пароль успешно изменён",
                examples={
                    "application/json": OpenApiExample(
                        "Success",
                        value={"detail": "Password changed"}
                    )
                }
            ),
            400: OpenApiResponse(
                description="Ошибка валидации",
                examples={
                    "application/json": OpenApiExample(
                        "Bad Request",
                        value={"detail": "Current password is incorrect"}
                    )
                }
            ),
            404: OpenApiResponse(
                description="Профиль не найден",
                examples={
                    "application/json": OpenApiExample(
                        "Not Found",
                        value={"detail": "Profile not found or archived"}
                    )
                }
            ),
        }
    )
    def post(self, request):
        # ОПТИМИЗАЦИЯ: select_related для связи с User
        profile = Profile.objects.select_related('user').filter(
            user=request.user,
            archived=False
        ).first()

        if not profile:
            return Response(
                {"detail": "Profile not found or archived"},
                status=HTTP_404_NOT_FOUND,
            )

        user = request.user
        current_password = request.data.get("currentPassword")
        new_password = request.data.get("newPassword")

        if not current_password or not new_password:
            return Response(
                {"detail": "currentPassword and newPassword are required"},
                status=HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {"detail": "Current password is incorrect"},
                status=HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        return Response({"detail": "Password changed"}, status=HTTP_200_OK)


@extend_schema(tags=["Профиль"])
class ChangeAvatarView(APIView):
    """POST /profile/avatar — загрузка аватарки."""
    permission_classes = [IsAuthenticated]

    def get_profile(self, user):
        # ОПТИМИЗАЦИЯ: select_related для связи с User
        return Profile.objects.select_related('user').filter(
            user=user,
            archived=False
        ).first()

    @extend_schema(
        summary="Загрузить аватар",
        description="Загружает новый аватар для профиля. Максимальный размер файла — 2 МБ.",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "avatar": {"type": "string", "format": "binary"},
                },
                "required": ["avatar"],
            }
        },
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="Обновлённый профиль с новым аватаром",
            ),
            400: OpenApiResponse(
                description="Ошибка валидации",
                examples={
                    "application/json": OpenApiExample(
                        "No File",
                        value={"detail": "No avatar file provided"}
                    ),
                    "application/json": OpenApiExample(
                        "Too Large",
                        value={"detail": "Avatar size can`t be more than 2 MB"}
                    ),
                }
            ),
            404: OpenApiResponse(
                description="Профиль не найден",
                examples={
                    "application/json": OpenApiExample(
                        "Not Found",
                        value={"detail": "Profile not found or archived"}
                    )
                }
            ),
        }
    )
    def post(self, request):
        profile = self.get_profile(request.user)
        if not profile:
            return Response(
                {"detail": "Profile not found or archived"},
                status=HTTP_404_NOT_FOUND,
            )

        avatar_file = request.FILES.get("avatar")
        if not avatar_file:
            return Response(
                {"detail": "No avatar file provided"},
                status=HTTP_400_BAD_REQUEST,
            )
        if avatar_file.size > 2 * 1024 * 1024:
            return Response(
                {"detail": "Avatar size can`t be more than 2 MB"},
                status=HTTP_400_BAD_REQUEST,
            )

        avatar, _ = Avatar.objects.get_or_create(
            profile=profile,
            defaults={"alt": ""},
        )
        avatar.src = avatar_file
        avatar.save()

        return Response(
            UserProfileSerializer(profile).data,
            status=HTTP_200_OK,
        )