# CheckObjectionApp/views/topics.py
from django.shortcuts import render, redirect, reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.core.cache import cache
import json

from ..constants import URLNames
from ..models import topic, UserProfile, answer

@login_required
def index(request):
    """算法提交平台首页"""
    topics = topic.objects.all()
    user = request.user
    user_profile = user.userprofile
    return render(request, 'CheckObjection/base/Index.html',
                  context={'topics': topics, 'user': user, 'user_profile': user_profile})


@require_http_methods(['GET', 'POST'])
@login_required
def topic_detail(request, topic_id):
    """题目详情页 - 显示题目内容和处理提交"""
    if request.method == "POST":
        # 处理提交的逻辑
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'finish': 1}
        )
        UserProfile.objects.filter(user=request.user).update(finish=F('finish') + 1)

        content = request.POST.get('content')
        notes = request.POST.get('notes')
        user_name = request.POST.get('user_name')

        answer.objects.create(
            topic_id=topic_id,
            content=content,
            notes=notes,
            user_name=user_name
        )

        return redirect(reverse(f'CheckObjectionApp:{URLNames.INDEX}'))
    else:
        # 显示题目详情
        topic_content = topic.objects.get(id=topic_id)
        user = request.user
        return render(request, 'CheckObjection/topic/practice_topic.html',
                      context={'topic_content': topic_content, 'user': user})


@require_http_methods(['GET', 'POST'])
@login_required
def topic_design(request):
    """题目设计（管理员功能）"""
    if not request.user.is_staff:
        return redirect("CheckObjectionApp:no_power")

    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        example = request.POST.get('example')
        level = request.POST.get('level')
        topic.objects.create(content=content, title=title, example=example, level=level)
        return redirect(reverse("CheckObjectionApp:index"))
    else:
        return render(request, 'CheckObjection/topic/CheckObjection_design.html')


@login_required
def topic_search(request):
    """搜索题目"""
    q = request.GET.get('q')
    if not q:
        return render(request, 'CheckObjection/base/Index.html', context={"topics": []})

    cache_key = f"search_results:{q.lower()}"
    cached_results = cache.get(cache_key)

    if cached_results is not None:
        topic_ids = json.loads(cached_results)
        topics = topic.objects.filter(id__in=topic_ids)
    else:
        topics = topic.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q)
        )
        topic_ids = list(topics.values_list('id', flat=True))
        cache.set(cache_key, json.dumps(topic_ids), timeout=300)

    return render(request, 'CheckObjection/base/Index.html', context={"topics": topics})


@login_required
def topic_filter(request):
    """按难度过滤题目"""
    q = request.GET.get('f')
    if q == 'all':
        topics = topic.objects.all()
        return render(request, 'CheckObjection/base/Index.html', context={"topics": topics})

    if not q:
        return render(request, 'CheckObjection/base/Index.html', context={"topics": []})

    cache_key = f"filter_results:{q.lower()}"
    cached_results = cache.get(cache_key)

    if cached_results is not None:
        topic_ids = json.loads(cached_results)
        topics = topic.objects.filter(id__in=topic_ids)
    else:
        topics = topic.objects.filter(Q(level=q))
        topic_ids = list(topics.values_list('id', flat=True))
        cache.set(cache_key, json.dumps(topic_ids), timeout=300)

    return render(request, 'CheckObjection/base/Index.html', context={"topics": topics})