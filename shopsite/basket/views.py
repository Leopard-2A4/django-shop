from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .models import Basket, BasketItem
from .serializers import (
    BasketItemSerializer,
    SessionBasketItemSerializer,
)
from shopproducts.models import Product


@extend_schema(
    tags=["Корзина"],
    summary="Управление корзиной",
    description="Получение, добавление и удаление товаров из корзины (сессия или БД)",
)
class BasketView(APIView):

    def get(self, request):
        if request.user.is_authenticated:
            basket, _ = Basket.objects.get_or_create(user=request.user)

            items = basket.items.select_related('product__category').prefetch_related(
                'product__images',
                'product__tags',
                'product__specifications',
                'product__reviews'
            )
            serializer = BasketItemSerializer(items, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            session_cart = request.session.get('cart', {})
            if not session_cart:
                return Response([], status=status.HTTP_200_OK)

            products = Product.objects.filter(id__in=session_cart.keys()).select_related('category').prefetch_related(
                'images', 'tags', 'specifications', 'reviews'
            )

            cart_data = [{"product": product, "count": session_cart[str(product.id)]} for product in products]
            serializer = SessionBasketItemSerializer(cart_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        product_id = request.data.get("id")
        count = request.data.get("count", 1)

        if not product_id:
            return Response({"detail": "Product id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not Product.objects.filter(id=product_id).exists():
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_authenticated:
            basket, _ = Basket.objects.get_or_create(user=request.user)
            item, created = BasketItem.objects.get_or_create(basket=basket, product_id=product_id)

            if created:
                item.count = count
            else:
                item.count += count
            item.save()

            items = basket.items.select_related('product__category').prefetch_related(
                'product__images', 'product__tags', 'product__specifications', 'product__reviews'
            )
            serializer = BasketItemSerializer(items, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            cart = request.session.get('cart', {})
            pid_str = str(product_id)
            cart[pid_str] = cart.get(pid_str, 0) + count
            request.session['cart'] = cart

            products = Product.objects.filter(id__in=cart.keys()).select_related('category').prefetch_related(
                'images', 'tags', 'specifications', 'reviews'
            )
            cart_data = [{"product": product, "count": cart[str(product.id)]} for product in products]
            serializer = SessionBasketItemSerializer(cart_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        product_id = request.data.get("id")
        count_to_remove = request.data.get("count")

        if not product_id:
            return Response({"detail": "Product id is required"}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            basket, _ = Basket.objects.get_or_create(user=request.user)

            try:
                item = BasketItem.objects.get(basket=basket, product_id=product_id)
            except BasketItem.DoesNotExist:
                return Response({"detail": "Item not found in basket"}, status=status.HTTP_404_NOT_FOUND)

            if count_to_remove is None or item.count <= count_to_remove:
                item.delete()
            else:
                item.count -= count_to_remove
                item.save()

            items = basket.items.select_related('product__category').prefetch_related(
                'product__images', 'product__tags', 'product__specifications', 'product__reviews'
            )
            serializer = BasketItemSerializer(items, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            cart = request.session.get('cart', {})
            pid_str = str(product_id)

            if pid_str in cart:
                if count_to_remove is None or cart[pid_str] <= count_to_remove:
                    del cart[pid_str]
                else:
                    cart[pid_str] -= count_to_remove

                request.session['cart'] = cart

            products = Product.objects.filter(id__in=cart.keys()).select_related('category').prefetch_related(
                'images', 'tags', 'specifications', 'reviews'
            )
            cart_data = [{"product": product, "count": cart[str(product.id)]} for product in products]
            serializer = SessionBasketItemSerializer(cart_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)