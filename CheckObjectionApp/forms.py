from django import forms
from django.contrib.auth import get_user_model
User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(error_messages={"required":'请传入邮箱!','invalid':'请传入一个正确的邮箱!'})
    password = forms.CharField(max_length=20, min_length=6)
    remember = forms.IntegerField(required=False)