from rest_framework import serializers
from .models import topic,answer,UserProfile
# class topic(models.Model):
#     """内容"""
#     title = models.CharField(max_length=200,verbose_name='题目')
#     content = models.TextField(verbose_name='描述')
#     example = models.TextField(verbose_name='示例')
#     pub_time = models.DateTimeField(auto_now_add=True,verbose_name='发布时间')
#     level = models.IntegerField(default=0)
#     def __str__(self):
#         # 返回标题
#         return self.title
#     class Meta:
#         verbose_name = '题目信息模型'
#         verbose_name_plural = '题目信息模型'
#         ordering = ['-pub_time']
#
# class answer(models.Model):
#     topic_id = models.BigIntegerField(verbose_name='问题题号')
#     content = models.TextField(verbose_name='回答内容')
#     notes = models.TextField(verbose_name='备注')
#     pub_time = models.DateTimeField(auto_now_add=True,verbose_name='发布时间')
#     user_name = models.TextField(verbose_name='姓名')
#     def __str__(self):
#         # 返回标题
#         return self.content
#     class Meta:
#         verbose_name = '用户回答模型'
#         verbose_name_plural = '用户回答模型'
#         ordering = ['-pub_time']
#
#
# class UserProfile(models.Model):
#     user_id = models.BigIntegerField(verbose_name='id号')
#     finish = models.BigIntegerField(default=0,verbose_name='完成数量')
#     def __str__(self):
#         return str(self.user_id)
#
#     class Meta:
#         verbose_name = '用户附加信息模型'
#         verbose_name_plural = '用户附加信息模型'

class topicSerializer(serializers.Serializer):
    title = serializers.CharField()
    content = serializers.CharField()
    example = serializers.CharField()
    pub_time = serializers.DateTimeField()
    level = serializers.IntegerField()

class topicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = topic
        fields = '__all__'

# class answerSerializer(serializers.ModelSerializer):
#     author_name = serializers.CharField(source='author.name', read_only=True)
#
#     class Meta:
#         model = answer
#         fields = '__all__'
#
# class UserProfileSerializer(serializers.ModelSerializer):
#     author_name = serializers.CharField(source='author.name', read_only=True)
#
#     class Meta:
#         model = UserProfile
#         fields = '__all__'

from rest_framework import serializers
from .models import topic, TestCase


class TopicSerializer(serializers.ModelSerializer):
    test_cases_count = serializers.SerializerMethodField()

    class Meta:
        model = topic
        fields = ['id', 'title', 'content', 'example', 'pub_time', 'level', 'test_cases_count']
        read_only_fields = ['id', 'pub_time']

    def get_test_cases_count(self, obj):
        return obj.testcase_set.count()


class TestCaseSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source='titleSlug.title', read_only=True)

    class Meta:
        model = TestCase
        fields = ['id', 'titleSlug', 'topic_title', 'input_data', 'expected_output',
                  'is_sample', 'order', 'score', 'created_at']
        read_only_fields = ['id', 'created_at']


class TestCaseDetailSerializer(TestCaseSerializer):
    class Meta(TestCaseSerializer.Meta):
        fields = TestCaseSerializer.Meta.fields + ['titleSlug']


class TopicWithTestCasesSerializer(TopicSerializer):
    test_cases = TestCaseSerializer(many=True, read_only=True, source='testcase_set')

    class Meta(TopicSerializer.Meta):
        fields = TopicSerializer.Meta.fields + ['test_cases']