from django.urls import path

from ..constants import URLNames
from ..views.admin_views import user_list, user_contests, contest_user_submissions
from ..views.submissions import contest_my_submissions
from ..views.user_management import my_contests

urlpatterns = [
    # 注册
    # 用户列表页
    path('users/', user_list, name=URLNames.USER_LIST),
    # 展示用户参加过的比赛记录(管理员函数)
    path('user/contests/<str:user_name>/', user_contests, name=URLNames.USER_CONTESTS),
    # 显示当前用户参加过的比赛记录
    path('my_contests/', my_contests, name=URLNames.MY_CONTESTS),
    # 展示查询的比赛用户提交记录（管理员函数）
    path('contest/submissions/<int:contest_id>/user/<str:user_name>/', contest_user_submissions,
         name=URLNames.CONTEST_USER_SUBMISSIONS),
    # 显示当前用户某比赛提交记录
    path('contest/submissions/<int:contest_id>/', contest_my_submissions, name=URLNames.CONTEST_MY_SUBMISSIONS),
]