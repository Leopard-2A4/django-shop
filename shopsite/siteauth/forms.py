from django import forms
from django.contrib.auth.models import User


class UserUpdateForm(forms.ModelForm):
    avatar = forms.ImageField(required=False)
    name = forms.CharField(required=True)
    class Meta:
        model = User
        fields = (
            "name"
            "username",
        )

    def save(self, commit=True):
        user = super().save(commit)

        profile = user.profile
        
        profile.save()

        return user