
from django.urls import path
from ..views.submissions import submission_list,my_submission_list,submission_detail,query_submission_list,query_contest_submission_list
urlpatterns = [
# 展示所有人的提交（管理员函数）
    path('submission', submission_list, name='submission_list'),
    # 展示所有人的比赛提交（管理员函数）
    path('contest_submission', my_submission_list, name='contest_submission_list'),
    # 显示单个提交详情
    path('submission/<uuid:pk>/', submission_detail, name='submission_detail'),
    # 我的所有提交
    path('my_submission', my_submission_list, name='my_submission_list'),
    # 根据用户名查询提交（管理员函数）
    path('query_submission_list/<user_name>',query_submission_list,name='query_submission_list'),

    path('query_contest_submission_list/<contest_id>/<user_name>',query_contest_submission_list,name='query_contest_submission_list'),
    path("show", submission_list, name="CheckObjectionApp_show"),]