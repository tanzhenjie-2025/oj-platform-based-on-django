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
def url_detail(topic_id):
    """题目详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.DETAIL}", args=[topic_id])

@register.simple_tag
def url_design():
    """题目设计URL"""
    return reverse(f"CheckObjectionApp:{URLNames.DESIGN}")

# ===== 提交记录 =====
@register.simple_tag
def url_show():
    """查看全部提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.SUBMISSION_LIST}")

@register.simple_tag
def url_my_submissions():
    """我的提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.MY_SUBMISSION_LIST}")

@register.simple_tag
def url_my_contest_submissions():
    """我的比赛提交URL"""
    return reverse(f"CheckObjectionApp:{URLNames.MY_CONTEST_SUBMISSION_LIST}")

# ===== 比赛相关 =====
@register.simple_tag
def url_contests():
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
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_SUBMIT_CODE}", args=[contest_id, contest_topic_id])

# ===== 排行榜 =====
@register.simple_tag
def url_ranking():
    """排行榜URL"""
    return reverse(f"CheckObjectionApp:{URLNames.RANKING_PAGE}")

@register.simple_tag
def url_contest_rank_list():
    """比赛排行列表URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_RANK_LIST}")

# ===== 工具功能 =====
@register.simple_tag
def url_batch_import():
    """批量导入测试案例URL"""
    return reverse(f"CheckObjectionApp:{URLNames.BATCH_IMPORT_TESTCASES}")

# ===== 管理功能 =====
@register.simple_tag
def url_my_contests():
    """我的比赛记录URL"""
    return reverse(f"CheckObjectionApp:{URLNames.MY_CONTESTS}")

# ===== 带参数的通用标签 =====
@register.simple_tag
def url_submission_detail(submission_id):
    """提交详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.SUBMISSION_DETAIL}", args=[submission_id])

@register.simple_tag
def url_contest_rank_detail(contest_id):
    """比赛排行详情URL"""
    return reverse(f"CheckObjectionApp:{URLNames.CONTEST_RANK_DETAIL}", args=[contest_id])