from rest_framework import serializers
from django.contrib.auth import get_user_model
from siteauth.models import Avatar, Profile

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    src = serializers.SerializerMethodField()

    class Meta:
        model = Avatar
        fields = ("src", "alt")

    def get_src(self, obj):
        if obj.src:
            return obj.src.url
        return ""


class UserProfileSerializer(serializers.Serializer):
    """
    Сериализатор профиля (GET/POST /profile).
    instance — Profile.
    """
    fullName = serializers.CharField(
        help_text="Полное имя пользователя",
        source="user.first_name",
        required=False,
        allow_blank=True
    )
    email = serializers.EmailField(
        help_text="Email пользователя",
        source="user.email",
        required=False
    )
    phone = serializers.CharField(
        help_text="Телефон пользователя",
        required=False,
        allow_blank=True
    )
    avatar = serializers.SerializerMethodField(help_text="Аватар пользователя")

    def get_avatar(self, obj: Profile):
        avatar = getattr(obj, "avatar", None)
        if avatar:
            return AvatarSerializer(avatar).data
        return {"src": "", "alt": ""}

    def validate_email(self, value):
        """Проверяем, что email не занят другим пользователем."""
        if self.instance and self.instance.user.email == value:
            return value  # Email не изменился

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def update(self, instance, validated_data):
        """
        instance — Profile.
        validated_data: { user: { first_name, email }, phone }
        """
        user = instance.user
        user_changed = False

        user_data = validated_data.pop("user", {})
        if "first_name" in user_data:
            user.first_name = user_data["first_name"]
            user_changed = True
        if "email" in user_data:
            user.email = user_data["email"]
            user_changed = True

        if "phone" in validated_data:
            instance.phone = validated_data["phone"]

        # Сохраняем user только если он менялся
        if user_changed:
            user.save()

        instance.save()
        return instance