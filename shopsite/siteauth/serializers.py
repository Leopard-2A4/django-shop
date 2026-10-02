from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="Имя пользователя")
    password = serializers.CharField(write_only=True, help_text="Пароль")


class SignUpSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="Имя пользователя")
    username = serializers.CharField(help_text="Логин для входа")
    password = serializers.CharField(write_only=True, help_text="Пароль")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            first_name=validated_data["name"],  # name -> first_name
        )
        Profile.objects.create(user=user)
        return user