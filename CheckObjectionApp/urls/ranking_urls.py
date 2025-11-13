from django.urls import path
from ..views.ranking import ranking_view

urlpatterns = [
    # 排行
    path('ranking_list/', ranking_view, name='ranking_page'),]