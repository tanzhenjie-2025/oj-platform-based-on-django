from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter
from CheckObjectionApp import views
from .views import CheckObjection_register, CheckObjection_login, CheckObjection_logout
from .views.admin_views import user_list, user_contests, contest_user_submissions
# from CheckObjectionApp.views import JudgeCodeView, JudgeContestCodeView
from .views.submissions import my_submission_list, submission_detail, submission_list, query_submission_list, \
    query_contest_submission_list, my_contest_submission_list, contest_my_submissions
from .views.submissions import clear_my_submission_cache
from .views.base import base, CheckObjection_noPower
from .views.judge import JudgeCodeView, JudgeContestCodeView
from .views.topics import detail, design, CheckObjection_search, CheckObjection_filter
from .views.user_management import my_contests
from .views.user_profile import change_profile, change_password
from .views.ranking import ranking_view, contest_rank_list, contest_rank_detail
from .views.utils import image_code, batch_import_testcases
from .views.base import index
from .views.contests import contest_submit_code, ContestListView, ContestDetailView, ContestRankView, contest_register

app_name = 'CheckObjectionApp'

from django.urls import path, include


urlpatterns = [
    # path('detail/proxy-submit-code', views.quick_judge_example, name='proxy_submit_code'),
    # 提交日常判题的api
    path('detail/proxy-submit-code/', JudgeCodeView.as_view(), name='proxy_submit_code'),
    # 提交内部算法判题的api
    path('contest/<contest_id>/proxy-submit-code-contest/', JudgeContestCodeView.as_view(), name='proxy_submit_code_contest'),

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
    path("index", index, name="index"),
    path("base", base, name="base"),
    # 日常答题界面
    path("detail/<topic_id>", detail, name="detail"),
    # 内部算法竞赛界面
    path("contest/<contest_id>/<contest_topic_id>", contest_submit_code, name="contest_submit_code"),

    path("design", design, name="design"),
    path("show", submission_list, name="show"),
    # 修改用户名
    path("changeName", change_profile, name="changeName"),
    # 修改密码
    path('changePassword', change_password, name="changePassword"),
    # 更新偏好
    # path('update_preferences/', views.update_preferences, name='CheckObjectionApp_updatePreferences'),
    # 排行
    path('ranking/', ranking_view, name='ranking_page'),
    # 生成验证码
    path('image_code',image_code,name='image_code'),
    # 删除缓存
    path('clear_my_submission_cache', clear_my_submission_cache, name='clear_my_submission_cache'),

    path('auth/', include('CheckObjectionApp.urls.auth_urls')),

    # 注册
    path("CheckObjection_register", CheckObjection_register, name="register"),
    # 登录
    path("CheckObjection_login", CheckObjection_login, name="login"),
    # 退出登录
    path("CheckObjection_logout", CheckObjection_logout, name="logout"),
    # 无权限则返回
    path("CheckObjection_noPower", CheckObjection_noPower, name="noPower"),
    # 搜索
    path('CheckObjection_search', CheckObjection_search, name='CheckObjection_search'),
    path("CheckObjection_filter", CheckObjection_filter, name='CheckObjection_filter'),

    # 显示 比赛的列表 所有比赛均在此处显示
    path('contest/', ContestListView.as_view(), name='contest_list'),
    # 比赛报名界面
    path('contest_register/<contest_id>',contest_register, name='contest_register'),
    # 显示 具体某场比赛的详情 列出比赛的题目
    path('contest/<int:pk>/', ContestDetailView.as_view(), name='contest_detail'),
    # 显示 某场比赛的排名
    path('contest/<int:pk>/rank/', ContestRankView.as_view(), name='contest_rank'),
    # 显示我的全部比赛提交记录
    path('my_contest_submission', my_contest_submission_list, name='my_contest_submission_list'),

    # 比赛排行路由及视图
    path('contest_rank_list/', contest_rank_list, name='contest_rank_list'),
    path('contest_rank_detail/<int:contest_id>/', contest_rank_detail, name='contest_rank_detail'),

    # 批量导入题目api
    path('batch-import-testcases/', batch_import_testcases, name='batch_import_testcases'),

    # 用户列表页
    path('users/', user_list, name='user_list'),
    # 展示用户参加过的比赛记录(管理员函数)
    path('user/contests/<str:user_name>/',user_contests, name='user_contests'),
    # 显示当前用户参加过的比赛记录
    path('my_contests/',my_contests, name='my_contests'),
    # 展示查询的比赛用户提交记录（管理员函数）
    path('contest/submissions/<int:contest_id>/user/<str:user_name>/',contest_user_submissions, name='contest_user_submissions'),
    # 显示当前用户某比赛提交记录
    path('contest/submissions/<int:contest_id>/',contest_my_submissions, name='contest_my_submissions'),

]
