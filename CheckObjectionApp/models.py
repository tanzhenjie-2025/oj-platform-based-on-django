from django.db import models
from django.contrib.auth.models import User

from CheckObjection import settings


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

# todo 重构为题解 修改view
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

# todo 重构时要修改view视图中的保存逻辑
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,  # 设置为主键
        verbose_name='用户'
    )
    finish = models.BigIntegerField(default=0, verbose_name='完成数量')

    def __str__(self):
        return str(self.user.username)  # 使用用户名而不是ID

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


from django.db import models
import uuid


# todo 修改判题逻辑的保存
class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        blank=True,# 允许为空,后面修改晚再改
        null=True
    )
    user_name = models.CharField(max_length=100)
    topic = models.ForeignKey(
        'topic',  # 关联到topic模型（类名是小写的topic）
        on_delete=models.CASCADE,  # 当题目被删除时，关联的提交也删除
        related_name='submissions',  # 反向关联名：topic.submissions可查所有提交
        null=False  # 暂时允许为空，后续会填充数据

    )

    old_topic_id = models.CharField(max_length=100)

    source_code = models.TextField()
    language_id = models.IntegerField(default=71)
    status = models.CharField(max_length=20)
    overall_result = models.CharField(max_length=50, blank=True, null=True)
    results = models.JSONField(blank=True, null=True)  # 存储所有测试用例的结果
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'submissions'
        ordering = ['-created_at']


# 新增比赛模型
class Contest(models.Model):
    CONTEST_STATUS = (
        ('pending', '未开始'),
        ('running', '进行中'),
        ('ended', '已结束')
    )

    title = models.CharField(max_length=200, verbose_name='比赛标题')
    description = models.TextField(verbose_name='比赛描述')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    password = models.CharField(max_length=100, blank=True, null=True, verbose_name='访问密码')

    # 比赛规则设置
    penalty_time = models.IntegerField(default=20, verbose_name='错误提交罚时(分钟)')
    allow_register = models.BooleanField(default=True, verbose_name='允许报名')
    ranking_frozen = models.BooleanField(default=False, verbose_name='封榜')
    frozen_time = models.DateTimeField(blank=True, null=True, verbose_name='封榜时间')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def status(self):
        from django.utils import timezone
        now = timezone.now()

        # 先检查start_time或end_time是否未设置（为None）
        if self.start_time is None or self.end_time is None:
            return '未设置时间'  # 或其他合理的默认状态

        # 只有当时间字段都有值时，才进行比较
        if now < self.start_time:
            return 'pending'
        elif now > self.end_time:
            return 'ended'
        else:
            return 'running'

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '比赛'
        verbose_name_plural = '比赛'
        ordering = ['-start_time']


# 比赛题目关联
class ContestTopic(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='contest_topics')
    topic = models.ForeignKey(topic, on_delete=models.CASCADE, verbose_name='题目')
    order = models.IntegerField(default=0, verbose_name='题目顺序')
    score = models.IntegerField(default=100, verbose_name='题目分数')

    class Meta:
        verbose_name = '比赛题目'
        verbose_name_plural = '比赛题目'
        unique_together = ['contest', 'topic']
        ordering = ['order']


# 比赛参与者
class ContestParticipant(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='参与者')
    registered_at = models.DateTimeField(auto_now_add=True)
    is_disqualified = models.BooleanField(default=False, verbose_name='是否取消资格')

    class Meta:
        verbose_name = '比赛参与者'
        verbose_name_plural = '比赛参与者'
        unique_together = ['contest', 'user']


# 比赛提交记录
class ContestSubmission(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='contest_submissions')
    participant = models.ForeignKey(ContestParticipant, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '比赛提交记录'
        verbose_name_plural = '比赛提交记录'
        ordering = ['submitted_at']

