# CheckObjectionApp/views/contests.py
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from CheckObjection import settings
from CheckObjectionApp.models import Contest, ContestParticipant, topic, ContestSubmission
from CheckObjectionApp.utils.contest_service import ContestService


class ContestListView(ListView):
    model = Contest
    template_name = 'CheckObjection/contest/contest_list.html'
    paginate_by = 20

    def get_queryset(self):
        queryset = Contest.objects.all()
        status = self.request.GET.get('status')
        if status == 'running':
            queryset = queryset.filter(
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now()
            )
        elif status == 'upcoming':
            queryset = queryset.filter(start_time__gt=timezone.now())
        elif status == 'ended':
            queryset = queryset.filter(end_time__lt=timezone.now())
        return queryset


class ContestDetailView(LoginRequiredMixin, DetailView):
    model = Contest
    template_name = 'CheckObjection/contest/contest_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contest = self.object

        # 检查用户权限
        if not ContestService.can_view_contest(self.request.user, contest):
            raise PermissionDenied("无权查看此比赛")

        # 获取比赛题目
        contest_topics = contest.contest_topics.select_related('topic').all()
        context['contest_topics'] = contest_topics

        # 获取当前用户的提交统计
        if hasattr(self.request.user, 'id'):
            participant = ContestParticipant.objects.filter(
                contest=contest, user=self.request.user
            ).first()

            if participant:
                # 简化的统计逻辑，详细的排行榜逻辑移到ranking.py
                submissions = ContestSubmission.objects.filter(
                    participant=participant
                ).select_related('submission')

                # 基础统计信息
                total_submissions = submissions.count()
                accepted_submissions = submissions.filter(
                    submission__overall_result='Accepted'
                ).count()

                context['user_stats'] = {
                    'total_submissions': total_submissions,
                    'accepted_submissions': accepted_submissions,
                    'participation_rate': (
                                accepted_submissions / total_submissions * 100) if total_submissions > 0 else 0
                }

        return context


class ContestRankView(LoginRequiredMixin, DetailView):
    """比赛排名页面 - 重定向到专门的排行榜视图"""
    model = Contest
    template_name = 'CheckObjection/contest/rank/rank_list.html'

    def get(self, request, *args, **kwargs):
        """重定向到专门的比赛排行榜视图"""
        contest = self.get_object()
        return redirect('CheckObjectionApp:contest_rank_detail', contest_id=contest.id)


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy(settings.LOGIN_URL))
def contest_submit_code(request, contest_id, contest_topic_id):
    """比赛提交界面"""
    if request.method == 'GET':
        topic_content = topic.objects.get(id=contest_topic_id)
        user = request.user
        context = {
            'topic_content': topic_content,
            'user': user,
            'contest_id': contest_id,
            'contest_topic_id': contest_topic_id,
        }
        return render(request, 'CheckObjection/topic/contest_topic.html', context=context)


@login_required
def contest_register(request, contest_id):
    """比赛报名视图"""
    contest = get_object_or_404(Contest, id=contest_id)

    if request.method == 'GET':
        return render(request, 'CheckObjection/contest/contest_register.html', {
            'contest': contest
        })

    if request.method == 'POST':
        # 检查比赛是否允许报名
        if not contest.allow_register:
            messages.error(request, "该比赛不允许报名")
            return redirect('CheckObjectionApp:contest_detail', pk=contest_id)

        # 检查比赛状态
        if contest.status == 'ended':
            messages.error(request, "比赛已结束，无法报名")
            return redirect('CheckObjectionApp:contest_detail', pk=contest_id)

        # 检查是否已报名
        if ContestParticipant.objects.filter(contest=contest, user=request.user).exists():
            messages.warning(request, "您已报名该比赛，无需重复报名")
            return redirect('CheckObjectionApp:contest_detail', pk=contest_id)

        # 验证比赛密码
        if contest.password:
            input_password = request.POST.get('password', '').strip()
            if input_password != contest.password:
                messages.error(request, "比赛密码错误")
                return render(request, 'CheckObjection/contest/contest_register.html', {
                    'contest': contest
                })

        # 创建报名记录
        ContestParticipant.objects.create(contest=contest, user=request.user)
        messages.success(request, "报名成功！请准时参加比赛")
        return redirect('CheckObjectionApp:contest_detail', pk=contest_id)