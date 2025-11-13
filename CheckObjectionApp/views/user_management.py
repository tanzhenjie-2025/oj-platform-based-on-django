# CheckObjectionApp/views/user_management.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Contest, ContestParticipant

@login_required
def my_contests(request):
    """显示当前用户自己参加过的所有比赛"""
    # 这里可以调用 admin_views 中的逻辑，但使用当前用户
    from .admin_views import user_contests
    return user_contests(request, request.user.username)