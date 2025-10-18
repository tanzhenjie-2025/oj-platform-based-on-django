from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.db.models import Count
from .models import topic, answer, UserProfile, TestCase, Submission


# 修改 answer 模型，添加外键关系（推荐）
# 或者修改现有的 answer 模型定义，将 topic_id 改为外键
# 如果不想修改模型，我们移除内联并使用其他方式展示

class TestCaseInline(admin.TabularInline):
    """题目测试用例内联"""
    model = TestCase
    extra = 1
    fields = ('input_data', 'expected_output', 'is_sample', 'order', 'score')
    ordering = ['order']


# 移除了 AnswerInline，因为 answer 模型没有外键到 topic

# 主模型Admin配置
@admin.register(topic)
class TopicAdmin(ModelAdmin):
    """题目管理"""
    list_display = (
        'id', 'title', 'level', 'pub_time',
        'testcase_count', 'answer_count', 'status_badge'
    )
    list_filter = ('level', 'pub_time')
    search_fields = ('title', 'content')
    list_per_page = 20
    list_editable = ('level',)
    date_hierarchy = 'pub_time'
    readonly_fields = ('pub_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'level', 'pub_time')
        }),
        ('题目内容', {
            'fields': ('content', 'example'),
            'classes': ('wide',)
        }),
    )
    inlines = [TestCaseInline]  # 只保留 TestCaseInline

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            testcase_count=Count('testcase_set'),

        )

    def testcase_count(self, obj):
        return obj.testcase_count

    testcase_count.short_description = '测试用例数'
    testcase_count.admin_order_field = 'testcase_count'

    def answer_count(self, obj):
        # 手动计算回答数量
        return answer.objects.filter(topic_id=obj.id).count()

    answer_count.short_description = '回答数'

    def status_badge(self, obj):
        """状态徽章"""
        if obj.level == 0:
            return format_html('<span style="color: green;">● 简单</span>')
        elif obj.level == 1:
            return format_html('<span style="color: orange;">● 中等</span>')
        else:
            return format_html('<span style="color: red;">● 困难</span>')

    status_badge.short_description = '难度'

    # 添加自定义操作来查看相关回答
    actions = ['view_related_answers']

    def view_related_answers(self, request, queryset):
        """查看选中题目的相关回答"""
        from django.urls import reverse
        from django.http import HttpResponseRedirect

        if queryset.count() == 1:
            topic_id = queryset.first().id
            url = reverse('admin:CheckObjectionApp_answer_changelist') + f'?topic_id={topic_id}'
            return HttpResponseRedirect(url)
        else:
            self.message_user(request, "请只选择一个题目", level='error')

    view_related_answers.short_description = '查看相关回答'


@admin.register(answer)
class AnswerAdmin(ModelAdmin):
    """回答管理"""
    list_display = (
        'id', 'topic_title', 'user_name',
        'content_preview', 'pub_time'
    )
    list_filter = ('pub_time', 'user_name')
    search_fields = ('user_name', 'content', 'topic_id')
    list_per_page = 20
    readonly_fields = ('pub_time',)
    date_hierarchy = 'pub_time'

    # 添加自定义过滤器来按题目筛选
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        topic_id = request.GET.get('topic_id')
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        return qs

    def get_list_filter(self, request):
        list_filter = list(super().get_list_filter(request))
        # 添加题目ID过滤器
        list_filter.append('topic_id')
        return list_filter

    fieldsets = (
        ('关联信息', {
            'fields': ('topic_id', 'user_name')
        }),
        ('内容', {
            'fields': ('content', 'notes')
        }),
        ('时间', {
            'fields': ('pub_time',)
        }),
    )

    def topic_title(self, obj):
        """显示题目标题"""
        try:
            topic_obj = topic.objects.get(id=obj.topic_id)
            return format_html('<a href="{}">{}</a>',
                               reverse('admin:CheckObjectionApp_topic_change', args=[obj.topic_id]),
                               topic_obj.title)
        except topic.DoesNotExist:
            return "未知题目"

    topic_title.short_description = '题目'

    def content_preview(self, obj):
        """内容预览"""
        content = obj.content
        if len(content) > 100:
            return content[:100] + '...'
        return content

    content_preview.short_description = '回答内容'


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    """用户信息管理"""
    list_display = ('user_id', 'finish', 'username_display')
    list_filter = ('finish',)
    search_fields = ('user_id',)
    list_per_page = 20
    list_editable = ('finish',)

    def username_display(self, obj):
        """显示用户名"""
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=obj.user_id)
            return user.username
        except User.DoesNotExist:
            return "未知用户"

    username_display.short_description = '用户名'


@admin.register(TestCase)
class TestCaseAdmin(ModelAdmin):
    """测试用例管理"""
    list_display = (
        'id', 'topic_title', 'is_sample',
        'order', 'score', 'created_at'
    )
    list_filter = ('is_sample', 'created_at')
    search_fields = ('titleSlug__title', 'input_data', 'expected_output')
    list_per_page = 20
    list_editable = ('is_sample', 'order', 'score')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('关联信息', {
            'fields': ('titleSlug',)
        }),
        ('测试数据', {
            'fields': ('input_data', 'expected_output')
        }),
        ('配置', {
            'fields': ('is_sample', 'order', 'score')
        }),
        ('时间', {
            'fields': ('created_at',)
        }),
    )

    def topic_title(self, obj):
        return obj.titleSlug.title

    topic_title.short_description = '题目'


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    """提交记录管理"""
    list_display = (
        'id_short', 'user_name', 'topic_id',
        'language_display', 'status_badge',
        'overall_result', 'created_at'
    )
    list_filter = ('status', 'language_id', 'created_at')
    search_fields = ('user_name', 'topic_id', 'source_code')
    list_per_page = 25
    readonly_fields = (
        'id', 'created_at', 'updated_at',
        'results_display', 'source_code_preview'
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'user_name', 'topic_id', 'created_at')
        }),
        ('提交内容', {
            'fields': ('language_id', 'source_code_preview', 'notes')
        }),
        ('判题结果', {
            'fields': ('status', 'overall_result', 'results_display')
        }),
    )

    def id_short(self, obj):
        """缩短ID显示"""
        return str(obj.id)[:8]

    id_short.short_description = 'ID'

    def language_display(self, obj):
        """语言显示"""
        languages = {
            71: 'Python',
            62: 'Java',
            54: 'C++',
            50: 'C'
        }
        return languages.get(obj.language_id, f'未知({obj.language_id})')

    language_display.short_description = '语言'

    def status_badge(self, obj):
        """状态徽章"""
        status_colors = {
            'Accepted': 'green',
            'Wrong Answer': 'red',
            'Time Limit Exceeded': 'orange',
            'Runtime Error': 'purple',
            'Compile Error': 'brown',
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">● {}</span>',
            color, obj.status
        )

    status_badge.short_description = '状态'

    def source_code_preview(self, obj):
        """源代码预览"""
        return format_html(
            '<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; max-height: 300px; overflow: auto;">{}</pre>',
            obj.source_code
        )

    source_code_preview.short_description = '源代码'

    def results_display(self, obj):
        """测试结果展示"""
        if not obj.results:
            return "无结果"

        results_html = []
        for i, result in enumerate(obj.results, 1):
            status = result.get('status', {}).get('description', 'Unknown')
            results_html.append(f"测试用例 {i}: {status}")

        return format_html('<br>'.join(results_html))

    results_display.short_description = '详细结果'


# 在文件顶部添加导入
from django.urls import reverse

# Admin站点标题配置
admin.site.site_header = 'OJ平台管理系统'
admin.site.site_title = 'OJ平台'
admin.site.index_title = '系统管理'