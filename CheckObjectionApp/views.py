from django.shortcuts import render,redirect,reverse
import string
from django.http.response import JsonResponse
# Create your views here.
import random
from django.core.mail import send_mail
from django.views import View
from django.views.decorators.http import require_http_methods,require_POST,require_GET

from django.contrib.auth import get_user_model,login,logout
from django.urls.base import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .code import check_code
from .models import answer
from .forms import LoginForm
from .models import UserProfile
from django.db.models import F
# TODO 生产环境时打开csrf验证
from django.views.decorators.csrf import csrf_exempt

from CheckObjectionApp.serializers import topicSerializer
from CheckObjectionApp.serializers import topicModelSerializer
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin

User = get_user_model()
from .models import topic
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


def redirect_root(request):
    """ 重定向到主页 """
    return redirect('http://localhost:8000/CheckObjectionApp/CheckObjection_login?next=/CheckObjectionApp/index')
class Topic(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,  # 添加 CreateModelMixin
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView
):
    queryset = topic.objects.all()
    serializer_class = topicModelSerializer

    def get(self, request, pk=None):
        if pk is not None:
            return self.retrieve(request, pk)
        else:
            return self.list(request)

    def post(self, request):
        return self.create(request)  # 调用 CreateModelMixin 的 create 方法

    def put(self, request, pk=None):
        return self.update(request, pk)

    def patch(self, request, pk=None):
        return self.partial_update(request, pk)

    def delete(self, request, pk=None):
        return self.destroy(request, pk)


class topic_get(View):
    def get(self, request):  # 改为标准的 get 方法
        topic_one = topic.objects.first()
        serializer = topicSerializer(topic_one)
        return JsonResponse(serializer.data,
                            json_dumps_params={'ensure_ascii': False, 'indent': 2},
                            safe=False)
class topicModel_get(View):
    def get(self,request):
        topics = topic.objects.all()
        serializer = topicModelSerializer(topics,many=True)
        return JsonResponse(serializer.data,
                            json_dumps_params={'ensure_ascii': False, 'indent': 2},
                            safe=False)
class topicAPIView(APIView):
    def get(self, request):
        return Response({'data':'xiaoming'})
class topicAPIGenericAPIView(GenericAPIView):
    serializer_class = topicSerializer
    queryset = topic.objects.all()

    def get(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return JsonResponse(serializer.data,
                            json_dumps_params={'ensure_ascii': False, 'indent': 2},
                            safe=False)
    # def get(self, request):
    #     serializer = self.get_serializer(self.get_queryset(), many=True)
    #     return JsonResponse(serializer.data,
    #                         json_dumps_params={'ensure_ascii': False, 'indent': 2},
    #                         safe=False)

def get1(request):
    topic_one = topic.objects.first()
    serializer = topicSerializer(topic_one)
    return JsonResponse(serializer.data,
                        json_dumps_params={'ensure_ascii': False, 'indent': 2},
                        safe=False  # 如果返回的是非字典数据，需要设置 safe=False
                        )

def socket_index(request):
    # 从 URL 参数获取 num，如果没有则使用默认值
    qq_group_num = request.GET.get('num', 'default_group')
    print(f"当前群组号: {qq_group_num}")  # 调试信息
    context = {
        'qq_group_num': qq_group_num
    }
    return render(request, 'CheckObjection/index.html', context)
@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def index(request):
    """算法提交平台首页"""
    topics = topic.objects.all()
    user = request.user
    user_profile = UserProfile.objects.get(user_id=user.id)
    return render(request, 'CheckObjection/CheckObjection_Index.html', context={'topics': topics, 'user':user, 'user_profile':user_profile})

def base(request):
    return render(request,'CheckObjection/CheckObjectionApp_base.html')


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def detail(request, topic_id):
    if request.method == "POST":
        # 使用 F() 表达式原子性地增加 finish 计数
        user_profile, created = UserProfile.objects.get_or_create(
            user_id=request.user.id,
            defaults={'finish': 1}  # 如果是新创建，直接设为1
        )

        if not created:
            # 如果不是新创建的，原子性地增加计数
            UserProfile.objects.filter(
                user_id=request.user.id
            ).update(finish=F('finish') + 1)

        content = request.POST.get('content')
        notes = request.POST.get('notes')
        user_name = request.POST.get('user_name')

        answer.objects.create(
            topic_id=topic_id,
            content=content,
            notes=notes,
            user_name=user_name
        )

        return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))
    else:
        topic_content = topic.objects.get(id=topic_id)
        user = request.user
        return render(request, 'CheckObjection/CheckObjection_detail.html',
                      context={'topic_content': topic_content, 'user': user})
@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def design(request):
    if not request.user.is_staff:
        return redirect("CheckObjectionApp:CheckObjection_noPower")
    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        example = request.POST.get('example')
        level = request.POST.get('level')
        topic.objects.create(content=content, title=title,example=example, level=level)
        return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))
    else:
        return render(request,'CheckObjection/CheckObjection_design.html')

@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def show(request):

    if not request.user.is_staff:
        return redirect("CheckObjectionApp:CheckObjection_noPower")

    answers = answer.objects.all()
    topics = topic.objects.all()
    return render(request,'CheckObjection/CheckObjection_show.html',context={'answers':answers,'topics':topics})


from django.http import HttpResponse

@require_http_methods(['GET', 'POST'])
@csrf_exempt
def CheckObjection_login(request):
    if request.method == 'GET':
        return render(request, 'CheckObjection/CheckObjection_login.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # 检查用户名和密码是否为空
        if not username or not password:
            # 返回错误信息，提示用户名和密码不能为空
            return HttpResponse("用户名和密码不能为空")

        # 检查用户是否存在，如果不存在则创建用户
        if not User.objects.filter(username=username).first():
            # 注意：这里如果用户不存在，就创建用户。但是通常登录逻辑不应该自动创建用户，而是应该返回错误。
            # 如果你希望是注册逻辑，那么这里创建用户是合理的。但如果是纯登录，那么这里应该返回错误。
            # 根据你的需求，这里保持原样，但请注意这可能不是标准的登录行为。
            user = User.objects.create_user(username=username, password=password)
            user_profile = UserProfile.objects.create(user_id=user.id)
        else:
            print('密码错误')

        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            return redirect(reverse('CheckObjectionApp:CheckObjectionApp_index'))
        else:
            # 如果密码错误，则重定向到登录页面
            return redirect(reverse('CheckObjectionApp:CheckObjectionApp_login'))

def CheckObjection_logout(request):
    """退出功能实现"""
    logout(request)
    return redirect('CheckObjectionApp:CheckObjectionApp_index')

def CheckObjection_noPower(request):
    return render(request,'CheckObjection/CheckObjection_noPower.html')


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def changePassword(request):
    """修改密码"""
    if request.method == "POST":
        user_id = request.user.id
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        check_new_password = request.POST.get('check_new_password', '').strip()

        # 1. 获取单个用户实例（用get()而非filter()）
        user = User.objects.get(id=user_id)  # get()返回单个User对象

        # 2. 验证旧密码和新密码
        if not old_password or not new_password or not check_new_password:
            return redirect(reverse("CheckObjectionApp:CheckObjectionApp_changePassword"))  # 跳回密码修改页

        if new_password != check_new_password:
            return redirect(reverse("CheckObjectionApp:CheckObjectionApp_changePassword"))

        if not user.check_password(old_password):  # 现在user是实例，可以调用check_password
            return redirect(reverse("CheckObjectionApp:CheckObjectionApp_changePassword"))

        # 3. 正确设置新密码（自动加密）
        user.set_password(new_password)  # set_password会自动加密密码
        user.save()  # 保存修改

        return redirect(reverse("CheckObjectionApp:CheckObjectionApp_login"))  # 建议修改后重新登录

    if request.method == "GET":
        user = request.user
        return render(request, 'CheckObjection/CheckObjection_changeName.html', context={'user': user})
@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def changeName(request):
    """修改用户名"""
    if request.method == "POST":
        user_id = request.user.id
        User.objects.filter(id=user_id).update(username=request.POST.get('username',''))
        # 正确示例：批量更新QuerySet中的所有对象
        # 你的模型类.objects.filter(某个条件).update(name="新名称")  # 直接更新，无需save()
        return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))
    if request.method == "GET":
        user = request.user
        return render(request,'CheckObjection/CheckObjection_changeName.html',context={'user':user})
# @require_GET
# @login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
# def CheckObjection_search(request):
#     """搜索模块 会按下面的url格式传参"""
#     #/search?q=xxx
#     q = request.GET.get('q')
#     topics = topic.objects.filter(Q(title__icontains=q)|Q(content__icontains=q)).all()
#     user = request.user
#     return render(request,'CheckObjection/CheckObjection_Index.html', context={"topics": topics,'user':user})

# 以下是搜索模块
from django.core.cache import cache
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.db.models import Q
from .models import topic
import json
from datetime import timedelta


@require_GET
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def CheckObjection_search(request):
    """搜索模块 会按下面的url格式传参"""
    # /search?q=xxx
    q = request.GET.get('q')

    # 如果搜索词为空，返回空结果
    if not q:
        return render(request, 'CheckObjection/CheckObjection_Index.html', context={"topics": []})

    # 创建基于搜索词的缓存键
    cache_key = f"search_results:{q.lower()}"

    # 尝试从Redis缓存获取结果
    cached_results = cache.get(cache_key)

    if cached_results is not None:
        # 如果缓存存在，直接使用缓存的结果
        # 这里我们存储的是博客ID列表，需要从数据库获取完整对象
        topic_ids = json.loads(cached_results)
        topics = topic.objects.filter(id__in=topic_ids)
    else:
        # 如果缓存不存在，执行数据库查询
        topics = topic.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q)
        )

        # 将结果缓存到Redis，存储ID列表而不是完整对象
        topic_ids = list(topics.values_list('id', flat=True))
        cache.set(
            cache_key,
            json.dumps(topic_ids),
            timeout=300  # 缓存5分钟，根据需求调整
        )

    return render(request, 'CheckObjection/CheckObjection_Index.html', context={"topics": topics})

@require_GET
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def CheckObjection_filter(request):
    """过滤模块 会按下面的url格式传参"""
    # /search?q=xxx
    q = request.GET.get('f')
    if q == 'all':
        topics = topic.objects.all()
        return render(request, 'CheckObjection/CheckObjection_Index.html', context={"topics": topics})

    # 如果搜索词为空，返回空结果
    if not q:
        return render(request, 'CheckObjection/CheckObjection_Index.html', context={"topics": []})

    # 创建基于搜索词的缓存键
    cache_key = f"filter_results:{q.lower()}"

    # 尝试从Redis缓存获取结果
    cached_results = cache.get(cache_key)

    if cached_results is not None:
        print('使用缓存')
        # 如果缓存存在，直接使用缓存的结果
        # 这里我们存储的是博客ID列表，需要从数据库获取完整对象
        topic_ids = json.loads(cached_results)
        topics = topic.objects.filter(id__in=topic_ids)
    else:
        print('无缓存')
        # 如果缓存不存在，执行数据库查询
        topics = topic.objects.filter(
            Q(level=q)
        )

        # 将结果缓存到Redis，存储ID列表而不是完整对象
        topic_ids = list(topics.values_list('id', flat=True))
        cache.set(
            cache_key,
            json.dumps(topic_ids),
            timeout=300  # 缓存5分钟，根据需求调整
        )

    return render(request, 'CheckObjection/CheckObjection_Index.html', context={"topics": topics})

# 以下为判题模块
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import TestCase, topic
from mycelery.sms.tasks import submit_code_task, process_test_run


@method_decorator(csrf_exempt, name='dispatch')
class JudgeCodeView(View):
    def post(self, request):
        """
        判题接口 - 使用Celery异步处理
        """
        try:
            data = json.loads(request.body)

            source_code = data.get('source_code', '')
            language_id = data.get('language_id', 71)
            topic_id = data.get('topic_id', '')
            user_name = data.get('user_name', '')
            notes = data.get('notes', '')
            is_test = data.get('is_test', False)

            # 生成唯一的提交ID
            submission_id = str(uuid.uuid4())

            submission_data = {
                'source_code': source_code,
                'language_id': language_id,
                'topic_id': topic_id,
                'user_name': user_name,
                'notes': notes,
                'submission_id': submission_id,
                'is_test': is_test
            }


            if is_test:
                # 测试运行 - 同步处理以便快速返回
                result = process_test_run.delay(submission_data)
                try:
                    # 等待任务完成，设置超时时间
                    task_result = result.get(timeout=30)
                    return JsonResponse(task_result)
                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "error": f"测试运行超时或失败: {str(e)}",
                        "is_test_run": True
                    })
            else:
                # 正式提交 - 异步处理

                task = submit_code_task.delay(submission_data)

                # 立即返回任务ID，前端可以轮询结果
                return JsonResponse({
                    "success": True,
                    "message": "代码已提交，正在处理中...",
                    "task_id": task.id,
                    "submission_id": submission_id,
                    "status": "PENDING"
                })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"处理请求时出错: {str(e)}"
            })


@method_decorator(csrf_exempt, name='dispatch')
class TaskStatusView(View):
    """
    查询任务状态的接口
    """

    def get(self, request, task_id):
        from celery.result import AsyncResult
        from mycelery.sms.tasks import submit_code_task

        task_result = AsyncResult(task_id, app=submit_code_task.app)

        response_data = {
            'task_id': task_id,
            'status': task_result.status,
        }

        if task_result.ready():
            if task_result.successful():
                response_data['result'] = task_result.result
            else:
                response_data['error'] = str(task_result.result)

        return JsonResponse(response_data)

# 以下是增加测试用例的代码
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import topic, TestCase
from .serializers import *


class TopicViewSet(viewsets.ModelViewSet):
    queryset = topic.objects.all().annotate(test_cases_count=Count('testcase_set'))
    serializer_class = TopicSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TopicWithTestCasesSerializer
        return TopicSerializer

    @action(detail=True, methods=['get'])
    def test_cases(self, request, pk=None):
        """获取特定题目的所有测试用例"""
        topic_obj = self.get_object()
        test_cases = topic_obj.testcase_set.all()

        serializer = TestCaseSerializer(test_cases, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_test_case(self, request, pk=None):
        """为特定题目添加测试用例"""
        topic_obj = self.get_object()
        serializer = TestCaseSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(titleSlug=topic_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def with_test_cases(self, request):
        """获取包含测试用例的题目列表"""
        topics = topic.objects.prefetch_related('testcase_set').all()
        serializer = TopicWithTestCasesSerializer(topics, many=True)
        return Response(serializer.data)


class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer

    def get_queryset(self):
        queryset = TestCase.objects.all()
        topic_id = self.request.query_params.get('topic_id')
        is_sample = self.request.query_params.get('is_sample')

        if topic_id:
            queryset = queryset.filter(titleSlug_id=topic_id)
        if is_sample is not None:
            queryset = queryset.filter(is_sample=is_sample.lower() == 'true')

        return queryset

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return TestCaseDetailSerializer
        return TestCaseSerializer

    def create(self, request, *args, **kwargs):
        """创建测试用例"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 验证外键存在
            topic_id = request.data.get('titleSlug')
            if not topic.objects.filter(id=topic_id).exists():
                return Response(
                    {'error': '指定的题目不存在'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def update_topic(self, request, pk=None):
        """更新测试用例所属的题目"""
        test_case = self.get_object()
        new_topic_id = request.data.get('titleSlug')

        if not new_topic_id:
            return Response(
                {'error': '必须提供题目ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_topic = topic.objects.get(id=new_topic_id)
            test_case.titleSlug = new_topic
            test_case.save()

            serializer = self.get_serializer(test_case)
            return Response(serializer.data)
        except topic.DoesNotExist:
            return Response(
                {'error': '指定的题目不存在'},
                status=status.HTTP_404_NOT_FOUND
            )


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Submission


# 基于函数的视图
@login_required
def submission_list(request):
    """显示全部用户的所有提交记录"""
    submissions = Submission.objects.all()
    context = {
        'submissions': submissions,
        'page_title': '全部提交记录'
    }
    return render(request, 'CheckObjection/submission_list.html', context)


@login_required
def submission_detail(request, pk):
    """显示单个提交记录的详细信息"""
    submission = get_object_or_404(Submission, pk=pk)
    context = {
        'submission': submission,
        'page_title': f'提交详情 - {submission.topic_id}'
    }
    return render(request, 'CheckObjection/submission_detail.html', context)

@login_required
def my_submission_list(request):
    """显示我的所有提交记录"""
    submissions = Submission.objects.filter(user_name=request.user.username)
    context = {
        'submissions': submissions,
        'page_title': '我的提交记录'
    }
    return render(request, 'CheckObjection/submission_list.html', context)



# 基于类的视图（推荐）
class SubmissionListView(LoginRequiredMixin, ListView):
    """使用类视图显示提交列表"""
    model = Submission
    template_name = 'CheckObjection/submission_list.html'
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
    template_name = 'CheckObjection/submission_detail.html'
    context_object_name = 'submission'

    def get_queryset(self):
        return Submission.objects.filter(user_name=self.request.user.username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'提交详情 - {self.object.topic_id}'
        return context

# 以下是排行榜功能
from django.db.models import Count, Q
from django.http import JsonResponse
from .models import Submission, User, UserProfile


def ranking_view(request):
    """排行榜页面，直接渲染所有数据"""
    # 获取所有用户通过的题目统计（去重）
    user_rankings = Submission.objects.filter(
        overall_result='Accepted'
    ).values('user_name').annotate(
        solved_count=Count('topic_id', distinct=True)
    ).order_by('-solved_count')


    # 构建排行榜数据
    rankings = []
    for rank, user_data in enumerate(user_rankings, 1):
        rankings.append({
            'rank': rank,
            'user_name': user_data['user_name'],
            'solved_count': user_data['solved_count'],
        })

    context = {
        'rankings': rankings,
        'total_users': len(rankings)
    }

    return render(request, 'CheckObjection/CheckObjection_ranking.html', context)


from io import BytesIO

def image_code(request):
    "生成图片验证码"
    #调用pillow函数，生成图片
    img,code_string = check_code()
    print(code_string)
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())

