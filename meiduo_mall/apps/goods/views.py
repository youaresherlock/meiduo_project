from django.shortcuts import render
from django.views import View
from apps.contents.models import GoodsCategory
from apps.goods.models import SKU
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage
from apps.goods.utils import get_breadcrumb

# Create your views here.


class HotGoodsView(View):
    """热销排行
    GET /hot/(?P<category_id>\d+)/
    """
    def get(self, request, category_id):
        """
        提供指定分类下热销排行数据
        :param request:
        :param category_id:  第三级分类
        :return:  JSON
        """
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': 'category_id不存在'})

        # 查询指定分类下,未被下架的销量最好的前两款商品
        skus = SKU.objects.filter(category=category, is_launched=True).order_by('-sales')[:2]
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'hot_skus': hot_skus})


class ListView(View):
    """商品列表页
    GET /list/<int:category_id>/skus/
    """
    def get(self, request, category_id):
        """
        提供商品列表数据和面包屑导航数据
        :param request:
        :param category_id:  商品第三级分类
        :return:  JSON
        """
        page_num = request.GET.get('page')  # 当前用户想看的页码
        page_size = request.GET.get('page_size')  # 该页中想看的记录的个数
        ordering = request.GET.get('ordering')  # 排序字段

        # 校验category_id是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': 'category_id不存在'})
        # 查询指定分类下,未被下架的sku信息
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        # 分页查询
        # 1. 创建分页器对象 分页器对象=Paginator(要分页的查询集,每页记录个数)
        paginator = Paginator(skus, page_size)
        # 2. 获取指定页的数据
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return JsonResponse({'code': 400, 'errmsg': 'page数据出错'})

        total_page = paginator.num_pages
        breadcrumb = get_breadcrumb(category)
        sku_list = []
        for sku in page_skus:
            sku_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.id,
                'name': sku.name,
                'price': sku.price
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'list': sku_list,
            'count': total_page
        })

























