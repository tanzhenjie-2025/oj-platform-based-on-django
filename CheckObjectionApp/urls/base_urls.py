from django.urls import path

from ..constants import URLNames
from ..views.auth import CheckObjection_login, CheckObjection_register, CheckObjection_logout
from ..views.base import CheckObjection_noPower, index, base

# 注意：这里不需要 app_name，因为主urls.py已经定义了

urlpatterns = [
    path("index", index, name=URLNames.INDEX),
    path("base", base, name=URLNames.BASE),
]