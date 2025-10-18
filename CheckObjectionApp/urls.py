from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter
from CheckObjectionApp import views
from CheckObjectionApp.views import JudgeCodeView, TaskStatusView

app_name = 'CheckObjectionApp'

from django.urls import path, include

router = DefaultRouter()
router.register(r'topics', views.TopicViewSet)
router.register(r'testcases', views.TestCaseViewSet)

urlpatterns = [
    # path('detail/proxy-submit-code', views.quick_judge_example, name='proxy_submit_code'),
    path('detail/proxy-submit-code/', JudgeCodeView.as_view(), name='proxy_submit_code'),
    path('api/', include(router.urls)),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task_status'),
    path('submission', views.submission_list, name='submission_list'),
    path('submission/<uuid:pk>/', views.submission_detail, name='submission_detail'),

    path('my_submission', views.my_submission_list, name='my_submission_list'),

    path("index", views.index, name="CheckObjectionApp_index"),
    path("base", views.base, name="CheckObjectionApp_base"),
    path("detail/<topic_id>", views.detail, name="CheckObjectionApp_detail"),
    path("design", views.design, name="CheckObjectionApp_design"),
    path("show", views.submission_list, name="CheckObjectionApp_show"),
    path("changeName", views.changeName, name="CheckObjectionApp_changeName"),
    path('changePassword', views.changePassword, name="CheckObjectionApp_changePassword"),
    # 排行
    path('ranking/', views.ranking_view, name='ranking_page'),
    # 生成验证码
    path('image_code',views.image_code,name='image_code'),
    # 删除缓存
    path('clear_my_submission_cache', views.clear_my_submission_cache, name='clear_my_submission_cache'),

    path("CheckObjection_login", views.CheckObjection_login, name="CheckObjectionApp_login"),
    path("CheckObjection_logout", views.CheckObjection_logout, name="CheckObjectionApp_logout"),
    path("CheckObjection_noPower", views.CheckObjection_noPower, name="CheckObjection_noPower"),
    path('CheckObjection_search', views.CheckObjection_search, name='CheckObjection_search'),
    path("CheckObjection_filter", views.CheckObjection_filter, name='CheckObjection_filter'),
    # path("get",views.topic_get.as_view(),name="CheckObjection_topic_get"),
    # path("get",views.topicModel_get.as_view({"get":"get"}), name="CheckObjection_get"),
    path("t1", views.topicModel_get.as_view()),
    path("t2", views.topicAPIGenericAPIView.as_view()),
    path('get', views.topicAPIView.as_view(), name='CheckObjection_get'),
    path('topic/', views.Topic.as_view(), name='topic-list'),
    path('topic/<int:pk>/', views.Topic.as_view(), name='topic-detail'),
    path("get1", views.get1, name="CheckObjection_get1"),
    path('s1', views.topicAPIView.as_view()),
    # path("CheckObjectionApp_pub", views.CheckObjectionApp_pub, name="CheckObjectionApp_pub"),
    # path("send_email_captcha", views.send_email_captcha, name="send_email_captcha"),
    # path("CheckObjectionApp_register", views.CheckObjectionApp_register, name="CheckObjectionApp_register"),
    # path("CheckObjectionApp_login", views.CheckObjectionApp_login, name="CheckObjectionApp_login"),
    # path("CheckObjectionApp_logout", views.CheckObjectionApp_logout, name="CheckObjectionApp_logout"),
    # path("CheckObjectionApp_detail/<blog_id>", views.CheckObjectionApp_detail, name="CheckObjectionApp_detail"),
    # path('CheckObjectionApp/comment/pub', views.pub_comment, name='pub_comment'),
    # path('search', views.search, name='search'),
    # path('CheckObjectionApp_myself/<user_id>', views.CheckObjectionApp_myself, name='CheckObjectionApp_myself'),
    # path('CheckObjectionApp_dialogue', views.CheckObjectionApp_dialogue, name='CheckObjectionApp_dialogue'),
    # path('CheckObjectionApp_informationChange/<user_id>',views.CheckObjectionApp_informationChange,name='CheckObjectionApp_informationChange'),
    # path('CheckObjectionApp_test', views.CheckObjectionApp_test, name='CheckObjectionApp_test'),
    # path('CheckObjectionApp_myself_to_myBlogs/<user_id>',views.CheckObjectionApp_myself_to_myBlogs,name='CheckObjectionApp_myself_to_myBlogs'),
    # path('CheckObjectionApp_test2/<user_id>', views.CheckObjectionApp_test2, name='CheckObjectionApp_test2'),
]
