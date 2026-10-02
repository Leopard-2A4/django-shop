from .models import Basket, BasketItem


def merge_session_cart_to_db(user, session_cart: dict):
    """
    Переносит товары из сессионной корзины в корзину пользователя в БД.
    session_cart имеет вид: {'product_id': count, ...}
    """
    if not session_cart:
        return

    basket, _ = Basket.objects.get_or_create(user=user)

    for product_id_str, count in session_cart.items():
        product_id = int(product_id_str)

        item, created = BasketItem.objects.get_or_create(
            basket=basket,
            product_id=product_id
        )

        if not created:
            item.count += count
        else:
            item.count = count

        item.save()