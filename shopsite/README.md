# Интернет-магазин Megano (Django REST Framework)

Дипломный проект Skillbox: Django-бэкенд для готового фронтенда.
Фронтенд подключается как pip-пакет и **не изменяется**. Вся бизнес-логика, API и работа с базой данных реализованы на
бэкенде.

## 📁 Структура проекта

python_django_diploma/
├── diploma-frontend/ # Исходники фронтенда (не модифицируются)
├── shopsite/ # Основной Django-проект (бэкенд)
│ ├── basket/ # Приложение корзины
│ ├── catalog/ # Приложение каталога
│ ├── orders/ # Приложение заказов
│ ├── payment/ # Приложение оплаты
│ ├── shopproducts/ # Приложение товаров (Product, Category, Image, Tag, Review)
│ ├── siteauth/ # Приложение авторизации
│ ├── tag/ # Приложение тегов
│ ├── userprofile/ # Приложение профиля пользователя
│ ├── manage.py
│ ── settings.py
├── requirements.txt
└── README.md

## GitFlow

Проект строго следует методологии GitFlow:

- Ветка `master` — основная стабильная ветка.
- Ветка `release` — создается от `master`, является основной веткой для разработки и тестирования.
- Ветки `feature/*` — создаются **только от ветки `release`** для новых задач.
- Слияние (Merge Request) ветки `feature/*` в `release` выполняется **только после одобрения куратора**.

## 🚀 Развёртывание и запуск

   ```bash
   cd ~/PycharmProjects/python_django_diploma/shopsite/
   python3 -m venv .venv
   source .venv/bin/activate  # Для Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install ./diploma-frontend/dist/diploma-frontend-0.6.tar.gz
   python manage.py migrate
   python manage.py load_demo_data
   python manage.py runserver 8000
   ```

## Учётные записи

| Логин   | Пароль   | Роль                      |
|---------|----------|---------------------------|
| admin   | admin123 | Администратор (Superuser) |
| buyer1  | 123456   | Покупатель                |
| buyer2  | 123456   | Покупатель                |
| seller1 | 123456   | Продавец (Staff)          |

- Магазин: http://127.0.0.1:8000/
- Админка: http://127.0.0.1:8000/admin/
- Swagger: http://127.0.0.1:8000/swagger/
- Схема: http://127.0.0.1:8000/api/schema/

## 🛒 Логика работы корзины

Реализована в строгом соответствии с требованиями:
Неавторизованный пользователь (Гость): товары хранятся только в Django-сессии. Это предотвращает засорение базы данных "
мусорными" записями.
Авторизованный пользователь: товары хранятся в базе данных (модель Basket), что позволяет видеть актуальную корзину с
любого устройства.
Слияние (Merge): при входе или регистрации пользователя данные из сессионной корзины автоматически переносятся в корзину
базы данных, после чего сессия очищается.

## 📦 Основные команды управления

```bash
# Загрузка демо-данных (пользователи, товары, заказы)
python manage.py load_demo_data

# Создание миграций после изменения моделей
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя вручную
python manage.py createsuperuser

```

## API Контракт

Бэкенд реализует API в строгом соответствии с контрактом фронтенда (swagger.yaml).
Основные группы эндпоинтов:
/api/sign-in/, /api/sign-up/ — Авторизация и регистрация
/api/categories/, /api/catalog/, /api/product/ — Каталог и товары
/api/basket/ — Управление корзиной
/api/orders/, /api/payment/ — Заказы и оплата
/api/profile/ — Управление профилем пользователя