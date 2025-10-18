# utils/cache_utils.py
from django.core.cache import cache
from django.conf import settings


class SubmissionCache:
    """提交记录缓存工具类"""

    @staticmethod
    def get_cache_key(user_name):
        """生成缓存键"""
        return f"user_submissions_{user_name}"

    @staticmethod
    def get_submissions(user_name, timeout=None):
        """获取用户的提交记录缓存"""
        cache_key = SubmissionCache.get_cache_key(user_name)
        return cache.get(cache_key)

    @staticmethod
    def set_submissions(user_name, submissions, timeout=None):
        """设置用户的提交记录缓存"""
        if timeout is None:
            timeout = getattr(settings, 'SUBMISSION_CACHE_TIMEOUT', 300)

        cache_key = SubmissionCache.get_cache_key(user_name)
        cache.set(cache_key, submissions, timeout)

    @staticmethod
    def delete_submissions(user_name):
        """删除用户的提交记录缓存"""
        cache_key = SubmissionCache.get_cache_key(user_name)
        cache.delete(cache_key)

    @staticmethod
    def get_cache_timeout():
        """获取当前缓存超时时间"""
        return getattr(settings, 'SUBMISSION_CACHE_TIMEOUT', 300)

    @staticmethod
    def set_cache_timeout(timeout):
        """动态设置缓存超时时间"""
        from django.conf import settings
        settings.SUBMISSION_CACHE_TIMEOUT = timeout