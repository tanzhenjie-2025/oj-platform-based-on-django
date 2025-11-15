# CheckObjectionApp/templatetags/objection_tags.py
from django import template
from django.urls import reverse
from CheckObjectionApp.constants import URLNames

register = template.Library()

# 通用URL标签
@register.simple_tag
def objection_url(name):
    """通用URL标签，根据名称生成URL"""
    return reverse(f"CheckObjectionApp:{name}")

# ===== 基础页面 =====
@register.simple_tag
def url_index():
    """首页URL"""
    return reverse(f"CheckObjectionApp:{URLNames.INDEX}")

@register.simple_tag
def url_base():
    """基础页面URL"""
    return reverse(f"CheckObjectionApp:{URLNames.BASE}")

# ===== 用户认证 =====
@register.simple_tag
def url_login():
    """登录页面URL"""
    return reverse(f"CheckObjectionApp:{URLNames.LOGIN}")

# @register.simple_tag
# def url_image_code():
#     """验证码生成url"""

@register.simple_tag
def url_logout():
    """退出登录URL"""
    return reverse(f"CheckObjectionApp:{URLNames.LOGOUT}")

@register.simple_tag
def url_register():
    """注册页面URL"""
    return reverse(f"CheckObjectionApp:{URLNames.REGISTER}")

# ===== 用户资料 =====
@register.simple_tag
def url_change_name():
    """修改用户名URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CHANGE_NAME}")

@register.simple_tag
def url_change_password():
    """修改密码URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CHANGE_PASSWORD}")

# ===== 题目相关 =====
@register.simple_tag
def url_topic_detail(topic_id):
    """题目详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.TOPIC_DETAIL}", args=[topic_id])

@register.simple_tag
def url_topic_filter():
    """题目过滤URL"""
    return reverse(f"CheckObjectionApp:{URLNames.TOPIC_FILTER}")

@register.simple_tag
def url_topic_search():
    """题目搜索URL"""
    return reverse(f"CheckObjectionApp:{URLNames.TOPIC_SEARCH}")

@register.simple_tag
def url_topic_design():
    """题目设计URL"""
    return reverse(f"CheckObjectionApp:{URLNames.TOPIC_DESIGN}")



# ===== 提交记录相关 =====
@register.simple_tag
def url_show():
    """查看全部提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.SUBMISSION_LIST}")

@register.simple_tag
def url_my_submissions_list():
    """我的提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.MY_SUBMISSION_LIST}")

@register.simple_tag
def url_query_contest_submission_list(user_name,contest_id):
    """查询比赛提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.QUERY_CONTEST_SUBMISSION_LIST}",
                   kwargs={'contest_id': contest_id, 'user_name': user_name})

@register.simple_tag
def url_my_contest_submission_list():
    """我的全部比赛提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.MY_CONTEST_SUBMISSION_LIST}")

@register.simple_tag
def url_query_submission_list(user_name):
    """查询提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.QUERY_SUBMISSION_LIST}", args=[user_name])

@register.simple_tag
def url_all_contest_submission_list():
    return reverse(f"CheckObjectionApp:{URLNames.ALL_CONTEST_SUBMISSION_LIST}")
# ===== 比赛相关 =====
@register.simple_tag
def url_contest_list():
    """内部算法竞赛URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_LIST}")

@register.simple_tag
def url_contest_detail(contest_id):
    """比赛详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_DETAIL}", args=[contest_id])

@register.simple_tag
def url_contest_register(contest_id):
    """比赛报名URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_REGISTER}", args=[contest_id])

@register.simple_tag
def url_contest_submit_code(contest_id, contest_topic_id):
    """比赛提交代码URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_SUBMIT_CODE}", kwargs={'contest_id': contest_id, 'contest_topic_id': contest_topic_id})

# ===== 排行榜 =====
@register.simple_tag
def url_ranking():
    """排行榜URL"""
    return reverse(f"CheckObjectionApp:{URLNames.RANKING_PAGE}")

@register.simple_tag
def url_all_contest_rank_list():
    """比赛排行列表URL"""
    return reverse(f"CheckObjectionApp:{URLNames.ALL_CONTEST_RANK_LIST}")

# ===== 工具功能 =====
@register.simple_tag
def url_batch_import_testcases():
    """批量导入测试案例URL"""
    return reverse(f"CheckObjectionApp:{URLNames.BATCH_IMPORT_TESTCASES}")

@register.simple_tag
def url_clear_my_submission_cache():
    """清除我的提交缓存URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CLEAR_MY_SUBMISSION_CACHE}")

@register.simple_tag
def url_image_code():
    """图片验证码URL"""
    return reverse(f"CheckObjectionApp:{URLNames.IMAGE_CODE}")




# ===== 管理功能 =====
@register.simple_tag
def url_my_contests():
    """我的比赛记录URL"""
    return reverse(f"CheckObjectionApp:{URLNames.MY_CONTESTS}")

@register.simple_tag
def url_all_user_list():
    """所有比赛记录URL"""
    return reverse(f"CheckObjectionApp:{URLNames.ALL_USER_LIST}")

# ===== 带参数的通用标签 =====
@register.simple_tag
def url_submission_detail(submission_id):
    """提交详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.SUBMISSION_DETAIL}", args=[submission_id])

@register.simple_tag
def url_contest_submission_detail(submission_id):
    """比赛提交详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.SUBMISSION_DETAIL}", kwargs={'submission_id': submission_id})

@register.simple_tag
def url_contest_rank_detail(contest_id):
    """比赛排行详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_RANK_DETAIL}", args=[contest_id])

# ===== 提交api =====
@register.simple_tag
def url_proxy_submit_code():
    """提交代码api"""
    return reverse(f"CheckObjectionApp:{URLNames.PROXY_SUBMIT_CODE}")

@register.simple_tag
def url_proxy_submit_code_contest(contest_id):
    """提交内部算法比赛代码api"""
    return reverse(f"CheckObjectionApp:{URLNames.PROXY_SUBMIT_CODE_CONTEST}", args=[contest_id])

# ==== 比赛相关url  ====
@register.simple_tag
def url_contest_user_submissions(contest_id):
    """比赛用户提交列表URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_USER_SUBMISSIONS}", args=[contest_id])


