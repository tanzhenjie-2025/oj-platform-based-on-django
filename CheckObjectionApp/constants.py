# CheckObjectionApp/constants.py

class URLNames:
    """URL名称常量 - 按功能模块分类"""

    # 基础页面
    INDEX = "index"
    BASE = "base"
    NO_POWER = "no_power"

    # 用户认证
    REGISTER = "register"
    LOGIN = "login"
    LOGOUT = "logout"

    # 用户资料
    CHANGE_NAME = "change_name"
    CHANGE_PASSWORD = "change_password"

    # 题目相关
    TOPIC_DETAIL = "topic_detail"
    TOPIC_DESIGN = "topic_design"
    TOPIC_SEARCH = "topic_search"
    TOPIC_FILTER = "topic_filter"

    # 提交记录
    SUBMISSION_LIST = "submission_list"
    SUBMISSION_DETAIL = "submission_detail"
    MY_SUBMISSION_LIST = "my_submission_list"
    QUERY_SUBMISSION_LIST = "query_submission_list"
    QUERY_CONTEST_SUBMISSION_LIST = "query_contest_submission_list"
    MY_CONTEST_SUBMISSION_LIST = "my_contest_submission_list"
    CONTEST_MY_SUBMISSIONS = "contest_my_submissions"

    # 判题API
    PROXY_SUBMIT_CODE = "proxy_submit_code"
    PROXY_SUBMIT_CODE_CONTEST = "proxy_submit_code_contest"

    # 比赛相关
    CONTEST_LIST = "contest_list"
    CONTEST_DETAIL = "contest_detail"
    CONTEST_RANK = "contest_rank"
    CONTEST_REGISTER = "contest_register"
    CONTEST_SUBMIT_CODE = "contest_submit_code"


    # 排行榜
    RANKING_PAGE = "ranking_page"
    CONTEST_RANK_LIST = "contest_rank_list"
    CONTEST_RANK_DETAIL = "contest_rank_detail"

    # 工具功能
    IMAGE_CODE = "image_code"
    BATCH_IMPORT_TESTCASES = "batch_import_testcases"
    CLEAR_MY_SUBMISSION_CACHE = "clear_my_submission_cache"

    # 管理功能
    USER_LIST = "user_list"
    USER_CONTESTS = "user_contests"
    MY_CONTESTS = "my_contests"
    CONTEST_USER_SUBMISSIONS = "contest_user_submissions"

# 缓存配置
CACHE_TIMEOUT = {
    'SUBMISSION_LIST': 300,
    'SEARCH_RESULTS': 300,
    'CONTEST_SUBMISSIONS': 300,
    'USER_SUBMISSIONS': 300,
}

# 颜色配置
COLOR_CODES = {
    'SUCCESS': '#4caf50',  # 绿色
    'ERROR': '#f44336',  # 红色
    'WARNING': '#ff9800',  # 黄色
    'INFO': '#2196f3',
    'NEUTRAL': '#757575',
}

# 判题配置
JUDGE_CONFIG = {
    'DEFAULT_LANGUAGE_ID': 71,
    'TEST_RUN_TIMEOUT': 30,
    'SUBMISSION_TIMEOUT': 60,
}

# 验证码配置
CAPTCHA_CONFIG = {
    'SESSION_EXPIRY': 60, # 验证码session超时时间
    'WIDTH': 120,
    'HEIGHT': 30,
}

# 默认值配置
DEFAULT_VALUES = {
    'TESTCASE_SCORE': 10,
    'PAGINATE_BY': 20,
}