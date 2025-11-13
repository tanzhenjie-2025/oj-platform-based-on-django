# CheckObjectionApp/urls/__init__.py
app_name = 'CheckObjectionApp'  # 这里设置命名空间

from django.urls import path, include

# 导入所有子URL配置
from . import admin_urls,auth_urls,base_urls,contest_urls,judge_urls,ranking_urls,submission_urls,topic_urls,user_urls,utils_urls
# 合并所有URL模式
urlpatterns = [
    # 认证相关
    path('auth/', include(auth_urls)),
    path('base_url/',include(base_urls)),
    path('admin/', include(admin_urls)),
    path('contest/', include(contest_urls)),
    path('judge/', include(judge_urls)),
    path('ranking/', include(ranking_urls)),
    path('submission/', include(submission_urls)),
    path('topic/', include(topic_urls)),
    path('user/', include(user_urls)),
    path('utils/', include(utils_urls)),
]