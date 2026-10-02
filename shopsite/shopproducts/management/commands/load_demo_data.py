from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shopproducts.models import Category, Product, Image, Specification, Tag, Review
from siteauth.models import Profile
from orders.models import Order, OrderProduct
from decimal import Decimal
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Загружает демонстрационные данные для тестирования'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начинаю загрузку демонстрационных данных...')

        # ==========================================
        # 1. ПОЛЬЗОВАТЕЛИ (покупатели и продавцы)
        # ==========================================
        self.stdout.write('Создаю пользователей...')

        # Создаем покупателей
        buyers_data = [
            {'username': 'buyer1', 'email': 'buyer1@example.com', 'first_name': 'Иван', 'last_name': 'Петров',
             'phone': '+79001111111'},
            {'username': 'buyer2', 'email': 'buyer2@example.com', 'first_name': 'Мария', 'last_name': 'Сидорова',
             'phone': '+79002222222'},
            {'username': 'buyer3', 'email': 'buyer3@example.com', 'first_name': 'Алексей', 'last_name': 'Козлов',
             'phone': '+79003333333'},
            {'username': 'buyer4', 'email': 'buyer4@example.com', 'first_name': 'Елена', 'last_name': 'Волкова',
             'phone': '+79004444444'},
        ]

        buyers = []
        for data in buyers_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            if created:
                user.set_password('123456')  # Простой пароль для тестирования
                user.save()

                # Создаем профиль
                Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'full_name': f"{data['first_name']} {data['last_name']}",
                        'phone': data['phone'],
                    }
                )
            buyers.append(user)

        # Создаем продавцов (staff users)
        sellers_data = [
            {'username': 'seller1', 'email': 'seller1@example.com', 'first_name': 'Дмитрий', 'last_name': 'Продавец'},
            {'username': 'seller2', 'email': 'seller2@example.com', 'first_name': 'Ольга', 'last_name': 'Менеджер'},
        ]

        sellers = []
        for data in sellers_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_staff': True,  # Продавцы - это staff
                }
            )
            if created:
                user.set_password('123456')
                user.save()
            sellers.append(user)

        # Создаем суперпользователя
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь: admin / admin123'))

        self.stdout.write(self.style.SUCCESS(f'Создано {len(buyers)} покупателей и {len(sellers)} продавцов'))

        # ==========================================
        # 2. КАТЕГОРИИ
        # ==========================================
        self.stdout.write('Создаю категории...')

        # Родительские категории
        electronics, _ = Category.objects.get_or_create(title='Электроника')
        computers, _ = Category.objects.get_or_create(title='Компьютеры', parent=electronics)
        drones, _ = Category.objects.get_or_create(title='Дроны', parent=electronics)
        components, _ = Category.objects.get_or_create(title='Комплектующие', parent=electronics)

        self.stdout.write(self.style.SUCCESS('Создано 4 категории'))

        # ==========================================
        # 3. ТОВАРЫ
        # ==========================================
        self.stdout.write('Создаю товары...')

        products_data = [
            {
                'title': 'Ноутбук ASUS ZenBook Pro 15',
                'category': computers,
                'description': 'Мощный ноутбук с сенсорным экраном и стилусом',
                'full_description': 'Профессиональный ноутбук с 15.6" OLED дисплеем, поддержкой стилуса ASUS Pen для рисования и заметок. Идеален для дизайнеров и художников.',
                'price': Decimal('149990.00'),
                'discount': 10,
                'count': 25,
                'rating': Decimal('4.7'),
                'free_delivery': True,
                'limited_edition': False,
                'available': True,
                'sale_date_from': date.today(),
                'sale_date_to': date.today() + timedelta(days=30),
            },
            {
                'title': 'Ноутбук Microsoft Surface Laptop Studio',
                'category': computers,
                'description': 'Трансформер с поддержкой стилуса Surface Pen',
                'full_description': 'Уникальный ноутбук-трансформер с откидным экраном и поддержкой стилуса Surface Slim Pen. Идеален для творчества и работы.',
                'price': Decimal('189990.00'),
                'discount': 5,
                'count': 15,
                'rating': Decimal('4.8'),
                'free_delivery': True,
                'limited_edition': True,
                'available': True,
            },
            {
                'title': 'Дрон DJI Mavic 3 Pro',
                'category': drones,
                'description': 'Профессиональный дрон с тройной камерой',
                'full_description': 'Флагманский дрон с тройной камерой Hasselblad, 46 минут полета и дальностью до 15 км. Снимайте в качестве 5.1K.',
                'price': Decimal('179990.00'),
                'discount': 0,
                'count': 10,
                'rating': Decimal('4.9'),
                'free_delivery': True,
                'limited_edition': False,
                'available': True,
            },
            {
                'title': 'Видеокарта NVIDIA RTX 4090',
                'category': components,
                'description': 'Флагманская видеокарта для игр и работы',
                'full_description': 'Мощнейшая видеокарта с 24 ГБ GDDR6X памяти. Поддержка DLSS 3.0 и трассировки лучей. Идеальна для 4K гейминга и 3D рендеринга.',
                'price': Decimal('199990.00'),
                'discount': 15,
                'count': 8,
                'rating': Decimal('4.9'),
                'free_delivery': True,
                'limited_edition': True,
                'available': True,
                'sale_date_from': date.today(),
                'sale_date_to': date.today() + timedelta(days=14),
            },
        ]

        products = []
        for data in products_data:
            product, created = Product.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            products.append(product)

        self.stdout.write(self.style.SUCCESS(f'Создано {len(products)} товаров'))

        # ==========================================
        # 4. ИЗОБРАЖЕНИЯ ТОВАРОВ
        # ==========================================
        self.stdout.write('Добавляю изображения...')

        # Пути к твоим изображениям (измени под свои файлы)
        images_data = [
            {'product': products[0], 'src': 'products/photo_2026-09-01_21-47-10.jpg',
             'alt': 'Ноутбук ASUS ZenBook Pro 15 со стилусом'},
            {'product': products[1], 'src': 'products/photo_2026-09-01_21-47-36.jpg',
             'alt': 'Ноутбук Microsoft Surface Laptop Studio со стилусом'},
            {'product': products[2], 'src': 'products/photo_2026-09-01_21-46-42.jpg',
             'alt': 'Дрон DJI Mavic 3 Pro'},
            {'product': products[3], 'src': 'products/photo_2026-09-01_21-46-03.jpg',
             'alt': 'Видеокарта NVIDIA RTX 4090'},
        ]

        for data in images_data:
            Image.objects.get_or_create(
                product=data['product'],
                defaults={
                    'src': data['src'],
                    'alt': data['alt'],
                }
            )

        self.stdout.write(self.style.SUCCESS('Добавлены изображения для товаров'))

        # ==========================================
        # 5. ХАРАКТЕРИСТИКИ ТОВАРОВ
        # ==========================================
        self.stdout.write('Добавляю характеристики...')

        specs_data = [
            # Ноутбук ASUS
            {'product': products[0], 'name': 'Диагональ экрана', 'value': '15.6"'},
            {'product': products[0], 'name': 'Процессор', 'value': 'Intel Core i9-13900H'},
            {'product': products[0], 'name': 'Оперативная память', 'value': '32 GB'},
            {'product': products[0], 'name': 'Видеокарта', 'value': 'NVIDIA RTX 4070'},
            {'product': products[0], 'name': 'Стилус', 'value': 'ASUS Pen в комплекте'},

            # Ноутбук Surface
            {'product': products[1], 'name': 'Диагональ экрана', 'value': '14.4"'},
            {'product': products[1], 'name': 'Процессор', 'value': 'Intel Core i7-13700H'},
            {'product': products[1], 'name': 'Оперативная память', 'value': '32 GB'},
            {'product': products[1], 'name': 'Стилус', 'value': 'Surface Slim Pen 2'},
            {'product': products[1], 'name': 'Форм-фактор', 'value': 'Трансформер'},

            # Дрон
            {'product': products[2], 'name': 'Время полета', 'value': '46 минут'},
            {'product': products[2], 'name': 'Дальность', 'value': '15 км'},
            {'product': products[2], 'name': 'Камера', 'value': 'Тройная Hasselblad'},
            {'product': products[2], 'name': 'Разрешение видео', 'value': '5.1K'},
            {'product': products[2], 'name': 'Вес', 'value': '958 г'},

            # Видеокарта
            {'product': products[3], 'name': 'Память', 'value': '24 GB GDDR6X'},
            {'product': products[3], 'name': 'Частота ядра', 'value': '2520 МГц'},
            {'product': products[3], 'name': 'CUDA ядра', 'value': '16384'},
            {'product': products[3], 'name': 'Интерфейс', 'value': 'PCIe 4.0 x16'},
            {'product': products[3], 'name': 'TDP', 'value': '450W'},
        ]

        for data in specs_data:
            Specification.objects.get_or_create(**data)

        self.stdout.write(self.style.SUCCESS('Добавлены характеристики'))

        # ==========================================
        # 6. ТЕГИ ТОВАРОВ
        # ==========================================
        self.stdout.write('Добавляю теги...')

        tags_data = [
            {'product': products[0], 'name': 'со стилусом'},
            {'product': products[0], 'name': 'для дизайнеров'},
            {'product': products[1], 'name': 'трансформер'},
            {'product': products[1], 'name': 'со стилусом'},
            {'product': products[1], 'name': 'лимитированная серия'},
            {'product': products[2], 'name': 'профессиональный'},
            {'product': products[2], 'name': '4K видео'},
            {'product': products[3], 'name': 'флагман'},
            {'product': products[3], 'name': 'для 4K гейминга'},
            {'product': products[3], 'name': 'распродажа'},
        ]

        for data in tags_data:
            Tag.objects.get_or_create(**data)

        self.stdout.write(self.style.SUCCESS('Добавлены теги'))

        # ==========================================
        # 7. ОТЗЫВЫ
        # ==========================================
        self.stdout.write('Добавляю отзывы...')

        reviews_data = [
            {'product': products[0], 'author': buyers[0],
             'text': 'Отличный ноутбук для рисования! Стилус работает идеально.', 'rate': 5},
            {'product': products[0], 'author': buyers[1],
             'text': 'Мощная машина, но тяжеловат.', 'rate': 4},
            {'product': products[1], 'author': buyers[2],
             'text': 'Невероятный трансформер, очень удобный для работы.',
             'rate': 5},
            {'product': products[2], 'author': buyers[0],
             'text': 'Дрон просто космос! Качество съемки потрясающее.',
             'rate': 5},
            {'product': products[2], 'author': buyers[3],
             'text': 'Летает долго, батарея держит отлично.', 'rate': 4},
            {'product': products[3], 'author': buyers[1],
             'text': 'Тянет все игры на ультра настройках в 4K!',
             'rate': 5},
            {'product': products[3], 'author': buyers[2],
             'text': 'Для 3D рендеринга - идеальна.', 'rate': 5},
        ]

        for data in reviews_data:
            Review.objects.get_or_create(
                product=data['product'],
                author=data['author'],
                defaults={
                    'text': data['text'],
                    'rate': data['rate'],
                }
            )

        self.stdout.write(self.style.SUCCESS('Добавлены отзывы'))

        # ==========================================
        # 8. ЗАКАЗЫ
        # ==========================================
        self.stdout.write('Создаю заказы...')

        # Заказ 1: Покупатель 1 покупает ноутбук ASUS
        order1, created = Order.objects.get_or_create(
            user=buyers[0],
            full_name='Иван Петров',
            defaults={
                'email': 'buyer1@example.com',
                'phone': '+79001111111',
                'delivery_type': 'express',
                'payment_type': 'card',
                'status': 'confirmed',
                'city': 'Москва',
                'address': 'ул. Ленина, д. 1, кв. 1',
                'step': 'confirmed',
                'total_cost': 0,  # <-- ДОБАВЛЕНО: начальное значение
            }
        )
        if created:
            OrderProduct.objects.create(
                order=order1,
                product=products[0],
                title=products[0].title,
                description=products[0].description,
                full_description=products[0].full_description,
                price=products[0].price,
                category=products[0].category,
                free_delivery=products[0].free_delivery,
                rating=products[0].rating,
                count=1,
            )
            order1.recalculate_total()
            order1.save()

        # Заказ 2: Покупатель 2 покупает дрон
        order2, created = Order.objects.get_or_create(
            user=buyers[1],
            full_name='Мария Сидорова',
            defaults={
                'email': 'buyer2@example.com',
                'phone': '+79002222222',
                'delivery_type': 'ordinary',
                'payment_type': 'cash',
                'status': 'processing',
                'city': 'Санкт-Петербург',
                'address': 'Невский проспект, д. 10',
                'step': 'confirmed',
                'total_cost': 0,  # <-- ДОБАВЛЕНО
            }
        )
        if created:
            OrderProduct.objects.create(
                order=order2,
                product=products[2],
                title=products[2].title,
                description=products[2].description,
                full_description=products[2].full_description,
                price=products[2].price,
                category=products[2].category,
                free_delivery=products[2].free_delivery,
                rating=products[2].rating,
                count=1,
            )
            order2.recalculate_total()
            order2.save()

        # Заказ 3: Покупатель 3 покупает видеокарту
        order3, created = Order.objects.get_or_create(
            user=buyers[2],
            full_name='Алексей Козлов',
            defaults={
                'email': 'buyer3@example.com',
                'phone': '+79003333333',
                'delivery_type': 'express',
                'payment_type': 'card',
                'status': 'delivered',
                'city': 'Новосибирск',
                'address': 'ул. Красный проспект, д. 50',
                'step': 'confirmed',
                'total_cost': 0,  # <-- ДОБАВЛЕНО
            }
        )
        if created:
            OrderProduct.objects.create(
                order=order3,
                product=products[3],
                title=products[3].title,
                description=products[3].description,
                full_description=products[3].full_description,
                price=products[3].price,
                category=products[3].category,
                free_delivery=products[3].free_delivery,
                rating=products[3].rating,
                count=1,
            )
            order3.recalculate_total()
            order3.save()

        self.stdout.write(self.style.SUCCESS('Создано 3 заказа'))

        # ==========================================
        # ИТОГ
        # ==========================================
        self.stdout.write(self.style.SUCCESS('\nДемонстрационные данные успешно загружены!'))
        self.stdout.write(self.style.SUCCESS('\nСтатистика:'))
        self.stdout.write(f'  - Пользователей: {User.objects.count()}')
        self.stdout.write(f'  - Категорий: {Category.objects.count()}')
        self.stdout.write(f'  - Товаров: {Product.objects.count()}')
        self.stdout.write(f'  - Заказов: {Order.objects.count()}')
        self.stdout.write(f'  - Отзывов: {Review.objects.count()}')

        self.stdout.write(self.style.SUCCESS('\nДанные для входа:'))
        self.stdout.write('  Покупатели (пароль: 123456):')
        self.stdout.write('    - buyer1 / buyer2 / buyer3 / buyer4')
        self.stdout.write('  Продавцы (пароль: 123456):')
        self.stdout.write('    - seller1 / seller2')
        self.stdout.write('  Администратор:')
        self.stdout.write('    - admin / admin123')
