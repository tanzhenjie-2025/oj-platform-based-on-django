from hashlib import md5
from django.contrib.auth.hashers import make_password
from django import forms
from django.contrib.auth import get_user_model
User = get_user_model()


# 需要传入验证码的登录表单
# class LoginForm(forms.Form):
#     username= forms.CharField(
#         required=True,
#         max_length=20,
#         error_messages={
#             "required":'请传入用户名或邮箱!',
#             'invalid':'请传入一个正确的用户名或邮箱邮箱!'}
#     )
#     password = forms.CharField(
#         required=True,
#         error_messages={"required":'请传入密码!'},
#     )
#     remember = forms.IntegerField(
#         required=False
#     )
# #     验证码
#     captcha = forms.CharField(
#         required=True,
#         error_messages={"required":'请输入验证码!'}
#     )

    # def clean_password(self):
    #     password = self.cleaned_data.get('password')
    #     return make_password(password)
from django import forms

from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        label="用户名或邮箱",
        widget=forms.TextInput(attrs={
            'placeholder': '请输入用户名或邮箱',
            'required': 'required',
            'class': 'form-control'  # 直接添加CSS类
        })
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={
            'placeholder': '请输入密码',
            'required': 'required',
            'class': 'form-control'  # 直接添加CSS类
        })
    )
    captcha = forms.CharField(
        label="验证码",
        widget=forms.TextInput(attrs={
            'placeholder': '请输入验证码',
            'required': 'required',
            'maxlength': '6',
            'class': 'form-control'  # 直接添加CSS类
        })
    )
    remember = forms.BooleanField(
        label="记住我",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'id': 'remember'
        })
    )

class RegisterForm(forms.Form):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={
            'placeholder': '请输入用户名',
            'required': 'required',
            'class': 'form-control'  # 直接添加CSS类
        })
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={
            'placeholder': '请输入密码',
            'required': 'required',
            'class': 'form-control'  # 直接添加CSS类
        })
    )
    confirm_password = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(attrs={
            'placeholder': '请输入确认密码',
            'required': 'required',
            'class': 'form-control'  # 直接添加CSS类
        })
    )
    captcha = forms.CharField(
        label="验证码",
        widget=forms.TextInput(attrs={
            'placeholder': '请输入验证码',
            'required': 'required',
            'maxlength': '6',
            'class': 'form-control'  # 直接添加CSS类
        })
    )
    remember = forms.BooleanField(
        label="记住我",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'id': 'remember'
        })
    )
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('用户名已存在')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("两次输入的密码不一致")

        return cleaned_data