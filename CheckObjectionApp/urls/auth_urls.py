# CheckObjectionApp/urls/auth_urls.py
from django.urls import path

from ..constants import URLNames
from ..views.auth import CheckObjection_login, CheckObjection_register, CheckObjection_logout, CheckObjection_noPower

# 注意：这里不需要 app_name，因为主urls.py已经定义了

urlpatterns = [
    # 注册
    path("register", CheckObjection_register, name=URLNames.REGISTER),
    # 登录
    path("login", CheckObjection_login, name=URLNames.LOGIN),
    # 退出登录
    path("logout", CheckObjection_logout, name=URLNames.LOGOUT),
    # 无权限则返回
    path("noPower", CheckObjection_noPower, name=URLNames.NO_POWER),
]