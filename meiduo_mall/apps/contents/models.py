from django.db import models

from meiduo_mall.utils.models import BaseModel
# Create your models here.


class GoodsCategory(BaseModel):
    """商品类别"""
    name = models.CharField(max_length=10, verbose_name='名称')
    parent = models.ForeignKey('self', related_name='subs', null=True, blank=True, on_delete=models.CASCADE, verbose_name='父类别')

    class Meta:
        db_table = 'tb_goods_category'

    def __str__(self):
        return self.name


class GoodsChannelGroup(BaseModel):
    """商品频道组"""
    name = models.CharField(max_length=20, verbose_name='频道组名')

    class Meta:
        db_table = 'tb_channel_group'

    def __str__(self):
        return self.name


class GoodsChannel(BaseModel):
    """商品频道"""
    group = models.ForeignKey(GoodsChannelGroup, on_delete=models.CASCADE, verbose_name='频道组名')
    category = models.ForeignKey(GoodsCategory, on_delete=models.CASCADE, verbose_name='顶级商品类别')
    url = models.CharField(max_length=50, verbose_name='频道页面链接')
    sequence = models.IntegerField(verbose_name='组内顺序')

    class Meta:
        db_table = 'tb_goods_channel'

    def __str__(self):
        return self.category.name


class ContentCategory(BaseModel):
    """广告内容类别"""
    name = models.CharField(max_length=50, verbose_name='名称')
    key = models.CharField(max_length=50, verbose_name='类别键名')

    class Meta:
        db_table = 'tb_content_category'

    def __str__(self):
        return self.name


class Content(BaseModel):
    """广告内容"""
    category = models.ForeignKey(ContentCategory, on_delete=models.PROTECT, verbose_name='类别')
    title = models.CharField(max_length=100, verbose_name='标题')
    url = models.CharField(max_length=300, verbose_name='内容链接')
    image = models.ImageField(null=True, blank=True, verbose_name='图片')
    text = models.TextField(null=True, blank=True, verbose_name='内容')
    sequence = models.IntegerField(verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='是否展示')

    class Meta:
        db_table = 'tb_content'

    def __str__(self):
        return self.category.name + ': ' + self.title
