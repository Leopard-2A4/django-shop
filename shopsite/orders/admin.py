from django.contrib import admin
from .models import Order, OrderProduct


class SoftDeleteAdminMixin:
    """
    Миксин, который заставляет админку показывать ВСЕ объекты,
    включая архивированные (игнорируя фильтрацию в manager.objects).
    """

    def get_queryset(self, request):
        return self.model.all_objects.all()


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    can_delete = False  # Запрещаем удаление через inline, используем soft delete
    extra = 0  # Не показываем пустые формы
    verbose_name = "Товар в заказе"
    verbose_name_plural = "Товары в заказе"

    # archived — первое поле
    fields = ('archived', 'product', 'title', 'count', 'price', 'category', 'date')
    readonly_fields = ('date',)  # Дату менять нельзя

    # Показываем только необходимые поля для компактности
    def get_queryset(self, request):
        # Показываем все товары, включая архивированные
        return super().get_queryset(request)


@admin.register(Order)
class OrderAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    # archived — ПЕРВОЕ поле на детальной странице через fieldsets
    fieldsets = (
        ('Статус заказа', {
            'fields': ('archived', 'status', 'step'),
            'description': 'Управляйте статусом и архивацией заказа',
        }),
        ('Информация о клиенте', {
            'fields': ('user', 'full_name', 'email', 'phone'),
        }),
        ('Доставка', {
            'fields': ('delivery_type', 'city', 'address'),
        }),
        ('Оплата и стоимость', {
            'fields': ('payment_type', 'total_cost', 'created_at'),
        }),
    )

    readonly_fields = ('created_at',)  # Дата создания автоматически

    list_display = ('id', 'full_name', 'email', 'status', 'step', 'total_cost', 'archived', 'created_at')
    list_display_links = ('id', 'full_name')
    list_filter = ('archived', 'status', 'step', 'delivery_type', 'payment_type')
    search_fields = ('full_name', 'email', 'phone', 'city', 'address', 'user__username')
    list_editable = ('archived', 'status')  # Можно менять статус и архивацию прямо из списка

    inlines = [OrderProductInline]

    # Сортировка: новые заказы сверху
    ordering = ('-created_at',)

    # Массовые действия
    actions = ['soft_delete_selected', 'restore_selected', 'recalculate_totals']

    @admin.action(description='Мягко удалить выбранные заказы')
    def soft_delete_selected(self, request, queryset):
        for order in queryset:
            order.soft_delete()
        self.message_user(request, f'{queryset.count()} заказов архивировано.')

    @admin.action(description='Восстановить выбранные заказы')
    def restore_selected(self, request, queryset):
        for order in queryset:
            order.restore()
        self.message_user(request, f'{queryset.count()} заказов восстановлено.')

    @admin.action(description='Пересчитать итоговую стоимость')
    def recalculate_totals(self, request, queryset):
        count = 0
        for order in queryset:
            order.recalculate_total()
            order.save()
            count += 1
        self.message_user(request, f'Пересчитано {count} заказов.')


@admin.register(OrderProduct)
class OrderProductAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    # archived — ПЕРВОЕ поле
    fields = ('archived', 'order', 'product', 'title', 'description', 'full_description',
              'price', 'category', 'free_delivery', 'rating', 'count', 'date')

    list_display = ('__str__', 'order', 'product', 'count', 'price', 'archived', 'date')
    list_filter = ('archived', 'order')
    search_fields = ('title', 'description', 'order__full_name', 'product__title')
    readonly_fields = ('date',)
    list_editable = ('archived',)