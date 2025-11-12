from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import render,redirect,reverse
import string
from django.http.response import JsonResponse, HttpResponseForbidden
# Create your views here.
import random
from django.core.mail import send_mail
from django.views import View
from django.views.decorators.http import require_http_methods,require_POST,require_GET

from django.contrib.auth import get_user_model, login, logout, authenticate
from django.urls.base import reverse_lazy
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView

from CheckObjection import settings
from CheckObjection.settings import DB_QUERY_KEY, CACHE_KEY_HIT
from mycelery.sms.tasks import submit_code_task
from . import constants
from .code import check_code
from .models import answer, Contest, ContestParticipant, ContestSubmission, ContestTopic
from .forms import LoginForm, RegisterForm

from CheckObjectionApp.serializers import topicSerializer
from CheckObjectionApp.serializers import topicModelSerializer

User = get_user_model()
from .models import topic
from rest_framework import mixins
from rest_framework.generics import GenericAPIView

from .constants import CACHE_TIMEOUT, COLOR_CODES, JUDGE_CONFIG, CAPTCHA_CONFIG, DEFAULT_VALUES

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
@login_required(login_url=reverse_lazy(settings.LOGIN_URL))
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
@login_required(login_url=reverse_lazy(settings.LOGIN_URL))
def show(request):

    if not request.user.is_staff:
        return redirect("CheckObjectionApp:CheckObjection_noPower")

    answers = answer.objects.all()
    topics = topic.objects.all()
    return render(request,'CheckObjection/CheckObjection_show.html',context={'answers':answers,'topics':topics})


# 以下为登录模块
from django.http import HttpResponse


@require_http_methods(['GET', 'POST'])
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
        return render(request, 'CheckObjection/changeName.html', context={'user': user})


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
        return render(request, 'CheckObjection/changeName.html',
                      context={'user': user, 'user_info': user_info})


# 以下是搜索模块
from django.views.decorators.http import require_GET

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
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
# 直接导入任务函数，而不是Celery任务


# 日常提交判题
@method_decorator(csrf_exempt, name='dispatch')
class JudgeCodeView(View):
    def post(self, request):
        """
        判题接口 - 改为同步处理
        """
        try:
            user_id = request.user.id
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
                'user_id': user_id,
                'source_code': source_code,
                'language_id': language_id,
                'topic_id': topic_id,
                'user_name': user_name,
                'notes': notes,
                'submission_id': submission_id,
                'is_test': is_test
            }



            # 正式提交 - 直接同步调用
            task_result = submit_code_task(submission_data)
            # 直接返回结果，不再返回任务ID
            return JsonResponse({
                "success": True,
                "message": "代码处理完成",
                "submission_id": submission_id,
                "status": "COMPLETED",
                "result": task_result  # 包含详细结果
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"处理请求时出错: {str(e)}"
            })

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

# 管理员视图
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

from django.contrib.admin.views.decorators import staff_member_required

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
    # 调用pillow函数，生成图片
    img, code_string = check_code()
    print(code_string)

    # 将验证码存入session
    request.session['captcha'] = code_string
    # 给Session设置60s超时
    request.session.set_expiry(CAPTCHA_CONFIG['SESSION_EXPIRY'])

    # 将图片保存到内存流中
    stream = BytesIO()
    img.save(stream, 'png')

    # 将流的位置重置到开头
    stream.seek(0)
    # 返回图片响应，指定内容类型为image/png
    return HttpResponse(stream.getvalue(), content_type='image/png')

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

# 比赛提交界面 todo 2 加载时要有比赛资料 还要改造比赛提交界面 传递比赛 id
@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy(settings.LOGIN_URL))
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

# 比赛提交判题
@method_decorator(csrf_exempt, name='dispatch')
class JudgeContestCodeView(View):
    def post(self, request,contest_id):
        """
        判题接口 - 同步处理
        """
        try:
            user_id = request.user.id

            data = json.loads(request.body)
            source_code = data.get('source_code', '')
            language_id = data.get('language_id', JUDGE_CONFIG['DEFAULT_LANGUAGE_ID'])
            topic_id = data.get('topic_id', '')
            user_name = data.get('user_name', '')
            notes = data.get('notes', '')
            is_test = data.get('is_test', False)
            # 生成唯一的提交ID
            submission_id = str(uuid.uuid4())
            submission_data = {
                'user_id': user_id,
                'contest_id': contest_id,
                'source_code': source_code,
                'language_id': language_id,
                'topic_id': topic_id,
                'user_name': user_name,
                'notes': notes,
                'submission_id': submission_id,
                'is_test': is_test
            }


             # 正式提交 - 直接同步调用
            task_result = submit_code_task(submission_data)
            # 直接返回结果
            return JsonResponse({
                "success": True,
                "message": "代码处理完成",
                "submission_id": submission_id,
                "status": "COMPLETED",
                "result": task_result  # 包含详细结果
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"处理请求时出错: {str(e)}"
            })

# 以下为比赛代码提交记录展示
@login_required
def contest_submission_list(request):
    """显示全部比赛的所有提交记录（管理员视图）"""

    # 检查用户权限，如果是管理员则显示所有提交
    if request.user.is_staff:
        contest_submissions = ContestSubmission.objects.all().select_related(
            'contest',
            'submission',  # 关联到Submission模型
            'submission__topic',
            'participant__user'
        ).order_by('-submitted_at')
    else:
        # 普通用户只能看到自己的提交
        contest_submissions = ContestSubmission.objects.filter(
            participant__user=request.user
        ).select_related(
            'contest',
            'submission',  # 关联到Submission模型
            'submission__topic',
            'participant__user'  # 修正：应该是participant__user而不是participant
        ).order_by('-submitted_at')

    # 准备前端需要的数据
    submission_data = []
    for contest_sub in contest_submissions:
        # 获取关联的Submission对象
        submission = contest_sub.submission

        # 构建前端需要的数据结构
        submission_info = {
            # ContestSubmission信息
            'contest_submission_id': contest_sub.id,
            'submitted_at': contest_sub.submitted_at,

            # Submission信息
            'id': submission.id,
            'user_name': submission.user_name,
            'topic_id': submission.topic.id if submission.topic else None,
            'topic': submission.topic,  # 直接传递topic对象
            'language_id': submission.language_id,
            'status': submission.status,
            'overall_result': submission.overall_result,
            'created_at': submission.created_at,
            'updated_at': submission.updated_at,

            # 其他相关信息
            'contest': contest_sub.contest,
            'participant': contest_sub.participant,
        }
        submission_data.append(submission_info)


    context = {
        'submissions': submission_data,  # 传递处理后的数据
        'page_title': '比赛提交记录',
        'from': 'contest_submission_list',
    }
    return render(request, 'CheckObjection/submission_list.html', context)


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
    return render(request, 'CheckObjection/submission_list.html', context)

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
    return render(request, 'CheckObjection/submission_list.html', context)


@login_required
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
        return render(request, 'CheckObjection/submission_list.html', context)

    except Contest.DoesNotExist:
        return render(request, 'CheckObjection/CheckObjection_noPower.html', {'error_message': '比赛不存在'})
    except ContestTopic.DoesNotExist:
        return render(request, 'CheckObjection/CheckObjection_noPower.html', {'error_message': '该题目不在比赛中或不存在'})


# 批量导入题目
import re
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import topic, TestCase


@require_http_methods(["GET", "POST"])
def batch_import_testcases(request):
    if request.method == "GET":
        topics = topic.objects.all().values('id', 'title')
        return render(request, 'CheckObjection/batch_import_testcases.html', {'topics': topics})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            topic_id = data.get('topic_id')
            testcases_text = data.get('testcases_text')

            if not topic_id or not testcases_text:
                return JsonResponse({'success': False, 'error': '题目ID和测试案例内容不能为空'})

            topic_obj = get_object_or_404(topic, id=topic_id)

            # 解析测试案例文本
            testcases = parse_testcases_text(testcases_text)
            if not testcases:
                return JsonResponse({'success': False, 'error': '未找到有效的测试案例格式'})

            # 批量创建测试案例
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

            return JsonResponse({
                'success': True,
                'message': f'成功导入 {created_count} 个测试案例',
                'count': created_count
            })

        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': f'JSON解析错误: {str(e)}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

def parse_testcases_text(text):
    """
    智能解析测试案例文本格式
    支持：
    1. 纯JSON数组格式
    2. 包含JSON数组的混合文本（自动提取JSON部分）
    3. 传统的分隔符格式
    """
    text = text.strip()

    # 方法1: 尝试直接解析为JSON
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return validate_testcases(data)
    except json.JSONDecodeError:
        pass

    # 方法2: 尝试从文本中提取JSON数组
    json_match = extract_json_array(text)
    if json_match:
        try:
            data = json.loads(json_match)
            if isinstance(data, list):
                return validate_testcases(data)
        except json.JSONDecodeError:
            pass

    # 方法3: 传统的分隔符格式
    return parse_legacy_format(text)


def extract_json_array(text):
    """
    从混合文本中提取JSON数组部分
    """
    # 查找最外层的 JSON 数组
    bracket_count = 0
    start_index = -1
    json_chars = []

    for i, char in enumerate(text):
        if char == '[':
            if bracket_count == 0:
                start_index = i
            bracket_count += 1
            json_chars.append(char)
        elif char == ']':
            bracket_count -= 1
            json_chars.append(char)
            if bracket_count == 0 and start_index != -1:
                # 找到完整的JSON数组
                return ''.join(json_chars)
        elif start_index != -1:
            json_chars.append(char)

    return None


def parse_legacy_format(text):
    """
    解析传统的分隔符格式
    """
    testcases = []
    lines = text.strip().split('\n')
    current_testcase = {'input': '', 'output': '', 'is_sample': False, 'score': 10}
    current_section = 'input'
    section_found = False

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # 检测分隔符
        if re.match(r'^={3,}$|^-{3,}$', line):  # === 或 ---
            current_section = 'output'
            section_found = True
        elif re.match(r'^\*{3,}$|^#{3,}$', line):  # *** 或 ###
            # 结束当前测试案例
            if current_testcase['input'] and current_testcase['output']:
                testcases.append(current_testcase)
            current_testcase = {'input': '', 'output': '', 'is_sample': False, 'score': 10}
            current_section = 'input'
            section_found = False
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

    # 添加最后一个测试案例（如果没有明确的分隔符结束）
    if current_testcase['input'] and current_testcase['output']:
        testcases.append(current_testcase)
    elif current_testcase['input'] and not section_found:
        # 如果只有输入没有输出分隔符，尝试智能分割
        testcases = parse_smart_format(text)

    return testcases


def parse_smart_format(text):
    """
    智能解析格式：自动检测输入输出模式
    """
    testcases = []
    blocks = re.split(r'\n\s*\*{3,}\s*\n', text)  # 按 *** 分割测试案例

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # 尝试按 === 分割输入输出
        parts = re.split(r'\n\s*={3,}\s*\n', block)
        if len(parts) >= 2:
            testcase = {
                'input': parts[0].strip(),
                'output': parts[1].strip(),
                'is_sample': False,
                'score': 10
            }
            testcases.append(testcase)

    return testcases


def validate_testcases(testcases):
    """
    验证测试案例数据的完整性
    """
    validated = []
    for i, testcase in enumerate(testcases):
        if not isinstance(testcase, dict):
            continue

        # 确保必需的字段存在
        if 'input' not in testcase or 'output' not in testcase:
            continue

        validated.append({
            'input': str(testcase['input']),
            'output': str(testcase['output']),
            'is_sample': testcase.get('is_sample', False),
            'score': testcase.get('score', 10)
        })

    return validated

# 点击报名参加比赛
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Contest, ContestParticipant


# 比赛报名视图
@login_required  # 确保用户已登录
def contest_register(request, contest_id):
    # 获取比赛对象，不存在则返回404
    contest = get_object_or_404(Contest, id=contest_id)

    # GET请求：显示报名页面
    if request.method == 'GET':
        return render(request, 'CheckObjection/contest/contest_register.html', {
            'contest': contest
        })

    # POST请求：处理报名逻辑
    if request.method == 'POST':
        # 1. 检查比赛是否允许报名
        if not contest.allow_register:
            messages.error(request, "该比赛不允许报名")
            return redirect('CheckObjectionApp:contest_detail', pk=contest_id)  # 假设存在比赛详情页路由

        # 2. 检查比赛状态（已结束的比赛不能报名）
        if contest.status == 'ended':
            messages.error(request, "比赛已结束，无法报名")
            return redirect('CheckObjectionApp:contest_detail', pk=contest_id)

        # 3. 检查是否已报名
        if ContestParticipant.objects.filter(contest=contest, user=request.user).exists():
            messages.warning(request, "您已报名该比赛，无需重复报名")
            return redirect('CheckObjectionApp:contest_detail', pk=contest_id)

        # 4. 验证比赛密码（如果设置了密码）
        if contest.password:
            input_password = request.POST.get('password', '').strip()
            if input_password != contest.password:
                messages.error(request, "比赛密码错误")
                return render(request, 'CheckObjection/contest/contest_register.html', {
                    'contest': contest
                })

        # 5. 创建报名记录
        ContestParticipant.objects.create(
            contest=contest,
            user=request.user
        )

        messages.success(request, "报名成功！请准时参加比赛")
        return redirect('CheckObjectionApp:contest_detail', pk=contest_id)  # 跳转到比赛详情页


# 补充：建议新增比赛详情页视图（用于跳转）
# def contest_detail(request, contest_id):
#     contest = get_object_or_404(Contest, id=contest_id)
#     # 可以添加更多比赛详情相关逻辑
#     return render(request, 'CheckObjection/contest/contest_detail.html', {
#         'contest': contest
#     })


from django.db.models import Count, Q, Case, When, IntegerField
from django.utils import timezone
from django.shortcuts import get_object_or_404


def contest_detail(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    # 检查用户是否已报名
    is_registered = ContestParticipant.objects.filter(
        contest=contest,
        user=request.user
    ).exists()

    # 获取比赛题目
    contest_topics = ContestTopic.objects.filter(contest=contest).select_related('topic')

    # 获取当前用户在该比赛中的提交统计
    if request.user.is_authenticated and is_registered:
        participant = ContestParticipant.objects.get(contest=contest, user=request.user)

        # 获取已解决的题目ID
        solved_submissions = ContestSubmission.objects.filter(
            participant=participant,
            submission__status='Accepted'
        ).values_list('submission__topic_id', flat=True).distinct()

        solved_problems = list(solved_submissions)

        # 计算得分情况
        problem_scores = []
        total_score = 0
        contest_total_score = 0

        for contest_topic in contest_topics:
            # 获取该题目的最佳提交（分数最高）
            best_submission = ContestSubmission.objects.filter(
                participant=participant,
                submission__topic=contest_topic.topic,
                submission__status='Accepted'
            ).order_by('-submission__overall_result').first()

            if best_submission:
                score = contest_topic.score
                status = f"{score}分"
                color = "#4caf50"  # 绿色
            else:
                # 检查是否有提交但未通过
                has_attempts = ContestSubmission.objects.filter(
                    participant=participant,
                    submission__topic=contest_topic.topic
                ).exists()

                if has_attempts:
                    score = 0
                    status = "0分"
                    color = "#f44336"  # 红色
                else:
                    score = 0
                    status = "未提交"
                    color = "#757575"  # 灰色

            total_score += score
            contest_total_score += contest_topic.score

            problem_scores.append({
                'title': f"{contest_topic.order}. {contest_topic.topic.title}",
                'score': score,
                'score_status': status,
                'color': color
            })

        # 计算提交情况
        problem_submissions_stats = []
        total_ac_count = 0

        for contest_topic in contest_topics:
            # 统计该题目的提交情况
            submissions_count = ContestSubmission.objects.filter(
                participant=participant,
                submission__topic=contest_topic.topic
            ).count()

            ac_count = ContestSubmission.objects.filter(
                participant=participant,
                submission__topic=contest_topic.topic,
                submission__status='Accepted'
            ).count()

            if ac_count > 0:
                status = f"{ac_count}/{submissions_count}"
                color = "#4caf50"  # 绿色
                total_ac_count += 1
            elif submissions_count > 0:
                status = f"0/{submissions_count}"
                color = "#f44336"  # 红色
            else:
                status = "未提交"
                color = "#757575"  # 灰色

            problem_submissions_stats.append({
                'title': f"{contest_topic.order}. {contest_topic.topic.title}",
                'submissions_count': submissions_count,
                'ac_count': ac_count,
                'submission_status': status,
                'color': color
            })

        # 计算AC率
        ac_rate = round((total_ac_count / len(contest_topics)) * 100, 2) if contest_topics else 0

        # 获取排名数据（前4名）
        rankings = get_contest_rankings(contest, limit=4)

    else:
        # 用户未登录或未报名，显示空数据
        solved_problems = []
        problem_scores = []
        problem_submissions_stats = []
        total_score = 0
        contest_total_score = sum(ct.score for ct in contest_topics)
        ac_rate = 0
        total_ac_count = 0
        rankings = []

    context = {
        'contest': contest,
        'contest_topics': contest_topics,
        'is_registered': is_registered,
        'solved_problems': solved_problems,
        'problem_scores': problem_scores,
        'total_score': total_score,
        'contest_total_score': contest_total_score,
        'problem_submissions_stats': problem_submissions_stats,
        'ac_rate': ac_rate,
        'total_ac_count': total_ac_count,
        'rankings': rankings,
    }

    return render(request, 'CheckObjection/contest/contest_detail.html', context)


def get_contest_rankings(contest, limit=None):
    """获取比赛排名数据"""
    participants = ContestParticipant.objects.filter(contest=contest, is_disqualified=False)

    rankings = []
    for participant in participants:
        # 计算每个参与者的总得分和AC数量
        total_score = 0
        ac_count = 0

        # 获取参与者的所有AC提交（按题目分组，取每个题目的最佳提交）
        for contest_topic in contest.contest_topics.all():
            best_submission = ContestSubmission.objects.filter(
                participant=participant,
                submission__topic=contest_topic.topic,
                submission__status='Accepted'
            ).order_by('-submitted_at').first()

            if best_submission:
                total_score += contest_topic.score
                ac_count += 1

        rankings.append({
            'user_name': participant.user.username,
            'total_score': total_score,
            'ac_count': ac_count,
            'participant': participant
        })

    # 按得分和AC数量排序
    rankings.sort(key=lambda x: (-x['total_score'], -x['ac_count']))

    # 添加排名
    for i, rank in enumerate(rankings):
        rank['rank'] = i + 1

    return rankings[:limit] if limit else rankings


# def submission_detail(request, submission_id):
#     """提交详情页面"""
#     submission = get_object_or_404(Submission, id=submission_id)
#
#     # 检查用户权限（只能查看自己的提交或管理员）
#     if not request.user.is_staff and submission.user != request.user:
#         return HttpResponseForbidden("无权查看此提交")
#
#     context = {
#         'submission': submission,
#         'page_title': f"提交详情 - {submission.id}",
#     }

    # return render(request, 'CheckObjection/submission_detail.html', context)


# def contest_submission_list(request, contest_id, user_name=None):
#     """比赛提交列表"""
#     contest = get_object_or_404(Contest, id=contest_id)
#
#     # 如果指定了用户名，则显示该用户的提交，否则显示当前用户的提交
#     if user_name and request.user.is_staff:
#         target_user = get_object_or_404(User, username=user_name)
#     else:
#         target_user = request.user
#
#     # 获取参与者和提交记录
#     participant = get_object_or_404(ContestParticipant, contest=contest, user=target_user)
#     submissions = ContestSubmission.objects.filter(
#         participant=participant
#     ).select_related('submission', 'submission__topic').order_by('-submitted_at')
#
#     context = {
#         'contest': contest,
#         'submissions': submissions,
#         'target_user': target_user,
#     }
#
#     return render(request, 'CheckObjection/submission_list.html', context)


def global_ranking(request):
    """全局排名页面"""
    # 获取所有用户的AC题目数量统计
    from django.db.models import Count

    user_stats = Submission.objects.filter(
        status='Accepted'
    ).values(
        'user_name'
    ).annotate(
        solved_count=Count('topic', distinct=True)
    ).order_by('-solved_count')

    # 添加排名
    rankings = []
    for i, stat in enumerate(user_stats):
        rankings.append({
            'rank': i + 1,
            'user_name': stat['user_name'],
            'solved_count': stat['solved_count']
        })

    context = {
        'rankings': rankings,
        'total_users': len(rankings)
    }

    return render(request, 'CheckObjection/CheckObjection_ranking.html', context)


def contest_ranking(request, contest_id):
    """比赛排名页面"""
    contest = get_object_or_404(Contest, id=contest_id)
    rankings = get_contest_rankings(contest)  # 获取所有排名

    context = {
        'contest': contest,
        'rankings': rankings,
        'total_users': len(rankings)
    }

    return render(request, 'CheckObjection/CheckObjection_ranking.html', context)

# 以下是实现比赛排行的代码
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Case, When, IntegerField, F, Q
from django.db import models
from .models import Contest, ContestParticipant, ContestSubmission, Submission


def contest_rank_list(request):
    """
    展示所有比赛列表
    """
    contests = Contest.objects.all().order_by('-start_time')

    # 为每个比赛添加统计信息
    for contest in contests:
        contest.participant_count = contest.participants.count()
        contest.topic_count = contest.contest_topics.count()

    context = {
        'contests': contests
    }
    return render(request, 'CheckObjection/contest/rank/rank_list.html', context)


def contest_rank_detail(request, contest_id):
    """
    展示具体比赛的排名详情 - 生产版本
    """
    contest = get_object_or_404(Contest, id=contest_id)

    # 获取比赛的所有题目
    contest_topics = contest.contest_topics.select_related('topic').order_by('order')

    # 获取所有参赛者
    participants = contest.participants.filter(is_disqualified=False).select_related('user')

    # 构建排名数据
    rank_data = []

    for participant in participants:
        user = participant.user

        # 获取该用户在比赛中的所有提交
        contest_submissions = ContestSubmission.objects.filter(
            contest=contest,
            participant=participant
        ).select_related('submission', 'submission__topic').order_by('submitted_at')

        # 统计每个题目的最佳提交
        topic_results = {}
        total_accepted = 0
        total_penalty = 0

        # 按题目分组处理提交
        for contest_topic in contest_topics:
            topic = contest_topic.topic

            # 获取该题目的所有提交
            topic_submissions = [
                cs for cs in contest_submissions
                if cs.submission.topic_id == topic.id
            ]

            first_ac_time = None
            wrong_count = 0
            is_accepted = False
            penalty_minutes = 0

            # 遍历该题目的所有提交
            for cs in topic_submissions:
                submission = cs.submission
                # 关键修改：使用 overall_result 字段来判断是否通过
                is_ac = submission.overall_result == 'Accepted'

                if is_ac and not is_accepted:
                    # 第一次AC
                    is_accepted = True
                    first_ac_time = cs.submitted_at

                    # 计算该题目的罚时
                    if first_ac_time and contest.start_time:
                        time_diff = first_ac_time - contest.start_time
                        penalty_minutes = time_diff.total_seconds() / 60
                elif not is_ac and not is_accepted:
                    # 在第一次AC之前的错误提交
                    wrong_count += 1

            # 存储该题目的结果
            topic_results[topic.id] = {
                'is_accepted': is_accepted,
                'wrong_count': wrong_count,
                'first_ac_time': first_ac_time,
                'topic_order': contest_topic.order
            }

            # 如果该题目通过，累加通过数和罚时
            if is_accepted:
                total_accepted += 1
                topic_total_penalty = penalty_minutes + (wrong_count * contest.penalty_time)
                total_penalty += topic_total_penalty

        rank_data.append({
            'user': user,
            'username': user.username,
            'total_accepted': total_accepted,
            'total_penalty': total_penalty,
            'topic_results': topic_results,
            'participant': participant
        })

    # 按完成题目数量降序，罚时升序排序
    rank_data.sort(key=lambda x: (-x['total_accepted'], x['total_penalty']))

    # 添加排名（处理并列排名）
    current_rank = 1
    for i, data in enumerate(rank_data):
        if i > 0 and (rank_data[i - 1]['total_accepted'] == data['total_accepted'] and
                      rank_data[i - 1]['total_penalty'] == data['total_penalty']):
            # 与前一名成绩相同，则排名相同
            data['rank'] = rank_data[i - 1]['rank']
        else:
            data['rank'] = current_rank
        current_rank += 1

    context = {
        'contest': contest,
        'contest_topics': contest_topics,
        'rank_data': rank_data,
    }

    return render(request, 'CheckObjection/contest/rank/rank_detail.html', context)

# 展示用户模块，用于管理员查询提交
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from .models import UserProfile

# 管理员查询视图
@staff_member_required
def user_list(request):
    """展示所有用户的列表视图（仅管理员可访问）"""
    # 获取所有用户
    users = User.objects.all().order_by('-date_joined')  # 按注册时间倒序

    # 处理用户数据，关联用户附加信息
    user_list = []

    for user in users:
        try:
            # 获取用户的附加信息
            profile = UserProfile.objects.get(user_id=user.id)
            finish_count = profile.finish
        except UserProfile.DoesNotExist:
            # 如果用户没有附加信息，默认完成数为0
            finish_count = 0

        user_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined,
            'finish_count': finish_count
        })
    return render(request, 'CheckObjection/user_list.html', {'users': user_list})

# 管理员视图
# 查询用户参加过的所有比赛
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Count, Case, When, IntegerField, Subquery, OuterRef
from django.utils import timezone
from .models import Contest, ContestParticipant, User, ContestSubmission


@login_required
def user_contests(request, user_name):
    """显示指定用户参加过的所有比赛"""
    try:
        # 获取用户对象
        user = get_object_or_404(User, username=user_name)

        # 缓存键
        cache_key = f"user_{user_name}_contests"

        # 尝试从缓存获取数据
        contests_data = cache.get(cache_key)

        if contests_data is None:
            # 查询用户参加的所有比赛（未被取消资格的）
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

                # 计算通过率，避免除零错误
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

            # 设置缓存（10分钟）
            cache.set(cache_key, contests_list, 600)
            contests_data = contests_list

        print("Contests data:", contests_data)  # 调试信息

        context = {
            'contests_data': contests_data,
            'target_user': user,
            'page_title': f'{user_name} 参加的比赛',
            'current_time': timezone.now()
        }

        return render(request, 'CheckObjection/user_contests.html', context)

    except Exception as e:
        print(f"Error in user_contests view: {e}")
        # 返回一个简单的错误页面或重定向
        from django.http import HttpResponseServerError
        return HttpResponseServerError(f"服务器错误: {e}")


@login_required
def my_contests(request):
    """显示当前用户自己参加过的所有比赛"""
    return user_contests(request, request.user.username)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from .models import Contest, ContestSubmission, Submission, ContestParticipant


@login_required
@staff_member_required
def contest_user_submissions(request, contest_id, user_name):
    """显示指定用户在特定比赛中的提交记录"""
    contest = get_object_or_404(Contest, id=contest_id)

    # 缓存键
    cache_key = f"contest_{contest_id}_user_{user_name}_submissions"

    # 尝试从缓存获取数据
    submissions = cache.get(cache_key)

    if submissions is None:
        # 查询比赛提交记录，预加载相关对象
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

        # 设置缓存（5分钟）
        cache.set(cache_key, submissions_list, 300)
        submissions = submissions_list


    context = {
        'contest': contest,
        'submissions': submissions,
        'target_user_name': user_name,
        'page_title': f'{user_name} - {contest.title} 提交记录'
    }
    print(context)
    return render(request, 'CheckObjection/contest_submission_list.html', context)


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
        return render(request, 'CheckObjection/contest_submission_list.html', context)

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

        # 设置缓存（5分钟）
        cache.set(cache_key, submissions_list, 300)
        submissions = submissions_list

    context = {
        'contest': contest,
        'submissions': submissions,
        'target_user_name': user_name,
        'page_title': f'我的 {contest.title} 提交记录',
        'is_my_submissions': True
    }
    return render(request, 'CheckObjection/contest_submission_list.html', context)