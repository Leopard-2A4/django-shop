from django.contrib import admin
from .models import Profile, Avatar


class SoftDeleteAdminMixin:
    """
    Миксин, который заставляет админку показывать ВСЕ объекты,
    включая архивированные (игнорируя фильтрацию в manager.objects).
    """

    def get_queryset(self, request):
        return self.model.all_objects.all()



class AvatarInline(admin.StackedInline):
    model = Avatar
    can_delete = False  # Запрещаем удаление через inline, используем soft delete
    verbose_name = "Аватар"
    verbose_name_plural = "Аватар"
    fk_name = "profile"  # Указываем внешний ключ явно

    # archived — первое поле
    fields = ('archived', 'src', 'alt')

    def has_add_permission(self, request, obj=None):
        # Разрешаем добавление только если у профиля еще нет аватара
        if obj and hasattr(obj, 'avatar'):
            return False
        return True


@admin.register(Profile)
class ProfileAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    # archived — ПЕРВОЕ поле на детальной странице
    fields = ('archived', 'user', 'full_name', 'phone')

    list_display = ('full_name', 'user', 'phone', 'archived')
    list_filter = ('archived',)
    search_fields = ('full_name', 'phone', 'user__username', 'user__email')
    list_editable = ('archived',)  # Можно архивировать прямо из списка

    inlines = [AvatarInline]

    # readonly_fields = ('user',)  # Раскомментируй, если не хочешь, чтобы user можно было менять

    # Массовые действия для мягкого удаления/восстановления
    actions = ['soft_delete_selected', 'restore_selected']

    @admin.action(description='Мягко удалить выбранные профили')
    def soft_delete_selected(self, request, queryset):
        for profile in queryset:
            profile.soft_delete()  # Вызываем метод модели, который каскадно удалит аватар
        self.message_user(request, f'{queryset.count()} профилей архивировано.')

    @admin.action(description='Восстановить выбранные профили')
    def restore_selected(self, request, queryset):
        for profile in queryset:
            profile.restore()  # Вызываем метод модели, который каскадно восстановит аватар
        self.message_user(request, f'{queryset.count()} профилей восстановлено.')


@admin.register(Avatar)
class AvatarAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    # archived — ПЕРВОЕ поле
    fields = ('archived', 'profile', 'src', 'alt')

    list_display = ('__str__', 'profile', 'archived')
    list_filter = ('archived',)
    search_fields = ('alt', 'profile__full_name', 'profile__user__username')
    list_editable = ('archived',)