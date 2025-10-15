from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class topic(models.Model):
    """内容"""
    title = models.CharField(max_length=200,verbose_name='题目')

    content = models.TextField(verbose_name='描述')
    example = models.TextField(verbose_name='示例')
    pub_time = models.DateTimeField(auto_now_add=True,verbose_name='发布时间')
    level = models.IntegerField(default=0)
    def __str__(self):
        # 返回标题
        return self.title
    class Meta:
        verbose_name = '题目信息模型'
        verbose_name_plural = '题目信息模型'
        ordering = ['-pub_time']

class answer(models.Model):
    topic_id = models.BigIntegerField(verbose_name='问题题号')
    content = models.TextField(verbose_name='回答内容')
    notes = models.TextField(verbose_name='备注')
    pub_time = models.DateTimeField(auto_now_add=True,verbose_name='发布时间')
    user_name = models.TextField(verbose_name='姓名')
    def __str__(self):
        # 返回标题
        return self.content
    class Meta:
        verbose_name = '用户回答模型'
        verbose_name_plural = '用户回答模型'
        ordering = ['-pub_time']


class UserProfile(models.Model):
    user_id = models.BigIntegerField(verbose_name='id号')
    finish = models.BigIntegerField(default=0,verbose_name='完成数量')
    def __str__(self):
        return str(self.user_id)

    class Meta:
        verbose_name = '用户附加信息模型'
        verbose_name_plural = '用户附加信息模型'


class TestCase(models.Model):
    titleSlug = models.ForeignKey(topic, on_delete=models.CASCADE, related_name='testcase_set', verbose_name="题目别名")
    input_data = models.TextField(blank=True, verbose_name="输入数据")
    expected_output = models.TextField(verbose_name="期望输出")

    # 测试用例元数据
    is_sample = models.BooleanField(default=False, verbose_name="是否样例")
    order = models.IntegerField(default=0, verbose_name="排序")
    score = models.IntegerField(default=10, verbose_name="分数")

    # Judge0相关配置
    # time_limit = models.IntegerField(null=True, blank=True, verbose_name="自定义时间限制(ms)")
    # memory_limit = models.IntegerField(null=True, blank=True, verbose_name="自定义内存限制(KB)")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'judge_test_cases'
        ordering = ['order', 'id']


