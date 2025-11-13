# CheckObjectionApp/views/__init__.py
from .auth import CheckObjection_login, CheckObjection_register, CheckObjection_logout
from .base import redirect_root

# 确保导出所有需要的视图
__all__ = [
    'CheckObjection_login', 'CheckObjection_register', 'CheckObjection_logout',
    'redirect_root'
    # ... 其他视图
]