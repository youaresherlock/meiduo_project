from django.db import models
from django.contrib.auth.models import AbstractUser
from meiduo_mall.utils.models import BaseModel
# Create your models here.


class User(AbstractUser):
    """自定义用户模型类
    为了追加mobile字段: 字符串类型, 最长11位,唯一不重复
    """
    mobile = models.CharField(max_length=11, unique=True)
    email_active = models.BooleanField(default=False, verbose_name="邮箱验证状态")
    # 新增
    # null如果为True,表示允许为空, blank如果为True,则该字段允许为空白
    default_address = models.ForeignKey('Address',
                                        related_name='users',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'


"""
什么时候需要迁移模型类?
1. 新建的模型类如果需要建表就必须要迁移的
2. 对模型类进行了修改 
"""


# 增加地址的模型类, 放到User模型类的下方:
class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             verbose_name='用户')

    province = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='province_addresses',
                                 verbose_name='省')

    city = models.ForeignKey('areas.Area',
                             on_delete=models.PROTECT,
                             related_name='city_addresses',
                             verbose_name='市')

    district = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='district_addresses',
                                 verbose_name='区')

    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20,
                           null=True,
                           blank=True,
                           default='',
                           verbose_name='固定电话')

    email = models.CharField(max_length=30,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='电子邮箱')

    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        # 根据根据更新时间降序
        ordering = ['-update_time']






















