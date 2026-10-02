from rest_framework import serializers
from .models import Payment, PaymentQueue
from datetime import datetime
import random


class PaymentSerializer(serializers.ModelSerializer):
    number = serializers.CharField(
        max_length=16,
        help_text="Номер карты (до 16 цифр, четное число)"
    )
    name = serializers.CharField(
        max_length=100,
        help_text="Имя владельца карты"
    )
    month = serializers.CharField(
        max_length=2,
        help_text="Месяц истечения срока (01-12)"
    )
    year = serializers.CharField(
        max_length=4,
        help_text="Год истечения срока (4 цифры)"
    )
    code = serializers.CharField(
        max_length=4,
        write_only=True,
        help_text="CVV/CVC код (3-4 цифры)"
    )
    paymentType = serializers.ChoiceField(
        choices=Payment.PAYMENT_TYPE_CHOICES,
        default=Payment.PAYMENT_TYPE_CARD,
        required=False,
        source='payment_type',
        help_text="Тип оплаты: card (карта) или someone (кто-то другой)"
    )

    class Meta:
        model = Payment
        fields = ["number", "name", "month", "year", "code", "paymentType"]

    def validate_number(self, value):
        # Номер должен быть ≤ 8 цифр и чётным
        if not value.isdigit():
            raise serializers.ValidationError("Number must contain only digits")
        if len(value) > 8:
            raise serializers.ValidationError("Number must be no longer than 8 digits")
        if int(value) % 2 != 0:
            raise serializers.ValidationError("Number must be even")
        return value

    def validate_month(self, value):
        if not value.isdigit() or not (1 <= int(value) <= 12):
            raise serializers.ValidationError("Invalid month")
        return value.zfill(2)

    def validate_year(self, value):
        current_year = datetime.now().year

        if not value.isdigit() or len(value) != 4:
            raise serializers.ValidationError("Invalid year")
        return value

    def validate_code(self, value):
        if not value.isdigit() or not (3 <= len(value) <= 4):
            raise serializers.ValidationError("Invalid code")
        return value

    def create(self, validated_data):
        # code не сохраняем в БД
        validated_data.pop("code", None)
        return super().create(validated_data)