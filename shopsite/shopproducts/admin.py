from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Image, Specification, Tag, Review


class SoftDeleteAdminMixin:
    """
    Миксин, который заставляет админку показывать ВСЕ объекты,
    включая архивированные (игнорируя фильтрацию в manager.objects).
    """
    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    fields = ('archived', 'title', 'parent', 'src', 'alt')

    list_display = ('title', 'parent', 'image_thumbnail', 'archived')
    list_filter = ('archived', 'parent')
    search_fields = ('title',)
    list_editable = ('archived',)

    def image_thumbnail(self, obj):
        if obj.src:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.src.url
            )
        return "Нет изображения"

    image_thumbnail.short_description = "Картинка"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


@admin.register(Product)
class ProductAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    fieldsets = (
        ('Статус и доступность', {
            'fields': ('available',),
            'description': 'Снимите галочку, чтобы скрыть товар (мягкое удаление)',
        }),
        ('Основная информация', {
            'fields': ('title', 'category', 'description', 'full_description'),
        }),
        ('Ценообразование и скидки', {
            'fields': ('price', 'discount', 'sale_date_from', 'sale_date_to'),
        }),
        ('Наличие и характеристики', {
            'fields': ('count', 'rating', 'free_delivery', 'limited_edition', 'date'),
        }),
    )

    readonly_fields = ('date', 'rating')

    list_display = ('title', 'category', 'price', 'available', 'count', 'limited_edition')
    list_filter = ('available', 'category', 'limited_edition', 'free_delivery')
    search_fields = ('title', 'description', 'full_description')
    list_editable = ('available', 'price', 'count')


@admin.register(Image)
class ImageAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    fields = ('archived', 'product', 'src', 'alt')

    list_display = ('__str__', 'product', 'archived')
    list_filter = ('archived', 'product')
    search_fields = ('alt', 'product__title')


@admin.register(Specification)
class SpecificationAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    fields = ('archived', 'product', 'name', 'value')

    list_display = ('__str__', 'product', 'archived')
    list_filter = ('archived', 'product')
    search_fields = ('name', 'value', 'product__title')


@admin.register(Tag)
class TagAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    fields = ('archived', 'product', 'name')

    list_display = ('name', 'product', 'archived')
    list_filter = ('archived', 'product')
    search_fields = ('name', 'product__title')


@admin.register(Review)
class ReviewAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    fields = ('archived', 'product', 'author', 'text', 'rate', 'date')

    list_display = ('__str__', 'product', 'author', 'rate', 'archived', 'date')
    list_filter = ('archived', 'rate', 'product')
    search_fields = ('text', 'author__username', 'product__title')
    readonly_fields = ('date',)