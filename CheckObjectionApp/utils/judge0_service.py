import requests
import time
import json
from django.conf import settings



class Judge0Service:
    def __init__(self):
        # 从settings获取Judge0配置
        self.base_url = getattr(settings, 'JUDGE0_BASE_URL', "http://192.168.231.100:2358")
        self.submission_url = f"{self.base_url}/submissions"
        self.headers = {
            "Content-Type": "application/json",
        }
        self.timeout = getattr(settings, 'JUDGE0_TIMEOUT', 30)

    def submit_code(self, source_code, language_id, stdin="", expected_output=""):
        """
        提交代码到Judge0进行判题
        """
        submission_data = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
            "expected_output": expected_output,
            "cpu_time_limit": 2,
            "memory_limit": 128000,
            "wall_time_limit": 5,
        }

        try:
            # 提交代码
            response = requests.post(
                f"{self.submission_url}?base64_encoded=false&wait=false",
                headers=self.headers,
                data=json.dumps(submission_data),
                timeout=self.timeout
            )

            if response.status_code == 201:
                submission_token = response.json()["token"]
                return self._get_submission_result(submission_token)
            else:
                return {"error": f"提交失败: {response.status_code}", "status": "Error"}

        except requests.exceptions.Timeout:
            return {"error": "Judge0服务响应超时", "status": "Timeout"}
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
                    headers=self.headers,
                    timeout=self.timeout
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
            3: "Accepted",
            4: "Wrong Answer",
            5: "Time Limit Exceeded",
            6: "Compilation Error",
            7: "Runtime Error",
            8: "Memory Limit Exceeded",
            11: "Internal Error",
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