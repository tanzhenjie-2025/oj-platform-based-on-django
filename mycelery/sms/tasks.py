# celery的任务必须写在tasks.py的文件中，别的文件名称不识别！！！
from CheckObjectionApp.models import TestCase, topic
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


import json
import time
import requests
from celery import shared_task
from django.core.cache import cache
from CheckObjectionApp.models import TestCase
from CheckObjectionApp.utils.judge0_service import Judge0Service


@shared_task(bind=True, max_retries=3)
def submit_code_task(self, submission_data):
    """
    异步提交代码到Judge0进行判题
    """
    try:
        source_code = submission_data.get('source_code', '')
        language_id = submission_data.get('language_id', 71)
        topic_id = submission_data.get('topic_id', '')
        user_name = submission_data.get('user_name', '')
        submission_id = submission_data.get('submission_id', '')
        notes = submission_data.get('notes', '')

        # 根据题目ID获取测试用例（使用缓存）
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

            # 构建详细的测试结果
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

        # 保存提交结果到数据库
        save_submission_result(
            submission_id=submission_id,
            user_name=user_name,
            topic_id=topic_id,
            source_code=source_code,
            language_id=language_id,
            results=results,
            notes=notes,
            overall_result=overall_result,
        )

        # 返回结果
        return {
            "success": True,
            "overall_result": overall_result,
            "results": results,
            "user_name": user_name,
            "topic_id": topic_id,
            "submission_id": submission_id,
            "source_code": source_code,
            "language_id": language_id
        }

    except Exception as e:
        # 如果发生异常，重试
        raise self.retry(countdown=2 ** self.request.retries, exc=e)


def save_submission_result(submission_id, user_name, topic_id, source_code,
                           language_id, results, overall_result, notes):
    """
    保存提交结果到数据库
    """
    from CheckObjectionApp.models import Submission
    try:
        submission = Submission.objects.create(
            id=submission_id,
            user_name=user_name,
            topic_id=topic_id,
            source_code=source_code,
            language_id=language_id,
            results=results,
            overall_result=overall_result,
            notes=notes,
            status='completed'
        )
        return submission
    except Exception as e:
        print(f"保存提交结果失败: {str(e)}")
        return None

@shared_task
def process_test_run(submission_data):
    """
    处理测试运行（快速返回，不保存结果）
    """
    try:
        source_code = submission_data.get('source_code', '')
        language_id = submission_data.get('language_id', 71)
        topic_id = submission_data.get('topic_id', '')

        # 只获取样例测试用例
        test_cases = get_sample_test_cases(topic_id)

        judge_service = Judge0Service()
        results = []

        # 对每个样例测试用例进行判题
        for i, test_case in enumerate(test_cases):
            result = judge_service.submit_code(
                source_code=source_code,
                language_id=language_id,
                stdin=test_case["stdin"],
                expected_output=test_case["expected_output"]
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

        overall_result = calculate_overall_result(results)

        return {
            "success": True,
            "overall_result": overall_result,
            "results": results,
            "is_test_run": True
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"测试运行失败: {str(e)}",
            "is_test_run": True
        }


def get_test_cases_by_topic_with_cache(topic_id):
    """
    根据题目ID从Redis缓存或数据库获取测试用例
    # """
    from django.conf import settings
    cache_key = f"test_cases_topic_{topic_id}"

    # 尝试从缓存获取测试用例
    cached_test_cases = cache.get(cache_key)

    if cached_test_cases is not None:
        return cached_test_cases

    # 缓存未命中，从数据库获取
    test_cases = get_test_cases_from_db(topic_id)

    # 将结果存入缓存
    if test_cases:
        cache.set(cache_key, test_cases, timeout=getattr(settings, 'CACHE_TTL', 900))

    return test_cases


def get_sample_test_cases(topic_id):
    """
    获取样例测试用例
    """
    try:
        test_cases = TestCase.objects.filter(
            titleSlug_id=topic_id,
            is_sample=True
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
        return [{
            "stdin": "",
            "expected_output": "",
            "is_sample": True,
            "score": 0
        }]


def get_test_cases_from_db(topic_id):
    """
    从数据库获取测试用例
    """
    try:

        test_cases = TestCase.objects.filter(
            titleSlug_id=topic_id
        ).order_by('order')

        # Topic = topic.objects.get(id=topic_id)
        # test_cases = TestCase.objects.filter(
        #     titleSlug=Topic
        # ).order_by('order')


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