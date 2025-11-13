from django.urls import path

from ..constants import URLNames
from ..views.user_profile import change_profile,change_password

urlpatterns = [
    # 修改用户名
    path("changeName", change_profile, name=URLNames.CHANGE_NAME),
    # 修改密码
    path('changePassword', change_password, name=URLNames.CHANGE_PASSWORD),
    # 更新偏好
    # path('update_preferences/', views.update_preferences, name='CheckObjectionApp_updatePreferences'),
]