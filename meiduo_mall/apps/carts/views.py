import json
import base64
import pickle
import logging
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from apps.goods.models import SKU
from django_redis import get_redis_connection

# Create your views here.


logger = logging.getLogger('django')


class CartsView(View):
    """购物车管理: 增删改查
    增: POST /carts/
    """
    def post(self, request):
        """实现新增购物车的逻辑"""
        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        try:
            SKU.objcets.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数sku_id错误'})
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': 'count有误'})
        # 判断selected是否为bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400, 'errmsg': 'selected有误'})
        # 实现核心逻辑: 登录用户和未登录用户新增购物车
        if request.user.is_authenticated:
            # 如果用户已登录,新增redis购物车
            # hash: carts_user_id: {sku_id1: count1, sku_id2: count2, ...}
            # set: selected_user_id: [sku_id1]
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 操作hash,增量存储sku_id和count
            pl.hincrby('carts_%s' % request.user.id, sku_id, count)
            # 操作set,如果selected为True,需要将sku_id添加到set
            if selected:
                pl.sadd('selected_%s' % request.user.id, sku_id)
            pl.execute()

            return JsonResponse({'code': 0, 'errmsg': '添加购物车成功'})
        else:
            # 如果用户未登录,新增cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                cart_dict = {}
            if sku_id in cart_dict:
                count += cart_dict[sku_id]['count']
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({'code': 0, 'errmsg': '添加购物车成功'})
            response.set_cookie('carts', cart_data)
            return response

































