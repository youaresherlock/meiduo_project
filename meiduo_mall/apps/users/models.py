from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    """自定义用户模型类
    为了追加mobile字段: 字符串类型, 最长11位,唯一不重复
    """
    mobile = models.CharField(max_length=11, unique=True)
    email_active = models.BooleanField(default=False, verbose_name="邮箱验证状态")

    class Meta:
        db_table = 'tb_users'


"""
什么时候需要迁移模型类?
1. 新建的模型类如果需要建表就必须要迁移的
2. 对模型类进行了修改 
"""























