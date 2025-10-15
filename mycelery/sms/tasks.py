# celery的任务必须写在tasks.py的文件中，别的文件名称不识别！！！
from CheckObjectionApp.models import TestCase
from CheckObjectionApp.utils.judge0_service import Judge0Service
from mycelery.main import app
import time
import logging
logging.getLogger("django")
@app.task
#name表示设置任务的名称，如果不填写，则默认使用函数名做为任务名
def send_sms(mobile):
# "发送短信”
    print(f"向手机号%s发送短信成功！"%mobile)
    time.sleep(5)
    return "send_sms OK"


@app.task#name表示设置任务的名称，如果不填写，则默认使用函数名做为任务名
def send_sms2(mobile):
    print("向手机号%s发送短信成功！"%mobile)
    time.sleep(5)
    return "send_sms2 OK"


from celery import shared_task
import time
import json
import requests
# from .models import TestCase
from django.core.cache import cache
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def judge_submission_task(self, submission_data):
    """
    异步判题任务
    """
    try:
        source_code = submission_data['source_code']
        language_id = submission_data['language_id']
        topic_id = submission_data['topic_id']

        # 获取测试用例
        test_cases = get_test_cases_by_topic_with_cache(topic_id)

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

            # 更新任务状态
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': len(test_cases),
                    'status': f'正在评测测试用例 {i + 1}/{len(test_cases)}'
                }
            )

            detailed_result = {
                "test_case": i + 1,
                "input_data": test_case["stdin"],
                "expected_output": test_case["expected_output"],
                "user_output": result.get("stdout", ""),
                "result": result,
                "is_sample": test_case.get("is_sample", False),
                "score": test_case.get("score", 0)
            }
            results.append(detailed_result)

        # 计算总体结果
        overall_result = calculate_overall_result(results)

        return {
            'status': 'SUCCESS',
            'overall_result': overall_result,
            'results': results,
            'user_name': submission_data.get('user_name', ''),
            'topic_id': topic_id,
            'notes': submission_data.get('notes', ''),
            'source_code': source_code,
            'language_id': language_id
        }

    except Exception as e:
        # 重试逻辑
        self.retry(countdown=2 ** self.request.retries, exc=e)


def get_test_cases_by_topic_with_cache(topic_id):
    """
    根据题目ID从Redis缓存或数据库获取测试用例
    """
    cache_key = f"test_cases_topic_{topic_id}"
    cached_test_cases = cache.get(cache_key)

    if cached_test_cases is not None:
        return cached_test_cases

    # 缓存未命中，从数据库获取
    test_cases = get_test_cases_from_db(topic_id)

    # 将结果存入缓存
    if test_cases:
        cache.set(cache_key, test_cases, timeout=getattr(settings, 'CACHE_TTL', 900))

    return test_cases


def get_test_cases_from_db(topic_id):
    """
    从数据库获取测试用例
    """
    try:
        test_cases = TestCase.objects.filter(
            titleSlug_id=topic_id
        ).order_by('order')

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
        print(f"获取测试用例时出错: {str(e)}")
        return [{
            "stdin": "",
            "expected_output": "",
            "is_sample": False,
            "score": 0
        }]


def calculate_overall_result(results):
    """
    计算总体判题结果
    """
    if not results:
        return "No Test Cases"

    all_passed = all(
        result["result"].get("status") == "Accepted"
        for result in results
    )

    if all_passed:
        return "Accepted"
    else:
        for result in results:
            if result["result"].get("status") != "Accepted":
                return result["result"].get("status", "Wrong Answer")
        return "Wrong Answer"