from django.urls import path

from ..constants import URLNames
from ..views.ranking import ranking_view

urlpatterns = [
    # 排行
    path('ranking_list/', ranking_view, name=URLNames.RANKING_PAGE),]