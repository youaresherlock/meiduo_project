from django.db import models

# Create your models here.


class Area(models.Model):
    """
    行政区划
    """
    # 创建 name 字段, 用户保存名称
    name = models.CharField(max_length=20,
                            verbose_name='名称')
    # 自关联字段 parent
    # 第一个参数是 self : parent关联自己.
    # on_delete=models.SET_NULL:  如果省删掉了,省内其他的信息为 NULL
    # related_name='subs': 设置之后
    # 我们就这样调用获取市: area.area_set.all() ==> area.subs.all()
    # null=True, 允许为空,默认是false
    parent = models.ForeignKey('self',
                               on_delete=models.SET_NULL,
                               related_name='subs',
                               null=True,
                               blank=True,
                               verbose_name='上级行政区划')

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '行政区划'
        verbose_name_plural = '行政区划'

    def __str__(self):
        return self.name


"""
自关联: 
    表中的某一列,关联了这个表中的另外一列,但是他们的业务逻辑含义是不一样的.
自关联的表就是将一对多的表的关系和数据合并到一张表 
结论: 自关联的查询也就是一查多和多查一的套路 
    省查询市(一查多):
        模型对象.模型类名小写_set 
    市查询省(多查一):
        模型对象.外键属性名 
自定义一查多的关联字段
    为什么要自定义一查多的关联字段?
    因为,有可能出现模型类的类名特别长的情况,那么使用默认的一查多的关联字段时,
代码不够简洁, 我们可以自定义一查多的关联字段 
"""



















