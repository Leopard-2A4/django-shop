from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
# Create your models here.

def validate_image_size(src):
    max_size = 2 * 1024 * 1024
    if src.size > max_size:
        return ValidationError("Размер изображения долженн быть меньше 2 МБ")

class SoftDeleteManager(models.Manager):
    """
    Менеджер для мягкого удаления.
    Возвращает только объекты с archived=False.
    """
    def get_queryset(self):
        return super().get_queryset().filter(archived=False)

    def all_with_deleted(self):
        """
        Получить все объекты, включая удалённые.
        """
        return super().get_queryset()

    def deleted_only(self):
        """
        Получить только удалённые объекты.
        """
        return super().get_queryset().filter(archived=True)

class Avatar(models.Model):
    profile = models.OneToOneField(
        "Profile",
        on_delete=models.CASCADE,
        related_name="avatar",
        null=True,
        blank=True,
    )
    src = models.ImageField(upload_to="avatars/", validators=[validate_image_size])
    alt = models.CharField(max_length=255, blank=True)
    archived = models.BooleanField(default=False)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.archived = True
        self.save()

    def restore(self):

        self.archived = False
        self.save()

    def __str__(self):
        return self.alt or f"Image {self.pk}"


class Profile (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    archived = models.BooleanField(default=False)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.archived = True
        if hasattr(self, "avatar"):
            self.avatar.soft_delete()
        self.save()

    def restore(self):

        self.archived = False
        if hasattr(self, "avatar"):
            self.avatar.restore()
        self.save()


def avatars_image_directory_path(instance: Profile, filename: str):
    pk = instance.user.pk
    return f"avatars/user_{pk}images/{filename}"