import os
from celery import Celery

# 在创建celery实例之前,把Django的配置模块加载到运行环境中
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 创建Celery实例
celery_app = Celery('meiduo')

# 加载配置
celery_app.config_from_object('celery_tasks.config')
# 自动捕获tasks
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])
















