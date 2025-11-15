# CheckObjectionApp/views/admin_views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.db.models import Count, Case, When, IntegerField
from django.utils import timezone
from django.http import HttpResponseServerError
from django.urls import reverse_lazy
from CheckObjection import settings
from ..constants import URLNames
from ..models import User, UserProfile, Contest, ContestParticipant, ContestSubmission, Submission


@login_required(login_url=reverse_lazy(f'CheckObjectionApp:{URLNames.LOGIN}'))
@staff_member_required
def all_user_list(request):
    """展示所有用户的列表视图（仅管理员可访问）"""
    users = User.objects.all().order_by('-date_joined')

    # 处理用户数据，关联用户附加信息
    user_data = []
    for user in users:
        try:
            profile = UserProfile.objects.get(user=user)
            finish_count = profile.finish
        except UserProfile.DoesNotExist:
            finish_count = 0

        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined,
            'finish_count': finish_count,
            'is_active': user.is_active,
            'is_staff': user.is_staff
        })

    context = {
        'users': user_data,
        'page_title': '用户管理',
        'total_users': len(user_data)
    }
    return render(request, 'CheckObjection/admin/all_user_list.html', context)


@login_required
@staff_member_required
def user_contests(request, user_name):
    """显示指定用户参加过的所有比赛（管理员视图）"""
    try:
        user = get_object_or_404(User, username=user_name)
        cache_key = f"user_{user_name}_contests"

        # 尝试从缓存获取数据
        contests_data = cache.get(cache_key)

        if contests_data is None:
            # 查询用户参加的所有比赛
            participants = ContestParticipant.objects.filter(
                user=user,
                is_disqualified=False
            ).select_related('contest', 'contest__created_by')

            # 为每个比赛添加统计信息
            contests_list = []
            for participant in participants:
                contest = participant.contest

                # 查询该用户在此比赛中的提交统计
                submission_stats = ContestSubmission.objects.filter(
                    participant=participant
                ).aggregate(
                    total_submissions=Count('id'),
                    accepted_submissions=Count(
                        Case(
                            When(submission__overall_result='Accepted', then=1),
                            output_field=IntegerField()
                        )
                    )
                )

                # 查询解决的题目数量（去重）
                solved_topics = ContestSubmission.objects.filter(
                    participant=participant,
                    submission__overall_result='Accepted'
                ).values('submission__topic').distinct().count()

                total_subs = submission_stats['total_submissions'] or 0
                accepted_subs = submission_stats['accepted_submissions'] or 0

                # 计算通过率
                if total_subs > 0:
                    participation_rate = f"{(accepted_subs / total_subs) * 100:.1f}%"
                else:
                    participation_rate = "0%"

                contests_list.append({
                    'contest': contest,
                    'participant': participant,
                    'total_submissions': total_subs,
                    'accepted_submissions': accepted_subs,
                    'solved_topics': solved_topics,
                    'participation_rate': participation_rate
                })

            # 按比赛开始时间倒序排列
            contests_list.sort(key=lambda x: x['contest'].start_time, reverse=True)
            cache.set(cache_key, contests_list, 600)  # 10分钟缓存
            contests_data = contests_list

        context = {
            'contests_data': contests_data,
            'target_user': user,
            'page_title': f'{user_name} 参加的比赛',
            'current_time': timezone.now()
        }
        return render(request, 'CheckObjection/admin/query_user_contests.html', context)

    except Exception as e:
        return HttpResponseServerError(f"服务器错误: {e}")


@login_required
@staff_member_required
def contest_user_submissions(request, contest_id, user_name):
    """显示指定用户在特定比赛中的提交记录（管理员视图）"""
    contest = get_object_or_404(Contest, id=contest_id)
    cache_key = f"contest_{contest_id}_user_{user_name}_submissions"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        # 查询比赛提交记录
        contest_submissions = ContestSubmission.objects.filter(
            contest_id=contest_id,
            submission__user_name=user_name
        ).select_related(
            'submission',
            'submission__topic',
            'participant'
        ).order_by('-submitted_at')

        # 转换为可缓存格式
        submissions_list = list(contest_submissions)
        cache.set(cache_key, submissions_list, 300)  # 5分钟缓存
        submissions = submissions_list

    context = {
        'contest': contest,
        'submissions': submissions,
        'target_user_name': user_name,
        'page_title': f'{user_name} - {contest.title} 提交记录',
        'is_admin_view': True
    }
    return render(request, 'CheckObjection/submission/contest_submission_list.html', context)


@login_required
@staff_member_required
def query_submission_list(request, user_name):
    """根据用户名查询提交记录（管理员功能）"""
    cache_key = f"user_submissions_{user_name}"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        # 从数据库查询
        submissions_queryset = Submission.objects.filter(
            user_name=user_name
        ).select_related('topic')

        submissions_list = list(submissions_queryset)
        cache.set(cache_key, submissions_list, 300)  # 5分钟缓存
        submissions = submissions_list

    context = {
        'submissions': submissions,
        'page_title': f'用户 {user_name} 的提交记录',
        'target_user_name': user_name,
        'is_admin_view': True
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)


@login_required
@staff_member_required
def query_contest_submission_list(request, contest_id, user_name):
    """显示查询单个用户在指定比赛中的所有提交记录（管理员视图）"""
    cache_key = f"contest_{contest_id}_user_{user_name}_submissions"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        try:
            # 获取比赛对象
            contest = Contest.objects.get(id=contest_id)

            # 获取用户在指定比赛中的所有提交记录
            contest_submissions_queryset = ContestSubmission.objects.filter(
                contest_id=contest_id,
                participant__user__username=user_name
            ).select_related(
                'submission',
                'submission__topic',
                'participant'
            ).order_by('-submitted_at')

            # 处理数据
            processed_submissions = []
            for contest_submission in contest_submissions_queryset:
                submission = contest_submission.submission
                processed_submissions.append({
                    'contest_submission_id': contest_submission.id,
                    'id': submission.id,
                    'user_name': submission.user_name,
                    'topic_id': submission.topic.id if submission.topic else None,
                    'topic': {
                        'id': submission.topic.id if submission.topic else None,
                        'title': submission.topic.title if submission.topic else '未知题目'
                    },
                    'language_id': submission.language_id,
                    'status': submission.status,
                    'overall_result': submission.overall_result,
                    'created_at': submission.created_at,
                    'submitted_at': contest_submission.submitted_at,
                })

            cache.set(cache_key, processed_submissions, 300)
            submissions = processed_submissions

        except Contest.DoesNotExist:
            submissions = []

    context = {
        'submissions': submissions,
        'page_title': f'比赛提交记录 - 用户: {user_name}',
        'contest_id': contest_id,
        'user_name': user_name,
        'is_admin_view': True
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)


@login_required
@staff_member_required
def submission_list(request):
    """显示全部用户的所有提交记录（管理员视图）"""
    submissions = Submission.objects.all().select_related('topic').order_by('-created_at')

    context = {
        'submissions': submissions,
        'page_title': '全部提交记录',
        'is_admin_view': True
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)


@login_required
@staff_member_required
def contest_submission_list(request):
    """显示全部比赛的所有提交记录（管理员视图）"""
    contest_submissions = ContestSubmission.objects.all().select_related(
        'contest',
        'submission',
        'submission__topic',
        'participant__user'
    ).order_by('-submitted_at')

    # 准备前端需要的数据
    submission_data = []
    for contest_sub in contest_submissions:
        submission = contest_sub.submission
        submission_info = {
            'contest_submission_id': contest_sub.id,
            'submitted_at': contest_sub.submitted_at,
            'id': submission.id,
            'user_name': submission.user_name,
            'topic_id': submission.topic.id if submission.topic else None,
            'topic': submission.topic,
            'language_id': submission.language_id,
            'status': submission.status,
            'overall_result': submission.overall_result,
            'created_at': submission.created_at,
            'updated_at': submission.updated_at,
            'contest': contest_sub.contest,
            'participant': contest_sub.participant,
        }
        submission_data.append(submission_info)

    context = {
        'submissions': submission_data,
        'page_title': '比赛提交记录',
        'is_admin_view': True
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)