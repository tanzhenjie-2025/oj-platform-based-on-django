
from django.urls import path
from ..views.topics import detail,design,CheckObjection_search,CheckObjection_filter
urlpatterns = [
    # 日常答题界面
    path("detail/<topic_id>", detail, name="CheckObjectionApp_detail"),
    path("design", design, name="CheckObjectionApp_design"),
    # 搜索
    path('CheckObjection_search', CheckObjection_search, name='CheckObjection_search'),
    path("CheckObjection_filter", CheckObjection_filter, name='CheckObjection_filter'),
]