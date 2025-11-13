# CheckObjectionApp/views/judge.py
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse

from CheckObjectionApp.constants import JUDGE_CONFIG
# 导入判题任务函数
from mycelery.sms.tasks import submit_code_task


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