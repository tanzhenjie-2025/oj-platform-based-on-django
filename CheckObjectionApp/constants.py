# CheckObjectionApp/constants.py

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