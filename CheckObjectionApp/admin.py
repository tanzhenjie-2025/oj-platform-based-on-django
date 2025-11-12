from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse

from .forms import User
from .models import topic, answer, UserProfile, TestCase, Submission, Contest, ContestParticipant, ContestTopic, \
    ContestSubmission


# 修改 answer 模型，添加外键关系（推荐）
# 或者修改现有的 answer 模型定义，将 topic_id 改为外键
# 如果不想修改模型，我们移除内联并使用其他方式展示

class TestCaseInline(admin.TabularInline):
    """题目测试用例内联"""
    model = TestCase
    extra = 1
    fields = ('input_data', 'expected_output', 'is_sample', 'order', 'score')
    ordering = ['order']


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
    # 更新为使用 user 字段而不是 old_user_id
    list_display = ('user_info', 'finish', 'user_email')
    list_filter = ('finish',)
    search_fields = ('user__username', 'user__email')  # 可以通过用户名和邮箱搜索
    list_per_page = 20
    list_editable = ('finish',)

    # 添加字段分组
    fieldsets = (
        ('用户信息', {
            'fields': ('user', 'finish')
        }),
    )

    def user_info(self, obj):
        """显示用户信息"""
        if obj.user:
            return format_html(
                '<a href="{}">{}</a> (ID: {})',
                reverse('admin:auth_user_change', args=[obj.user.id]),
                obj.user.username,
                obj.user.id
            )
        return "无关联用户"

    user_info.short_description = '用户信息'
    user_info.admin_order_field = 'user__username'

    def user_email(self, obj):
        """显示用户邮箱"""
        if obj.user:
            return obj.user.email
        return "无邮箱"

    user_email.short_description = '邮箱'


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
class SubmissionAdmin(admin.ModelAdmin):
    """提交记录管理"""
    list_display = (
        'id_short', 'user_name', 'old_topic_id',
        'language_display', 'status_badge',
        'overall_result', 'created_at'
    )
    list_filter = ('status', 'language_id', 'created_at')
    search_fields = ('user_name', 'old_topic_id', 'source_code')
    list_per_page = 25
    readonly_fields = (
        'id', 'created_at', 'updated_at',
        'results_display', 'source_code_preview'
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'user_name', 'old_topic_id', 'created_at')
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


# 比赛题目内联配置
class ContestTopicInline(admin.TabularInline):
    model = ContestTopic
    extra = 3  # 默认显示3个空白的题目表单
    fields = ['topic', 'order', 'score']
    ordering = ['order']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """过滤可选的题目"""
        if db_field.name == "topic":
            # 可以在这里添加题目过滤逻辑，比如只显示特定难度的题目
            kwargs["queryset"] = topic.objects.all().order_by('level', 'title')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# 比赛参与者内联配置
class ContestParticipantInline(admin.TabularInline):
    model = ContestParticipant
    extra = 1
    fields = ['user', 'is_disqualified']
    readonly_fields = ['registered_at']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.all().order_by('username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'start_time',
        'end_time',
        'status_display',
        'topic_count',
        'participant_count',
        'created_by',
        'is_public'
    ]
    list_filter = ['is_public', 'start_time', 'created_by']
    search_fields = ['title', 'description']
    readonly_fields = ['status_display', 'created_at', 'updated_at']
    date_hierarchy = 'start_time'

    # 在编辑页面显示的内联
    inlines = [ContestTopicInline, ContestParticipantInline]

    # 字段分组显示
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'start_time', 'end_time', 'created_by')
        }),
        ('权限设置', {
            'fields': ('is_public', 'password', 'allow_register')
        }),
        ('比赛规则', {
            'fields': ('penalty_time', 'ranking_frozen', 'frozen_time')
        }),
        ('状态信息', {
            'fields': ('status_display', 'created_at', 'updated_at')
        })
    )

    # 自定义方法用于列表显示
    def status_display(self, obj):
        # 用CONTEST_STATUS创建一个"状态值: 显示文本"的映射字典
        status_mapping = dict(Contest.CONTEST_STATUS)
        # 获取当前状态对应的显示文本（比如obj.status是'pending'，则对应'未开始'）
        display_text = status_mapping.get(obj.status, obj.status)  # 兜底防止未定义的状态

        status_colors = {
            'pending': 'orange',
            'running': 'green',
            'ended': 'gray'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            display_text  # 这里用手动映射的显示文本，替代get_status_display()
        )

    status_display.short_description = '比赛状态'

    def topic_count(self, obj):
        return obj.contest_topics.count()

    topic_count.short_description = '题目数量'

    def participant_count(self, obj):
        return obj.participants.count()

    participant_count.short_description = '参赛人数'

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # 新建时自动设置创建者
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # 批量操作
    actions = ['make_public', 'make_private']

    def make_public(self, request, queryset):
        queryset.update(is_public=True)

    make_public.short_description = "设为公开比赛"

    def make_private(self, request, queryset):
        queryset.update(is_public=False)

    make_private.short_description = "设为私有比赛"


# 单独注册比赛题目模型，方便独立管理
@admin.register(ContestTopic)
class ContestTopicAdmin(admin.ModelAdmin):
    list_display = ['contest', 'topic', 'order', 'score']
    list_filter = ['contest']
    search_fields = ['contest__title', 'topic__title']
    list_editable = ['order', 'score']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "contest":
            kwargs["queryset"] = Contest.objects.all().order_by('-start_time')
        elif db_field.name == "topic":
            kwargs["queryset"] = topic.objects.all().order_by('level', 'title')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ContestParticipant)
class ContestParticipantAdmin(admin.ModelAdmin):
    list_display = ['contest', 'user', 'registered_at', 'is_disqualified']
    list_filter = ['contest', 'registered_at', 'is_disqualified']
    search_fields = ['user__username', 'contest__title']
    list_editable = ['is_disqualified']

    actions = ['disqualify_participants', 'qualify_participants']

    def disqualify_participants(self, request, queryset):
        queryset.update(is_disqualified=True)

    disqualify_participants.short_description = "取消选中参与者的资格"

    def qualify_participants(self, request, queryset):
        queryset.update(is_disqualified=False)

    qualify_participants.short_description = "恢复选中参与者的资格"


@admin.register(ContestSubmission)
class ContestSubmissionAdmin(admin.ModelAdmin):
    list_display = ['contest', 'participant', 'submission', 'submitted_at']
    list_filter = ['contest', 'submitted_at']
    readonly_fields = ['submitted_at']

    def has_add_permission(self, request):
        # 比赛提交记录应该通过系统自动创建，不允许手动添加
        return False


# Admin站点标题配置
admin.site.site_header = 'OJ平台管理系统'
admin.site.site_title = 'OJ平台'
admin.site.index_title = '系统管理'