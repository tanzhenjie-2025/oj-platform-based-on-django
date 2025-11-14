
from django.urls import path

from ..constants import URLNames
from ..views.topics import topic_detail,topic_design,topic_search,topic_filter
urlpatterns = [
    # 日常答题界面
    path("detail/<topic_id>", topic_detail, name=URLNames.TOPIC_DETAIL),
    path("design", topic_design, name=URLNames.TOPIC_DESIGN),
    # 搜索
    path('CheckObjection_search', topic_search, name=URLNames.TOPIC_SEARCH),
    path("CheckObjection_filter", topic_filter, name=URLNames.TOPIC_FILTER),
]