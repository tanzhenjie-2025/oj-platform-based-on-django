from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import render,redirect,reverse
import string
from django.http.response import JsonResponse
# Create your views here.
import random
from django.core.mail import send_mail
from django.views import View
from django.views.decorators.http import require_http_methods,require_POST,require_GET

from django.contrib.auth import get_user_model, login, logout, authenticate
from django.urls.base import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from CheckObjection.settings import DB_QUERY_KEY, CACHE_KEY_HIT
from .code import check_code
from .models import answer, Contest, ContestParticipant, ContestSubmission
from .forms import LoginForm, RegisterForm
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
    return redirect('CheckObjectionApp:CheckObjectionApp_login')
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


# todo 下面这段代码的逻辑不知道在写什么，有空重构 改造成写题解好了 有助于加深思考
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
        return render(request, 'CheckObjection/submission/practice_submission.html',
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


# 以下为登录模块
from django.http import HttpResponse


@require_http_methods(['GET', 'POST'])
@csrf_exempt
def CheckObjection_login(request):
    if request.method == 'GET':
        form = LoginForm()
        content = {'form': form}
        return render(request, 'CheckObjection/CheckObjection_login.html', content)
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            user_input_captcha = form.cleaned_data.pop('captcha')
            user_captcha = str(request.session.get('captcha'))

            # 验证码校验
            if user_input_captcha.lower() != user_captcha.lower():
                form.add_error('captcha', '验证码错误，请重新输入')
                content = {'form': form}
                return render(request, 'CheckObjection/CheckObjection_login.html', content)

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember = form.cleaned_data.get('remember')
            user = authenticate(username=username, password=password)

            if user is not None:
                # 检查用户是否激活
                if not user.is_active:
                    form.add_error(None, '账户已被禁用，请联系管理员')
                    content = {'form': form}
                    return render(request, 'CheckObjection/CheckObjection_login.html', content)

                login(request, user)
                request.session['captcha'] = None
                if remember:
                    request.session.set_expiry(60 * 60 * 24 * 7)
                else:
                    request.session.set_expiry(0)
                return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))
            else:
                # 用户认证失败，检查是用户名问题还是密码问题
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user_exists = User.objects.filter(username=username).exists()
                    if not user_exists:
                        form.add_error('username', '用户名不存在')
                    else:
                        form.add_error('password', '密码错误')
                except Exception:
                    form.add_error(None, '用户名或密码错误')

                content = {'form': form}
                return render(request, 'CheckObjection/CheckObjection_login.html', content)
        else:
            # 表单验证失败，错误信息已经在form中
            content = {'form': form}
            return render(request, 'CheckObjection/CheckObjection_login.html', content)


@require_http_methods(['GET', 'POST'])
def CheckObjection_register(request):
    """注册功能实现"""
    if request.method == 'GET':
        form = RegisterForm()
        return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})
    else:
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_input_captcha = form.cleaned_data.get('captcha')
            user_captcha = str(request.session.get('captcha', ''))

            # 验证验证码
            if not user_captcha:
                form.add_error('captcha', '验证码已过期，请刷新验证码')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            if user_input_captcha.lower() != user_captcha.lower():
                form.add_error('captcha', '验证码错误')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            # 双重检查用户名是否存在（防止并发注册等情况）
            if User.objects.filter(username=username).exists():
                form.add_error('username', '用户名已存在')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            try:
                # 创建用户
                user = User.objects.create_user(username=username, password=password)
                user_profile = UserProfile.objects.create(user_id=user.id)
                login(request, user)

                # 设置session过期时间
                if form.cleaned_data.get('remember'):
                    request.session.set_expiry(60 * 60 * 24 * 7)
                else:
                    request.session.set_expiry(0)

                # 注册成功后清除验证码session
                if 'captcha' in request.session:
                    del request.session['captcha']

                return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))

            except IntegrityError:
                # 处理数据库唯一性约束错误（用户名重复）
                form.add_error('username', '用户名已存在，请选择其他用户名')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

            except Exception as e:
                # 处理创建用户时的意外错误
                form.add_error(None, f'注册失败：{str(e)}')
                return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})

        else:
            # 表单验证失败，返回错误信息
            return render(request, 'CheckObjection/CheckObjection_register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
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
    """修改用户资料"""
    if request.method == "POST":
        user_id = request.user.id
        # 更新用户信息
        User.objects.filter(id=user_id).update(
            username=request.POST.get('username', ''),
            # 添加其他字段的更新，根据你的用户模型
            # email=request.POST.get('email', ''),
            # phone=request.POST.get('phone', ''),
            # 等等...
        )
        return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))

    if request.method == "GET":
        user = request.user
        # 准备用户信息，处理空值
        user_info = {
            'username': user.username or '暂无',
            'email': getattr(user, 'email', '') or '暂无',
            'phone': getattr(user, 'phone', '') or '暂无',
            'birthday': getattr(user, 'birthday', '') or '暂无',
            'bio': getattr(user, 'bio', '') or '暂无',
            'location': getattr(user, 'location', '') or '暂无',
            'website': getattr(user, 'website', '') or '暂无',
        }
        return render(request, 'CheckObjection/CheckObjection_changeName.html',
                      context={'user': user, 'user_info': user_info})
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

# 日常提交判题
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


from django.core.cache import cache
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Submission
from .utils.cache_utils import SubmissionCache


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

    print(submissions)

    context = {
        'submissions': submissions,
        'page_title': '提交记录',
        'cache_status': cache_status,
        'cache_timeout': SubmissionCache.get_cache_timeout()
    }
    return render(request, 'CheckObjection/submission_list.html', context)

@login_required
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
    return render(request, 'CheckObjection/submission_list.html', context)


# TODO 下面这个函数还未完成
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
    return render(request, 'CheckObjection/submission_list.html', context)

# @login_required
# def my_submission_list(request):
#     """显示我的所有提交记录"""
#     submissions = Submission.objects.filter(user_name=request.user.username)
#     context = {
#         'submissions': submissions,
#         'page_title': '我的提交记录'
#     }
#     return render(request, 'CheckObjection/submission_list.html', context)

# views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from .utils.cache_utils import SubmissionCache


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
    request.session['captcha'] = code_string
    # 给Session设置60s超时
    request.session.set_expiry(60)
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())

# 以下是比赛模块
# views/contest_views.py
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from CheckObjectionApp.utils.contest_service import ContestService
from datetime import timezone
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

# todo 1 传递比赛信息 传递提交信息
# todo 1 传递比赛信息 传递提交信息
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

                    if submission.submission.overall_result == 'AC':
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

        # 添加到context
        context['problem_scores'] = problem_scores
        context['problem_submissions_stats'] = problem_submissions_stats
        context['total_score'] = total_score
        context['contest_total_score'] = sum(topic.score for topic in contest_topics)
        context['ac_rate'] = ac_rate
        context['total_ac_count'] = total_ac_count
        context['total_problems'] = len(contest_topics)
        context['solved_problems'] = solved_problems

        return context


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

# 比赛提交界面 todo 2 加载时要有比赛资料 还要改造比赛提交界面 传递比赛 id
@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('CheckObjectionApp:CheckObjectionApp_login'))
def contest_submit_code(request, contest_id,contest_topic_id):
    if request.method == 'GET':
        topic_content = topic.objects.get(id=contest_topic_id)
        user = request.user
        context = {
            'topic_content': topic_content,
            'user': user,
            'contest_id': contest_id,
            'contest_topic_id': contest_topic_id,
        }
        return render(request, 'CheckObjection/submission/contest_submission.html',
                      context=context)

# 比赛提交判题 todo 没做完 记得重启异步任务
@method_decorator(csrf_exempt, name='dispatch')
class JudgeContestCodeView(View):
    def post(self, request):
        """
        判题接口 - 使用Celery异步处理
        """
        try:
            contest = True
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
                'contest': contest,
                'source_code': source_code,
                'language_id': language_id,
                'topic_id': topic_id,
                'user_name': user_name,
                'notes': notes,
                'submission_id': submission_id,
                'is_test': is_test
            }
            # 判断是否测试运行
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

# todo 下面五个函数没写完
# 以下为比赛代码提交记录展示
@login_required
def contest_submission_list(request):
    """显示全部比赛的所有提交记录（管理员视图）"""

    # 检查用户权限，如果是管理员则显示所有提交
    if request.user.is_staff:
        contest_submissions = ContestSubmission.objects.all().select_related(
            'contest',
            'submission',
            'submission__topic',
            'participant__user'
        ).order_by('-submitted_at')
    else:
        # 普通用户只能看到自己的提交
        contest_submissions = ContestSubmission.objects.filter(
            participant__user=request.user
        ).select_related(
            'contest',
            'submission',
            'submission__topic',
            'participant'
        ).order_by('-submitted_at')

    context = {
        'submissions': contest_submissions,
        'page_title': '比赛提交记录'
    }
    return render(request, 'CheckObjection/submission_list.html', context)

@login_required
def contest_submission_detail(request, pk):
    """显示单个提交记录的详细信息"""
    submission = get_object_or_404(Submission, pk=pk)
    context = {
        'submission': submission,
        'page_title': f'提交详情 - {submission.topic_id}'
    }
    return render(request, 'CheckObjection/submission_detail.html', context)

@login_required
def my_contest_submission_list(request):
    """显示我的所有比赛提交记录（带缓存）"""
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

    print(submissions)

    context = {
        'submissions': submissions,
        'page_title': '提交记录',
        'cache_status': cache_status,
        'cache_timeout': SubmissionCache.get_cache_timeout()
    }
    return render(request, 'CheckObjection/submission_list.html', context)

@login_required
def query_contest_submission_list(request, user_name):
    """显示查询单个用户的所有比赛提交记录"""
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
    return render(request, 'CheckObjection/submission_list.html', context)

@login_required
def query_contest_topic_submission_list(request, user_name):
    """显示查询单个比赛题目的所有提交记录"""
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
    return render(request, 'CheckObjection/submission_list.html', context)


# 批量导入题目
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import topic, TestCase


@require_http_methods(["GET", "POST"])
def batch_import_testcases(request):
    if request.method == "GET":
        # 获取所有题目用于下拉选择
        topics = topic.objects.all().values('id', 'title')
        return render(request, 'CheckObjection/batch_import_testcases.html', {'topics': topics})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            topic_id = data.get('topic_id')
            testcases_text = data.get('testcases_text')

            if not topic_id or not testcases_text:
                return JsonResponse({'success': False, 'error': '题目ID和测试案例内容不能为空'})

            # 获取题目对象
            topic_obj = get_object_or_404(topic, id=topic_id)

            # 解析测试案例文本
            testcases = parse_testcases_text(testcases_text)

            # 创建测试案例对象
            created_count = 0
            for i, testcase in enumerate(testcases):
                TestCase.objects.create(
                    titleSlug=topic_obj,
                    input_data=testcase['input'],
                    expected_output=testcase['output'],
                    order=i,
                    is_sample=testcase.get('is_sample', False),
                    score=testcase.get('score', 10)
                )
                created_count += 1
            print('创建了 %d 个测试案例' % created_count)

            return JsonResponse({
                'success': True,
                'message': f'成功导入 {created_count} 个测试案例'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


def parse_testcases_text(text):
    """
    解析测试案例文本格式
    支持多种格式：
    格式1：输入和输出用分隔符分开
    格式2：JSON格式
    """
    testcases = []

    # 尝试解析为JSON格式
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except:
        pass

    # 解析文本格式
    lines = text.strip().split('\n')
    current_testcase = {'input': '', 'output': ''}
    current_section = 'input'

    for line in lines:
        line = line.strip()

        if line.startswith('===') or line.startswith('---'):
            # 分隔符，切换到输出部分
            current_section = 'output'
        elif line.startswith('***') or line.startswith('###'):
            # 测试案例结束分隔符
            if current_testcase['input'] and current_testcase['output']:
                testcases.append(current_testcase)
            current_testcase = {'input': '', 'output': ''}
            current_section = 'input'
        else:
            # 添加到当前部分
            if current_section == 'input':
                if current_testcase['input']:
                    current_testcase['input'] += '\n' + line
                else:
                    current_testcase['input'] = line
            else:
                if current_testcase['output']:
                    current_testcase['output'] += '\n' + line
                else:
                    current_testcase['output'] = line

    # 添加最后一个测试案例
    if current_testcase['input'] and current_testcase['output']:
        testcases.append(current_testcase)

    return testcases