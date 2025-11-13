
from django.urls import path
from ..views.judge import JudgeCodeView,JudgeContestCodeView
urlpatterns = [
# 提交日常判题的api
    path('detail/proxy-submit-code/', JudgeCodeView.as_view(), name='proxy_submit_code'),
    # 提交内部算法判题的api
    path('contest/<contest_id>/proxy-submit-code-contest/', JudgeContestCodeView.as_view(), name='proxy_submit_code_contest'),]
