from django.db import models
"""
DateTimeField: datetime()
DateField: date()
TimeField: time() 
"""


class BaseModel(models.Model):
    """为模型类补充字段"""

    # 创建时间: auto_now_add只在数据添加的时候,记录时间
    create_time = models.DateTimeField(auto_now_add=True,
                                       verbose_name="创建时间")
    # 更新时间: auto_now数据添加和更新的时候, 记录时间
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name="更新时间")

    class Meta:
        # 说明是抽象模型类(抽象模型类不会创建表)
        abstract = True