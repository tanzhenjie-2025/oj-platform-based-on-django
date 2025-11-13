# CheckObjectionApp/views/utils.py
"""
工具函数模块
包含验证码生成、缓存清理、批量导入等辅助功能
"""
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
import json
import re
from ..code import check_code
from ..constants import CAPTCHA_CONFIG
from ..models import topic, TestCase
from ..utils.cache_utils import SubmissionCache


def image_code(request):
    """生成图片验证码"""
    img, code_string = check_code()
    print(f"生成的验证码: {code_string}")  # 生产环境应该移除或改为日志

    # 将验证码存入session
    request.session['captcha'] = code_string
    request.session.set_expiry(CAPTCHA_CONFIG['SESSION_EXPIRY'])

    # 将图片保存到内存流中
    stream = BytesIO()
    img.save(stream, 'png')
    stream.seek(0)

    return HttpResponse(stream.getvalue(), content_type='image/png')


@login_required
def clear_my_submission_cache(request):
    """清除当前用户的提交记录缓存"""
    user_name = request.user.username
    SubmissionCache.delete_submissions(user_name)
    from django.contrib import messages
    messages.success(request, '您的提交记录缓存已清除')
    return redirect('CheckObjectionApp:my_submission_list')


@staff_member_required
def batch_import_testcases(request):
    """批量导入测试用例"""
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

            topic_obj = topic.objects.get(id=topic_id)

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
    """解析测试案例文本格式"""
    # 这里放置原有的解析逻辑
    text = text.strip()

    # 方法1: 尝试直接解析为JSON
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return validate_testcases(data)
    except json.JSONDecodeError:
        pass

    # 其他解析方法...
    return []


def validate_testcases(testcases):
    """验证测试案例数据的完整性"""
    validated = []
    for testcase in testcases:
        if not isinstance(testcase, dict):
            continue
        if 'input' not in testcase or 'output' not in testcase:
            continue
        validated.append({
            'input': str(testcase['input']),
            'output': str(testcase['output']),
            'is_sample': testcase.get('is_sample', False),
            'score': testcase.get('score', 10)
        })
    return validated


def extract_json_array(text):
    """从混合文本中提取JSON数组部分"""
    # 这里放置原有的提取逻辑
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
                return ''.join(json_chars)
        elif start_index != -1:
            json_chars.append(char)
    return None