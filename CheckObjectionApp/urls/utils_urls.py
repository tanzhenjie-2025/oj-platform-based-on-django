from django.urls import path

from ..constants import URLNames
from ..views.utils import batch_import_testcases ,image_code ,clear_my_submission_cache

urlpatterns = [
    path('batch-import-testcases/', batch_import_testcases, name=URLNames.BATCH_IMPORT_TESTCASES),
# 生成验证码
    path('image_code',image_code,name='image_code'),
    # 删除缓存
    path('clear_my_submission_cache', clear_my_submission_cache, name='clear_my_submission_cache'),]