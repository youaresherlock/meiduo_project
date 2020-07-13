from django.shortcuts import render
from django.views import View

from apps.contents.models import GoodsChannel, ContentCategory
# Create your views here.


class IndexView(View):
    """首页测试用的视图
    仅仅是用来编写首页数据的查询代码的，在这里做纯粹是为了方便走断点，追踪首页数据查询的逻辑
    如果首页数据查询完毕，该视图可以删除，把里面的代码放到静态化首页的工具方法中
    GET /
    """

    def get(self, request):
        # 准备商品分类数据的字典容器
        categories = {}

        # 查询所有的37个频道(一级分类)
        # GoodsChannel.objects.all().order_by('group_id', 'sequence')
        channels = GoodsChannel.objects.order_by('group_id', 'sequence')
        # 遍历所有的频道，取出每一个频道
        for channel in channels:
            # 通过频道数据关联的组取出对应的组号
            group_id = channel.group.id
            # 将group_id作为categories字段的key
            if group_id not in categories:
                categories[group_id] = {'channels': [], 'sub_cats': []}

            # 获取当前频道关联的一级分类（一个频道对应一个一级分类）
            cat1 = channel.category
            # 添加每组中对应的频道数据
            categories[group_id]['channels'].append({
                "id": channel.id,
                "name": cat1.name,
                "url": channel.url
            })

            # 添加每组中的二级和三级分类
            for cat2 in cat1.subs.all():
                # 使用二级分类查询关联的三级分类
                sub_cats = []
                for cat3 in cat2.subs.all():
                    sub_cats.append({
                        "id": cat3.id, # 三级分类ID
                        "name": cat3.name # 三级分类名字
                    })

                categories[group_id]['sub_cats'].append({
                    "id": cat2.id, # 二级分类ID
                    "name": cat2.name, # 二级分类名字
                    "sub_cats": sub_cats # 二级关联的三级分类
                })

        # 查询首页广告数据
        contents = {}
        # 先查询所有的广告种类，并遍历出每一种广告
        content_categories = ContentCategory.objects.all()
        for content_cat in content_categories:
            # 在遍历的过程中，取出每一种广告关联的广告内容
            # 一查多语法: 一方模型对象.一查多关联字段
            contents[content_cat.key] = content_cat.content_set.filter(status=True).order_by('sequence')

