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

def changeName( request):
    """修改用户资料"""
    if request.method == "POST":
        username = request.POST.get('username')
        user = request.user
        user.username = username
        user.save()
        return redirect(reverse("CheckObjectionApp:CheckObjectionApp_index"))
    return render(request,'CheckObjection/CheckObjection_changeName.html')
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
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views import View
from django.utils.decorators import method_decorator
from .models import TestCase, topic
from .utils.judge0_service import Judge0Service

# 添加Redis缓存导入
from django.core.cache import cache
from django.conf import settings


@method_decorator(csrf_exempt, name='dispatch')
class JudgeCodeView(View):
    def post(self, request):
        """
        判题接口 - 接收前端提交的代码并进行判题
        """
        try:
            import json
            data = json.loads(request.body)

            source_code = data.get('source_code', '')
            language_id = data.get('language_id', 71)  # 默认Python
            topic_id = data.get('topic_id', '')
            user_name = data.get('user_name', '')
            notes = data.get('notes', '')

            # 根据题目ID获取对应的测试用例（使用缓存）
            test_cases = self._get_test_cases_by_topic_with_cache(topic_id)

            judge_service = Judge0Service()
            results = []

            # 对每个测试用例进行判题
            for i, test_case in enumerate(test_cases):
                result = judge_service.submit_code(
                    source_code=source_code,
                    language_id=language_id,
                    stdin=test_case["stdin"],
                    expected_output=test_case["expected_output"]
                )

                # 构建详细的测试结果，包含输入、期望输出和实际输出
                detailed_result = {
                    "test_case": i + 1,
                    "input_data": test_case["stdin"],  # 测试用例输入
                    "expected_output": test_case["expected_output"],  # 期望输出
                    "user_output": result.get("stdout", ""),  # 用户代码的实际输出
                    "result": result,
                    "is_sample": test_case.get("is_sample", False),  # 是否是样例测试
                    "score": test_case.get("score", 0)  # 该测试用例分值
                }
                results.append(detailed_result)

            # 计算总体结果
            overall_result = self._calculate_overall_result(results)

            return JsonResponse({
                "success": True,
                "overall_result": overall_result,
                "results": results,
                "user_name": user_name,
                "topic_id": topic_id,
                "notes": notes,
                "source_code": source_code,  # 返回提交的代码用于参考
                "language_id": language_id
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"处理请求时出错: {str(e)}"
            })

    def _get_test_cases_by_topic_with_cache(self, topic_id):
        """
        根据题目ID从Redis缓存或数据库获取测试用例
        """
        cache_key = f"test_cases_topic_{topic_id}"

        # 尝试从缓存获取测试用例
        cached_test_cases = cache.get(cache_key)

        if cached_test_cases is not None:
            print(f"从缓存获取测试用例 topic_id: {topic_id}")
            return cached_test_cases

        print(f"缓存未命中，从数据库获取测试用例 topic_id: {topic_id}")

        # 缓存未命中，从数据库获取
        test_cases = self._get_test_cases_from_db(topic_id)

        # 将结果存入缓存，设置过期时间
        if test_cases:
            cache.set(cache_key, test_cases, timeout=getattr(settings, 'CACHE_TTL', 900))
            print(f"测试用例已缓存 topic_id: {topic_id}")

        return test_cases

    def _get_test_cases_from_db(self, topic_id):
        """
        从数据库获取测试用例（原始数据库查询方法）
        """
        try:
            # 从数据库获取该题目的所有测试用例，按order字段排序
            test_cases = TestCase.objects.filter(
                titleSlug_id=topic_id
            ).order_by('order')

            # 将数据库记录转换为需要的格式
            formatted_test_cases = []
            for test_case in test_cases:
                formatted_test_cases.append({
                    "stdin": test_case.input_data,
                    "expected_output": test_case.expected_output,
                    "is_sample": test_case.is_sample,
                    "score": test_case.score
                })

            return formatted_test_cases

        except Exception as e:
            # 如果出现异常，返回空列表或默认测试用例
            print(f"获取测试用例时出错: {str(e)}")
            return [{
                "stdin": "",
                "expected_output": "",
                "is_sample": False,
                "score": 0
            }]

    def _get_test_cases_by_topic(self, topic_id):
        """
        保持向后兼容的原有方法（现在调用带缓存的方法）
        """
        return self._get_test_cases_by_topic_with_cache(topic_id)

    def _calculate_overall_result(self, results):
        """
        计算总体判题结果
        """
        if not results:
            return "No Test Cases"

        # 检查所有测试用例是否都通过
        all_passed = all(
            result["result"].get("status") == "Accepted"
            for result in results
        )

        if all_passed:
            return "Accepted"
        else:
            # 返回第一个失败的结果状态
            for result in results:
                if result["result"].get("status") != "Accepted":
                    return result["result"].get("status", "Wrong Answer")
            return "Wrong Answer"

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





