from django.urls import re_path
from .views import SignInView, SignUpView, SignOutView

app_name = "siteauth"

urlpatterns = [
    re_path("sign-in/?$", SignInView.as_view(), name="sign-in"),
    re_path("sign-up/?$", SignUpView.as_view(), name="sign-up"),
    re_path("sign-out/?$", SignOutView.as_view(), name="sign-out"),
]