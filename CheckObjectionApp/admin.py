from django.contrib import admin

import CheckObjection
# Register your models here.
from CheckObjectionApp.models import answer,topic,UserProfile

class answerAdmin(admin.ModelAdmin):
    list_display = ['topic_id','content','notes','pub_time','user_name']
    # topic_id = models.BigIntegerField(verbose_name='问题题号')
    # content = models.TextField(verbose_name='回答内容')
    # notes = models.TextField(verbose_name='备注')
    # pub_time = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    # user_name = models.TextField(verbose_name='姓名')
    search_fields = ['topic_id','user_name']
    list_filter = ['pub_time','topic_id']

    # class Meta:
    #     model = answer
    #     fields = '__all__'
    #     list_display = ('user','topic','answer')
    #     list_filter = ('user','topic')
    #     search_fields = ('user','topic')
    #     ordering = ('user','topic')
    #     filter_horizontal = ()
    #     readonly_fields = ('user','topic','answer')
    #     fieldsets = (
    #         (None, {'fields': ('user','topic','answer')}),
    #     )
class topicAdmin(admin.ModelAdmin):
    list_display = ['title','content','example','pub_time','level']
    search_fields = ['title','content']
    list_filter = ['pub_time','level']
    # title = models.CharField(max_length=200, verbose_name='题目')
    # content = models.TextField(verbose_name='描述')
    # example = models.TextField(verbose_name='示例')
    # pub_time = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')
    # level = models.IntegerField(default=0)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_id','finish']

    # user_id = models.BigIntegerField(verbose_name='id号')
    # finish = models.BigIntegerField(default=0, verbose_name='完成数量')
# 开始注册 分别是作答内容，题目内容，每个人的附加信息
admin.site.register(answer,answerAdmin)
admin.site.register(topic)
admin.site.register(UserProfile)