from django.urls import path
from .views import UserProfileView, ChangeAvatarView, ChangePasswordView

app_name = "userprofile"

urlpatterns = [
    path("profile", UserProfileView.as_view(), name="profile"),
    path("profile/avatar", ChangeAvatarView.as_view(), name="change-avatar"),
    path("profile/password", ChangePasswordView.as_view(), name="change-password"),
]