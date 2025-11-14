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
from CheckObjectionApp import models

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

        # 初始化统计数据
        problem_scores = []
        problem_submissions_stats = []
        total_score = 0
        total_ac_count = 0
        total_submission_count = 0
        solved_problems = set()

        # 获取当前用户的提交统计
        if hasattr(self.request.user, 'id'):
            participant = ContestParticipant.objects.filter(
                contest=contest, user=self.request.user
            ).first()

            if participant:
                submissions = ContestSubmission.objects.filter(
                    participant=participant
                ).select_related('submission')

                # 按题目分组统计
                problem_status = {}
                for submission in submissions:
                    topic_id = submission.submission.topic_id
                    if topic_id not in problem_status:
                        problem_status[topic_id] = {
                            'solved': False,
                            'submissions': [],
                            'ac_count': 0,
                            'total_count': 0
                        }

                    problem_status[topic_id]['submissions'].append(submission)
                    problem_status[topic_id]['total_count'] += 1

                    if submission.submission.overall_result == 'Accepted':
                        problem_status[topic_id]['solved'] = True
                        problem_status[topic_id]['ac_count'] += 1

                context['problem_status'] = problem_status

                # 构建得分情况和提交统计
                for contest_topic in contest_topics:
                    topic_id = contest_topic.topic.id
                    status = problem_status.get(topic_id, {})

                    # 得分情况
                    if status.get('solved', False):
                        score = contest_topic.score
                        total_score += score
                        solved_problems.add(topic_id)
                        score_status = f"{score}分（已得）"
                        score_color = "#4caf50"
                    else:
                        score = 0
                        score_status = f"{contest_topic.score}分（未得）"
                        score_color = "#f44336"

                    problem_scores.append({
                        'order': contest_topic.order,
                        'title': f"题目{contest_topic.order}",
                        'score_status': score_status,
                        'color': score_color,
                        'score': score,
                        'full_score': contest_topic.score
                    })

                    # 提交情况
                    total_count = status.get('total_count', 0)
                    ac_count = status.get('ac_count', 0)
                    total_submission_count += total_count

                    if ac_count > 0:
                        submission_status = f"{total_count}次（AC）"
                        submission_color = "#4caf50"
                        total_ac_count += 1
                    elif total_count > 0:
                        submission_status = f"{total_count}次（WA）"
                        submission_color = "#f44336"
                    else:
                        submission_status = "0次"
                        submission_color = "#9e9e9e"

                    problem_submissions_stats.append({
                        'order': contest_topic.order,
                        'title': f"题目{contest_topic.order}",
                        'submission_status': submission_status,
                        'color': submission_color,
                        'total_count': total_count,
                        'ac_count': ac_count
                    })

        # 计算AC率
        ac_rate = 0
        if contest_topics:
            ac_rate = round((total_ac_count / len(contest_topics)) * 100, 1)

        # 新增：获取前三名的答对题目数目
        top_three_ac_counts = self.get_top_three_ac_counts(contest)
        context['top_three_ac_counts'] = top_three_ac_counts

        # 添加到context
        context['problem_scores'] = problem_scores
        context['problem_submissions_stats'] = problem_submissions_stats
        context['total_score'] = total_score
        context['contest_total_score'] = sum(topic.score for topic in contest_topics)
        context['ac_rate'] = ac_rate
        context['total_ac_count'] = total_ac_count
        context['total_problems'] = len(contest_topics)
        context['solved_problems'] = solved_problems
        print(context)
        return context

    def get_top_three_ac_counts(self, contest):
        """
        获取前三名用户的答对题目数目
        """
        # 获取所有参与者
        participants = ContestParticipant.objects.filter(
            contest=contest,
            is_disqualified=False
        ).select_related('user')

        top_three_data = []

        for participant in participants:
            # 获取该参与者的所有AC提交
            ac_submissions = ContestSubmission.objects.filter(
                participant=participant,
                submission__overall_result='Accepted'
            ).select_related('submission')

            # 统计不同题目的AC数量（去重，同一题目多次AC只算一次）
            solved_problems = set()
            for submission in ac_submissions:
                solved_problems.add(submission.submission.topic_id)

            ac_count = len(solved_problems)

            top_three_data.append({
                'user': participant.user,
                'ac_count': ac_count,
                'username': participant.user.username
            })

        # 按AC数量降序排序，取前三名
        top_three_data.sort(key=lambda x: x['ac_count'], reverse=True)
        return top_three_data[:3]


class ContestRankView(LoginRequiredMixin, DetailView):
    model = Contest
    template_name = 'CheckObjection/contest/rank/rank_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contest = self.object

        # 检查封榜逻辑
        if contest.ranking_frozen and contest.frozen_time:
            show_real_time = self.request.user == contest.created_by
        else:
            show_real_time = True

        rank_data = ContestService.get_contest_ranklist(contest.id)
        context['rank_data'] = rank_data
        context['show_real_time'] = show_real_time

        return context


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