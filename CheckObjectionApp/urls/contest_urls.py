
from django.urls import path

from ..constants import URLNames
from ..views.contests import contest_submit_code,ContestListView,ContestDetailView,contest_register,ContestRankView
from ..views.ranking import contest_rank_list, contest_rank_detail
from ..views.submissions import my_contest_submission_list

urlpatterns = [

path("contest/<contest_id>/<contest_topic_id>", contest_submit_code, name=URLNames.CONTEST_SUBMIT_CODE),
    # 显示 比赛的列表 所有比赛均在此处显示
    path('contest_list/', ContestListView.as_view(), name=URLNames.CONTEST_LIST),
    # 比赛报名界面
    path('contest_register/<contest_id>', contest_register, name=URLNames.CONTEST_REGISTER),
    # 显示 具体某场比赛的详情 列出比赛的题目
    path('contest/<int:pk>/', ContestDetailView.as_view(), name=URLNames.CONTEST_DETAIL),
    # 显示 某场比赛的排名
    path('contest/<int:pk>/rank/', ContestRankView.as_view(), name=URLNames.CONTEST_RANK),
    # 显示我的全部比赛提交记录
    path('my_contest_submission', my_contest_submission_list, name=URLNames.MY_CONTEST_SUBMISSION_LIST),

    # 比赛排行路由及视图
    path('contest_rank_list/', contest_rank_list, name=URLNames.CONTEST_RANK_LIST),
    path('contest_rank_detail/<int:contest_id>/', contest_rank_detail, name=URLNames.CONTEST_RANK_DETAIL),
]