from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter
from CheckObjectionApp import views
from CheckObjectionApp.views import JudgeCodeView, JudgeContestCodeView

app_name = 'CheckObjectionApp'

from django.urls import path, include

router = DefaultRouter()
router.register(r'topics', views.TopicViewSet)
router.register(r'testcases', views.TestCaseViewSet)

urlpatterns = [
    # path('detail/proxy-submit-code', views.quick_judge_example, name='proxy_submit_code'),
    # 提交日常判题的api
    path('detail/proxy-submit-code/', JudgeCodeView.as_view(), name='proxy_submit_code'),
    # 提交内部算法判题的api
    path('contest/<contest_id>/proxy-submit-code-contest/', JudgeContestCodeView.as_view(), name='proxy_submit_code_contest'),

    path('api/', include(router.urls)),

    # 展示所有人的提交（管理员函数）
    path('submission', views.submission_list, name='submission_list'),
    # 展示所有人的比赛提交（管理员函数）
    path('contest_submission', views.contest_submission_list, name='contest_submission_list'),
    # 显示单个提交详情
    path('submission/<uuid:pk>/', views.submission_detail, name='submission_detail'),
    # 我的所有提交
    path('my_submission', views.my_submission_list, name='my_submission_list'),
    # 根据用户名查询提交（管理员函数）
    path('query_submission_list/<user_name>',views.query_submission_list,name='query_submission_list'),

    path('query_contest_submission_list/<contest_id>/<user_name>',views.query_contest_submission_list,name='query_contest_submission_list'),
    path("index", views.index, name="CheckObjectionApp_index"),
    path("base", views.base, name="CheckObjectionApp_base"),
    # 日常答题界面
    path("detail/<topic_id>", views.detail, name="CheckObjectionApp_detail"),
    # 内部算法竞赛界面
    path("contest/<contest_id>/<contest_topic_id>", views.contest_submit_code, name="contest_submit_code"),

    path("design", views.design, name="CheckObjectionApp_design"),
    path("show", views.submission_list, name="CheckObjectionApp_show"),
    # 修改用户名
    path("changeName", views.changeName, name="CheckObjectionApp_changeName"),
    # 修改密码
    path('changePassword', views.changePassword, name="CheckObjectionApp_changePassword"),
    # 更新偏好
    # path('update_preferences/', views.update_preferences, name='CheckObjectionApp_updatePreferences'),
    # 排行
    path('ranking/', views.ranking_view, name='ranking_page'),
    # 生成验证码
    path('image_code',views.image_code,name='image_code'),
    # 删除缓存
    path('clear_my_submission_cache', views.clear_my_submission_cache, name='clear_my_submission_cache'),
    # 注册
    path("CheckObjection_register", views.CheckObjection_register, name="CheckObjectionApp_register"),
    # 登录
    path("CheckObjection_login", views.CheckObjection_login, name="CheckObjectionApp_login"),
    # 退出登录
    path("CheckObjection_logout", views.CheckObjection_logout, name="CheckObjectionApp_logout"),
    # 无权限则返回
    path("CheckObjection_noPower", views.CheckObjection_noPower, name="CheckObjection_noPower"),
    # 搜索
    path('CheckObjection_search', views.CheckObjection_search, name='CheckObjection_search'),
    path("CheckObjection_filter", views.CheckObjection_filter, name='CheckObjection_filter'),

    # 显示 比赛的列表 所有比赛均在此处显示
    path('contest/', views.ContestListView.as_view(), name='contest_list'),
    # 比赛报名界面
    path('contest_register/<contest_id>',views.contest_register, name='contest_register'),
    # 显示 具体某场比赛的详情 列出比赛的题目
    path('contest/<int:pk>/', views.ContestDetailView.as_view(), name='contest_detail'),
    # 显示 某场比赛的排名
    path('contest/<int:pk>/rank/', views.ContestRankView.as_view(), name='contest_rank'),
    # 显示我的全部比赛提交记录
    path('my_contest_submission', views.my_contest_submission_list, name='my_contest_submission_list'),

    # 比赛排行路由及视图
    path('contest_rank_list/', views.contest_rank_list, name='contest_rank_list'),
    path('contest_rank_detail/<int:contest_id>/', views.contest_rank_detail, name='contest_rank_detail'),

    # 批量导入题目api
    path('batch-import-testcases/', views.batch_import_testcases, name='batch_import_testcases'),

    # 用户列表页
    path('users/', views.user_list, name='user_list'),
    # 用户详情页（假设你已经有user_detail视图）
    # path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    # 展示用户参加过的比赛记录(管理员函数)
    path('user/contests/<str:user_name>/',
         views.user_contests, name='user_contests'),
    # 显示当前用户参加过的比赛记录
    path('my_contests/',
         views.my_contests, name='my_contests'),
    # 展示查询的比赛用户提交记录（管理员函数）
    path('contest/submissions/<int:contest_id>/user/<str:user_name>/',
         views.contest_user_submissions, name='contest_user_submissions'),
    # 显示当前用户某比赛提交记录
    path('contest/submissions/<int:contest_id>/',
         views.contest_my_submissions, name='contest_my_submissions'),

]
