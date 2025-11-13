
from django.urls import path

from ..constants import URLNames
from ..views.judge import JudgeCodeView,JudgeContestCodeView
urlpatterns = [
# 提交日常判题的api
    path('detail/proxy-submit-code/', JudgeCodeView.as_view(), name=URLNames.PROXY_SUBMIT_CODE),
    # 提交内部算法判题的api
    path('contest/<contest_id>/proxy-submit-code-contest/', JudgeContestCodeView.as_view(), name=URLNames.PROXY_SUBMIT_CODE_CONTEST),]
