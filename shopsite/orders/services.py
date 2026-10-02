from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Order, OrderProduct
from shopproducts.models import Product


def calc_delivery(goods_total, delivery_type):
    if delivery_type == 'express':
        delivery_cost = Decimal('500')
    elif delivery_type == 'ordinary':
        delivery_cost = Decimal('0') if goods_total >= Decimal('2000') else Decimal('200')
    else:
        delivery_cost = Decimal('0')
    return delivery_cost


def _build_product_payload(item):
    """Формирует ответ для одного товара в заказе."""
    images = [
        {
            'src': img.src.url if img.src else '',
            'alt': img.alt or item.title,
        }
        for img in item.product.images.all()
    ]

    return {
        'id': item.product_id,
        'title': item.title,
        'price': float(item.price),
        'count': item.count,
        'category': item.category.title if item.category_id else None,
        'images': images,
        'shortDescription': item.product.description,
    }


def order_payload(order: Order) -> dict:
    """Формирует полный ответ для одного заказа."""

    items = (
        order.shopproducts
        .select_related('product', 'category')
        .prefetch_related('product__images')
    )

    products_payload = []
    goods_total = Decimal('0')

    print(f"\n=== DEBUG order_payload for Order #{order.id} ===")

    for item in items:
        item_total = item.price * item.count
        goods_total += item_total
        print(f"  Item: {item.title}, price={item.price}, count={item.count}, item_total={item_total}")
        products_payload.append(_build_product_payload(item))

    print(f"Goods total: {goods_total}")

    delivery_type = order.delivery_type or 'ordinary'
    delivery_cost = calc_delivery(goods_total, delivery_type)
    total_cost = goods_total + delivery_cost

    print(f"Delivery type: {delivery_type}, delivery cost: {delivery_cost}, total cost: {total_cost}")
    print(f"Order total_cost from DB: {order.total_cost}")
    print("=" * 50)

    return {
        'id': order.id,
        'createdAt': timezone.localtime(order.created_at).strftime('%Y-%m-%d %H:%M'),
        'fullName': order.full_name,
        'email': order.email,
        'phone': order.phone,
        'deliveryType': delivery_type,
        'paymentType': order.payment_type or 'card',
        'totalCost': float(total_cost),
        'status': order.status,
        'city': order.city or '',
        'address': order.address or '',
        'products': products_payload,
    }


@transaction.atomic
def create_order_from_basket(request, products_payload=None):
    """Создаёт заказ из корзины."""

    print(f"\n=== DEBUG create_order_from_basket ===")
    print(f"User: {request.user}")
    print(f"Products payload: {products_payload}")

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        status='new',
        step='user_info',
        total_cost=Decimal('0'),
    )
    print(f"Created order ID: {order.id}")

    order_products = []
    goods_total = Decimal('0')

    if products_payload and isinstance(products_payload, list):
        print(f"Using products_payload: {len(products_payload)} items")
        product_ids = [int(row.get('id')) for row in products_payload if row.get('id')]
        products_map = {
            p.id: p
            for p in Product.objects.filter(pk__in=product_ids, available=True)
        }

        for row in products_payload:
            product = products_map.get(int(row.get('id', 0)))
            if not product:
                print(f"  Product {row.get('id')} not found or not available")
                continue

            count = int(row.get('count') or 1)
            print(f"  Adding: {product.title}, price={product.price}, count={count}")

            order_products.append(OrderProduct(
                order=order,
                product=product,
                title=product.title,
                description=product.description,
                full_description=product.full_description,
                price=product.price,
                category=product.category,
                free_delivery=product.free_delivery,
                rating=product.rating,
                count=count,
            ))
            goods_total += product.price * count

    else:
        from basket.models import Basket
        basket_items = (
            Basket.objects
            .filter(user=request.user)
            .select_related('product', 'product__category')
        )
        print(f"Using basket: {basket_items.count()} items")

        for item in basket_items:
            if not item.product.available:
                print(f"  Product {item.product.id} not available")
                continue

            print(f"  Adding: {item.product.title}, count={item.count}, price={item.product.price}")

            order_products.append(OrderProduct(
                order=order,
                product=item.product,
                title=item.product.title,
                description=item.product.description,
                full_description=item.product.full_description,
                price=item.product.price,
                category=item.product.category,
                free_delivery=item.product.free_delivery,
                rating=item.product.rating,
                count=item.count,
            ))
            goods_total += item.product.price * item.count

        Basket.objects.filter(user=request.user).delete()
        print(f"Basket cleared")

    if order_products:
        OrderProduct.objects.bulk_create(order_products)

    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            order.full_name = (
                    profile.full_name
                    or f"{profile.user.first_name} {profile.user.last_name}".strip()
            )
            order.email = profile.user.email or request.user.email
            order.phone = profile.phone

    # На этом этапе delivery_type ещё не установлен, поэтому сохраняем только goods_total
    order.total_cost = goods_total
    order.save(update_fields=['full_name', 'email', 'phone', 'total_cost'])

    print(f"\nFinal summary:")
    print(f"  Products added: {len(order_products)}")
    print(f"  Goods total: {goods_total}")
    print(f"  Order total_cost saved: {order.total_cost}")
    print("=" * 50)

    return order


def confirm_order(order: Order, data: dict) -> Order:
    """Подтверждает заказ (шаг 4)."""

    print(f"\n=== DEBUG confirm_order for Order #{order.id} ===")

    items = order.shopproducts.select_related('product').all()

    goods_total = Decimal('0')
    for item in items:
        item_total = item.price * item.count
        goods_total += item_total
        print(f"  Item: {item.title}, price={item.price}, count={item.count}, item_total={item_total}")

    print(f"Goods total: {goods_total}")

    delivery_type = data.get('deliveryType') or order.delivery_type or 'ordinary'
    delivery_cost = calc_delivery(goods_total, delivery_type)
    total_cost = goods_total + delivery_cost

    print(f"Delivery type: {delivery_type}, delivery cost: {delivery_cost}, total cost: {total_cost}")

    order.full_name = data.get('fullName') or order.full_name
    order.email = data.get('email') or order.email
    order.phone = data.get('phone') or order.phone
    order.delivery_type = delivery_type
    order.payment_type = data.get('paymentType') or order.payment_type
    order.city = data.get('city') or order.city
    order.address = data.get('address') or order.address
    order.total_cost = total_cost
    order.status = 'accepted'

    order.save()

    print(f"Order saved with total_cost: {order.total_cost}")
    print("=" * 50)

    return order