# CheckObjectionApp/views/submissions.py

from ..models import ContestParticipant

from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import  user_passes_test,login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404

from CheckObjectionApp.models import Submission, Contest, ContestTopic, ContestSubmission
from CheckObjectionApp.utils.cache_utils import SubmissionCache
from CheckObjection.settings import DB_QUERY_KEY, CACHE_KEY_HIT
# 基于函数的视图
# 管理员函数
@login_required
@staff_member_required
def submission_list(request):
    """显示全部用户的所有提交记录"""
    submissions = Submission.objects.all()
    context = {
        'submissions': submissions,
        'page_title': '全部提交记录'
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)

# 管理员视图
@login_required
@staff_member_required
def submission_detail(request, pk):
    """显示单个提交记录的详细信息"""
    submission = get_object_or_404(Submission, pk=pk)
    context = {
        'submission': submission,
        'page_title': f'提交详情 - {submission.topic_id}'
    }
    return render(request, 'CheckObjection/submission/submission_detail.html', context)

@login_required
def my_submission_list(request):
    """显示我的所有提交记录（带缓存）"""
    user_name = request.user.username
    """显示查询用户的所有提交记录"""
    cache_key = f"user_submissions_{user_name}"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        # 缓存中没有，从数据库查询：使用select_related预加载topic
        submissions_queryset = Submission.objects.filter(
            user_name=user_name
        ).select_related('topic')  # 预加载关联的topic对象

        # 将查询结果转换为可缓存格式（列表）
        submissions_list = list(submissions_queryset)  # 此时每个对象已包含topic数据

        # 设置缓存
        cache_timeout = SubmissionCache.get_cache_timeout()
        cache.set(cache_key, submissions_list, cache_timeout)
        submissions = submissions_list  # 赋值给submissions，统一后续逻辑

        cache_status = DB_QUERY_KEY

    else:
        cache_status = CACHE_KEY_HIT

    if cache_status == DB_QUERY_KEY:
        cache_status = ''

    context = {
        'submissions': submissions,
        'page_title': '提交记录',
        'cache_status': cache_status,
        'cache_timeout': SubmissionCache.get_cache_timeout()
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)

# 管理员视图
@login_required
@staff_member_required
def query_submission_list(request, user_name):
    """显示查询用户的所有提交记录"""
    cache_key = f"user_submissions_{user_name}"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        # 缓存中没有，从数据库查询：使用select_related预加载topic
        submissions_queryset = Submission.objects.filter(
            user_name=user_name
        ).select_related('topic')  # 预加载关联的topic对象

        # 将查询结果转换为可缓存格式（列表）
        submissions_list = list(submissions_queryset)  # 此时每个对象已包含topic数据

        # 设置缓存
        cache_timeout = SubmissionCache.get_cache_timeout()
        cache.set(cache_key, submissions_list, cache_timeout)
        submissions = submissions_list  # 赋值给submissions，统一后续逻辑

    cache_status = ''

    context = {
        'submissions': submissions,
        'page_title': '提交记录',
        'cache_status': cache_status,
        'cache_timeout': SubmissionCache.get_cache_timeout()
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)

@login_required
def query_topic_submission_list(request, user_name):
    """显示查询题目的所有提交记录"""
    cache_key = f"user_submissions_{user_name}"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        # 缓存中没有，从数据库查询：使用select_related预加载topic
        submissions_queryset = Submission.objects.filter(
            user_name=user_name
        ).select_related('topic')  # 预加载关联的topic对象

        # 将查询结果转换为可缓存格式（列表）
        submissions_list = list(submissions_queryset)  # 此时每个对象已包含topic数据

        # 设置缓存
        cache_timeout = SubmissionCache.get_cache_timeout()
        cache.set(cache_key, submissions_list, cache_timeout)
        submissions = submissions_list  # 赋值给submissions，统一后续逻辑

    cache_status = ''

    context = {
        'submissions': submissions,
        'page_title': '提交记录',
        'cache_status': cache_status,
        'cache_timeout': SubmissionCache.get_cache_timeout()
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)


# 管理缓存
@login_required
def clear_my_submission_cache(request):
    """清除当前用户的提交记录缓存"""
    user_name = request.user.username
    SubmissionCache.delete_submissions(user_name)
    messages.success(request, '您的提交记录缓存已清除')
    return redirect('CheckObjectionApp:my_submission_list')


@user_passes_test(lambda u: u.is_staff)
def update_cache_timeout(request):
    """管理员更新缓存超时时间"""
    if request.method == 'POST':
        try:
            timeout = int(request.POST.get('timeout', 300))
            if timeout < 0:
                return JsonResponse({'success': False, 'error': '超时时间不能为负数'})

            SubmissionCache.set_cache_timeout(timeout)
            return JsonResponse({'success': True, 'new_timeout': timeout})
        except ValueError:
            return JsonResponse({'success': False, 'error': '无效的超时时间'})

    return JsonResponse({'success': False, 'error': '仅支持POST请求'})

# 基于类的视图（推荐）
class SubmissionListView(LoginRequiredMixin, ListView):
    """使用类视图显示提交列表"""
    model = Submission
    template_name = 'CheckObjection/submission/submission_list.html'
    context_object_name = 'submissions'
    paginate_by = 10

    def get_queryset(self):
        return Submission.objects.filter(
            user_name=self.request.user.username
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '我的提交记录'
        return context


class SubmissionDetailView(LoginRequiredMixin, DetailView):
    """使用类视图显示提交详情"""
    model = Submission
    template_name = 'CheckObjection/submission/submission_detail.html'
    context_object_name = 'submission'

    def get_queryset(self):
        return Submission.objects.filter(user_name=self.request.user.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'提交详情 - {self.object.topic_id}'
        return context


@login_required
def query_contest_submission_list(request, user_name, contest_id):
    """显示查询单个用户在指定比赛中的所有提交记录"""
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
                'submission',  # 预加载submission对象
                'submission__topic',  # 预加载submission的topic对象
                'participant'  # 预加载participant对象
            ).order_by('-submitted_at')

            # 处理数据，将需要的信息提取出来
            processed_submissions = []
            for contest_submission in contest_submissions_queryset:
                submission = contest_submission.submission
                processed_submissions.append({
                    'contest_submission_id': contest_submission.id,
                    'id': submission.id,  # 添加submission的id
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
                    # 保留原始对象引用以便其他用途
                    'original_submission': submission,
                    'original_contest_submission': contest_submission
                })

            # 设置缓存
            cache_timeout = SubmissionCache.get_cache_timeout()
            cache.set(cache_key, processed_submissions, cache_timeout)
            submissions = processed_submissions

            cache_status = '数据库查询'

        except Contest.DoesNotExist:
            # 比赛不存在
            submissions = []
            cache_status = '比赛不存在'

    else:
        cache_status = '缓存命中'

    context = {
        'submissions': submissions,
        'page_title': f'比赛提交记录 - 用户: {user_name}',
        'cache_status': cache_status,
        'cache_timeout': SubmissionCache.get_cache_timeout(),
        'contest_id': contest_id,
        'user_name': user_name
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)


@login_required
@staff_member_required
def query_contest_topic_submission_list(request, contest_id, topic_id):
    """显示查询单个比赛题目的所有提交记录(管理员视图）"""
    try:
        # 获取比赛和题目信息
        contest = Contest.objects.get(id=contest_id)
        contest_topic = ContestTopic.objects.get(contest=contest, topic_id=topic_id)

        # 构建缓存键
        cache_key = f"contest_{contest_id}_topic_{topic_id}_submissions"

        # 尝试从缓存获取数据
        submissions = cache.get(cache_key)

        if submissions is None:
            # 缓存中没有，从数据库查询
            # 通过ContestSubmission获取该比赛该题目的所有提交
            contest_submissions = ContestSubmission.objects.filter(
                contest=contest,
                submission__topic_id=topic_id
            ).select_related(
                'submission',
                'submission__topic',
                'participant',
                'participant__user'
            ).order_by('-submitted_at')

            # 构建包含详细信息的提交列表
            submissions_list = []
            for cs in contest_submissions:
                submission_data = {
                    'id': cs.submission.id,
                    'user_name': cs.submission.user_name,
                    'participant': cs.participant,
                    'source_code': cs.submission.source_code,
                    'language_id': cs.submission.language_id,
                    'status': cs.submission.status,
                    'overall_result': cs.submission.overall_result,
                    'results': cs.submission.results,
                    'notes': cs.submission.notes,
                    'created_at': cs.submission.created_at,
                    'updated_at': cs.submission.updated_at,
                    'topic': cs.submission.topic,
                    'submitted_at': cs.submitted_at,
                    'contest': contest
                }
                submissions_list.append(submission_data)

            # 设置缓存
            cache_timeout = 300  # 5分钟缓存，可以根据需要调整
            cache.set(cache_key, submissions_list, cache_timeout)
            submissions = submissions_list

        cache_status = '缓存命中' if cache.get(cache_key) else '缓存未命中'

        context = {
            'submissions': submissions,
            'contest': contest,
            'topic': contest_topic.topic,
            'page_title': f'{contest.title} - {contest_topic.topic.title} 提交记录',
            'cache_status': cache_status,
            'cache_timeout': 300
        }
        return render(request, 'CheckObjection/submission/submission_list.html', context)

    except Contest.DoesNotExist:
        return render(request, 'CheckObjection/base/noPower.html', {'error_message': '比赛不存在'})
    except ContestTopic.DoesNotExist:
        return render(request, 'CheckObjection/base/noPower.html', {'error_message': '该题目不在比赛中或不存在'})

@login_required
def my_contest_submission_list(request):
    """显示我的所有比赛提交记录（带缓存）"""
    user_name = request.user.username
    cache_key = f"user_contest_submissions_{user_name}"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)
    if submissions is None:
        # 缓存中没有，从数据库查询：查询比赛相关的提交记录
        contest_submissions_queryset = ContestSubmission.objects.filter(
            participant__user=request.user
        ).select_related(
            'submission__topic',  # 预加载提交的题目
            'contest',  # 预加载比赛信息
            'participant'  # 预加载参与者信息
        ).order_by('-submitted_at')

        # 将查询结果转换为包含所需数据的字典列表
        submissions_data = []
        for contest_submission in contest_submissions_queryset:
            submission = contest_submission.submission
            submissions_data.append({
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
                # 保留原始对象引用以便其他可能需要的数据
                'contest_submission': contest_submission,
                'submission_obj': submission
            })

        # 设置缓存
        cache_timeout = 300  # 5分钟缓存，可以根据需要调整
        cache.set(cache_key, submissions_data, cache_timeout)
        submissions = submissions_data

        cache_status = '数据库查询'
    else:
        cache_status = '缓存命中'

    context = {
        'submissions': submissions,
        'page_title': '比赛提交记录',
        'cache_status': cache_status,
        'cache_timeout': 300
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)

@login_required
def query_contest_submission_list(request, user_name, contest_id):
    """显示查询单个用户在指定比赛中的所有提交记录"""
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
                'submission',  # 预加载submission对象
                'submission__topic',  # 预加载submission的topic对象
                'participant'  # 预加载participant对象
            ).order_by('-submitted_at')

            # 处理数据，将需要的信息提取出来
            processed_submissions = []
            for contest_submission in contest_submissions_queryset:
                submission = contest_submission.submission
                processed_submissions.append({
                    'contest_submission_id': contest_submission.id,
                    'id': submission.id,  # 添加submission的id
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
                    # 保留原始对象引用以便其他用途
                    'original_submission': submission,
                    'original_contest_submission': contest_submission
                })

            # 设置缓存
            cache_timeout = SubmissionCache.get_cache_timeout()
            cache.set(cache_key, processed_submissions, cache_timeout)
            submissions = processed_submissions

            cache_status = '数据库查询'

        except Contest.DoesNotExist:
            # 比赛不存在
            submissions = []
            cache_status = '比赛不存在'

    else:
        cache_status = '缓存命中'

    context = {
        'submissions': submissions,
        'page_title': f'比赛提交记录 - 用户: {user_name}',
        'cache_status': cache_status,
        'cache_timeout': SubmissionCache.get_cache_timeout(),
        'contest_id': contest_id,
        'user_name': user_name
    }
    return render(request, 'CheckObjection/submission/submission_list.html', context)


@login_required
@staff_member_required
def query_contest_topic_submission_list(request, contest_id, topic_id):
    """显示查询单个比赛题目的所有提交记录(管理员视图）"""
    try:
        # 获取比赛和题目信息
        contest = Contest.objects.get(id=contest_id)
        contest_topic = ContestTopic.objects.get(contest=contest, topic_id=topic_id)

        # 构建缓存键
        cache_key = f"contest_{contest_id}_topic_{topic_id}_submissions"

        # 尝试从缓存获取数据
        submissions = cache.get(cache_key)

        if submissions is None:
            # 缓存中没有，从数据库查询
            # 通过ContestSubmission获取该比赛该题目的所有提交
            contest_submissions = ContestSubmission.objects.filter(
                contest=contest,
                submission__topic_id=topic_id
            ).select_related(
                'submission',
                'submission__topic',
                'participant',
                'participant__user'
            ).order_by('-submitted_at')

            # 构建包含详细信息的提交列表
            submissions_list = []
            for cs in contest_submissions:
                submission_data = {
                    'id': cs.submission.id,
                    'user_name': cs.submission.user_name,
                    'participant': cs.participant,
                    'source_code': cs.submission.source_code,
                    'language_id': cs.submission.language_id,
                    'status': cs.submission.status,
                    'overall_result': cs.submission.overall_result,
                    'results': cs.submission.results,
                    'notes': cs.submission.notes,
                    'created_at': cs.submission.created_at,
                    'updated_at': cs.submission.updated_at,
                    'topic': cs.submission.topic,
                    'submitted_at': cs.submitted_at,
                    'contest': contest
                }
                submissions_list.append(submission_data)

            # 设置缓存
            cache_timeout = 300  # 5分钟缓存，可以根据需要调整
            cache.set(cache_key, submissions_list, cache_timeout)
            submissions = submissions_list

        cache_status = '缓存命中' if cache.get(cache_key) else '缓存未命中'

        context = {
            'submissions': submissions,
            'contest': contest,
            'topic': contest_topic.topic,
            'page_title': f'{contest.title} - {contest_topic.topic.title} 提交记录',
            'cache_status': cache_status,
            'cache_timeout': 300
        }
        return render(request, 'CheckObjection/submission/submission_list.html', context)

    except Contest.DoesNotExist:
        return render(request, 'CheckObjection/base/noPower.html', {'error_message': '比赛不存在'})
    except ContestTopic.DoesNotExist:
        return render(request, 'CheckObjection/base/noPower.html', {'error_message': '该题目不在比赛中或不存在'})



@login_required
def contest_my_submissions(request, contest_id):
    """显示当前用户在特定比赛中的提交记录"""
    contest = get_object_or_404(Contest, id=contest_id)
    user_name = request.user.username

    # 检查用户是否参与比赛
    is_participant = ContestParticipant.objects.filter(
        contest=contest,
        user=request.user,
        is_disqualified=False
    ).exists()

    if not is_participant:
        context = {
            'contest': contest,
            'error_message': '您未参加此比赛或已被取消资格'
        }
        return render(request, 'CheckObjection/submission/contest_submission_list.html', context)

    # 缓存键
    cache_key = f"contest_{contest_id}_user_{user_name}_submissions"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        # 查询当前用户在比赛中的提交记录
        contest_submissions = ContestSubmission.objects.filter(
            contest_id=contest_id,
            participant__user=request.user
        ).select_related(
            'submission',
            'submission__topic'
        ).order_by('-submitted_at')

        # 转换为可缓存格式
        submissions_list = list(contest_submissions)
        cache.set(cache_key, submissions_list, 300)
        submissions = submissions_list

    context = {
        'contest': contest,
        'submissions': submissions,
        'target_user_name': user_name,
        'page_title': f'我的 {contest.title} 提交记录',
        'is_my_submissions': True
    }
    return render(request, 'CheckObjection/submission/contest_submission_list.html', context)