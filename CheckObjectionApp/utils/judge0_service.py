import requests
import time
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Judge0Service:
    def __init__(self):
        self.base_url = getattr(settings, 'JUDGE0_BASE_URL', 'http://judge0:2358')
        self.submission_url = f"{self.base_url}/submissions"
        self.headers = {
            "Content-Type": "application/json",
        }
        self.timeout = getattr(settings, 'JUDGE0_TIMEOUT', 30)
        logger.info(f"Judge0Service 初始化: base_url={self.base_url}, timeout={self.timeout}")

    def submit_code(self, source_code, language_id, stdin="", expected_output=""):
        """
        提交代码到Judge0进行判题
        """
        submission_data = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
            "expected_output": expected_output,
            "cpu_time_limit": 5,
            "memory_limit": 256000,
            "wall_time_limit": 15,
            "enable_network": False,
            "number_of_runs": 1,
        }

        logger.info(f"提交 Judge0 请求:")
        logger.info(f"  URL: {self.submission_url}?base64_encoded=false&wait=true")
        logger.info(f"  代码: {source_code[:100]}...")
        logger.info(f"  语言: {language_id}")
        logger.info(f"  输入: {stdin}")
        logger.info(f"  期望输出: {expected_output}")

        try:
            start_time = time.time()

            # 提交代码
            response = requests.post(
                f"{self.submission_url}?base64_encoded=false&wait=true",
                headers=self.headers,
                data=json.dumps(submission_data),
                timeout=self.timeout
            )

            end_time = time.time()
            logger.info(f"Judge0 响应时间: {end_time - start_time:.2f}秒")
            logger.info(f"Judge0 响应状态: {response.status_code}")

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Judge0 返回结果: {json.dumps(result, indent=2)}")
                return self._format_result(result)
            else:
                error_msg = f"Judge0 提交失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"error": error_msg, "status": "Error"}

        except requests.exceptions.Timeout:
            error_msg = f"Judge0 服务响应超时 ({self.timeout}秒)"
            logger.error(error_msg)
            return {"error": error_msg, "status": "Timeout"}
        except requests.exceptions.ConnectionError as e:
            error_msg = f"无法连接到Judge0服务: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "Connection Error"}
        except Exception as e:
            error_msg = f"判题服务异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg, "status": "Error"}

    def _format_result(self, result):
        """
        格式化判题结果
        """
        status_map = {
            1: "In Queue",
            2: "Processing",
            3: "Accepted",
            4: "Wrong Answer",
            5: "Time Limit Exceeded",
            6: "Compilation Error",
            7: "Runtime Error",
            8: "Memory Limit Exceeded",
            9: "Output Limit Exceeded",
            10: "System Error",
            11: "Internal Error",
            12: "Exec Format Error",
        }

        status_id = result.get("status", {}).get("id", 11)

        formatted_result = {
            "status": status_map.get(status_id, "Unknown"),
            "status_id": status_id,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "compile_output": result.get("compile_output", ""),
            "time": result.get("time", ""),
            "memory": result.get("memory", ""),
            "message": result.get("status", {}).get("description", "")
        }

        # 如果有编译错误，将编译输出放到stderr中
        if status_id == 6 and formatted_result["compile_output"]:
            formatted_result["stderr"] = formatted_result["compile_output"]

        logger.info(f"格式化后的结果: {formatted_result}")
        return formatted_result