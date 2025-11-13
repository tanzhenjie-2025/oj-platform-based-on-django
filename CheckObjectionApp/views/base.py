# CheckObjectionApp/views/base.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from CheckObjectionApp.models import topic


def redirect_root(request):
    """重定向到主页"""
    return redirect('CheckObjectionApp:CheckObjectionApp_index')
@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def index(request):
    """算法提交平台首页"""
    topics = topic.objects.all()
    user = request.user
    user_profile = user.userprofile
    return render(request, 'CheckObjection/CheckObjection_Index.html', context={'topics': topics, 'user':user, 'user_profile':user_profile})

def base(request):
    return render(request,'CheckObjection/CheckObjectionApp_base.html')

def CheckObjection_noPower(request):
    return render(request,'CheckObjection/CheckObjection_noPower.html')