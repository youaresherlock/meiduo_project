from celery import Celery

# 创建Celery实例
celery_app = Celery('meiduo')

# 加载配置
celery_app.config_from_object('celery_tasks.config')
# 自动捕获tasks
celery_app.autodiscover_tasks(['celery_tasks.sms'])
















