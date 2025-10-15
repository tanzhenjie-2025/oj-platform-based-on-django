import requests
import time
import json


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View


class Judge0Service:
    def __init__(self):
        # Judge0服务地址 - 根据你的Docker部署情况修改
        self.base_url = "http://192.168.231.100:2358"
        self.submission_url = f"{self.base_url}/submissions"
        self.headers = {
            "Content-Type": "application/json",
        }

    def submit_code(self, source_code, language_id, stdin="", expected_output=""):
        """
        提交代码到Judge0进行判题

        Args:
            source_code (str): 源代码
            language_id (int): 语言ID
            stdin (str): 输入数据
            expected_output (str): 期望输出

        Returns:
            dict: 判题结果
        """
        # 语言ID参考：
        # 54: C++, 71: Python, 62: Java, 63: JavaScript, 50: C
        submission_data = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
            "expected_output": expected_output,
            "cpu_time_limit": 2,  # CPU时间限制(秒)
            "memory_limit": 128000,  # 内存限制(KB)
            "wall_time_limit": 5,  # 挂钟时间限制(秒)
        }

        try:
            # 提交代码
            response = requests.post(
                f"{self.submission_url}?base64_encoded=false&wait=false",
                headers=self.headers,
                data=json.dumps(submission_data)
            )

            if response.status_code == 201:
                submission_token = response.json()["token"]
                return self._get_submission_result(submission_token)
            else:
                return {"error": f"提交失败: {response.status_code}", "status": "Error"}

        except requests.exceptions.ConnectionError:
            return {"error": "无法连接到Judge0服务", "status": "Connection Error"}
        except Exception as e:
            return {"error": f"判题服务异常: {str(e)}", "status": "Error"}

    def _get_submission_result(self, token, max_retries=10):
        """
        获取提交结果
        """
        for i in range(max_retries):
            try:
                response = requests.get(
                    f"{self.submission_url}/{token}?base64_encoded=false",
                    headers=self.headers
                )

                if response.status_code == 200:
                    result = response.json()

                    # 如果还在队列中或处理中，等待后重试
                    if result["status"]["id"] in [1, 2]:  # In Queue, Processing
                        time.sleep(0.5)
                        continue

                    return self._format_result(result)

            except Exception as e:
                return {"error": f"获取结果失败: {str(e)}", "status": "Error"}

        return {"error": "获取结果超时", "status": "Timeout"}

    def _format_result(self, result):
        """
        格式化判题结果
        """
        status_map = {
            3: "Accepted",  # 通过
            4: "Wrong Answer",  # 答案错误
            5: "Time Limit Exceeded",  # 超时
            6: "Compilation Error",  # 编译错误
            7: "Runtime Error",  # 运行时错误
            8: "Memory Limit Exceeded",  # 内存超限
            11: "Internal Error",  # 内部错误
        }

        formatted_result = {
            "status": status_map.get(result["status"]["id"], "Unknown"),
            "status_id": result["status"]["id"],
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "compile_output": result.get("compile_output", ""),
            "time": result.get("time", ""),
            "memory": result.get("memory", ""),
            "message": result["status"]["description"]
        }

        # 如果有编译错误，将编译输出放到stderr中
        if result["status"]["id"] == 6 and formatted_result["compile_output"]:
            formatted_result["stderr"] = formatted_result["compile_output"]

        return formatted_result





# # 添加到Django的URL配置中
# def add_judge_urls(urlpatterns):
#     """
#     在urls.py中调用这个函数来添加判题路由
#     """
#     urlpatterns.append(path('proxy-submit-code/', JudgeCodeView.as_view(), name='proxy_submit_code'))