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


class CartsSelectAllView(View):
    """购物车全选"""
    def put(self, request):
        """实现购物车全选"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected', True)
        # 校验参数
        if not isinstance(selected, bool):
            return JsonResponse({'code': 400, 'errmsg': '参数selected有误'})
        # 判断用户是否登录
        if request.user.is_authenticated:
            # 如果用户已登录,全选redis购物车
            redis_conn = get_redis_connection('carts')
            # 读取hash中所有的sku_id {b'sku_id1': b'count1',...}
            redis_cart = redis_conn.hgetall('carts_%s' % request.user.id)
            # 读取字典中所有的sku_id [b'sku_id1', b'sku_id2']
            sku_ids = redis_cart.keys()
            if selected:
                # 设置全选
                redis_conn.sadd('selected_%s' % request.user.id, *sku_ids)
            else:
                # 取消全选
                redis_conn.srem('selected_%s' % request.user.id, *sku_ids)
            return JsonResponse({'code': 0, 'errmsg': '全选购物车成功'})
        else:
            # 如果用户未登录,全选cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            response = JsonResponse({'code': 0, 'errmsg': '全选购物车成功'})
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
                for sku_id in cart_dict.keys():
                    cart_dict[sku_id]['selected'] = selected

                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cart_data)

            return response


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
            # 数据->pickle.dumps->bytes->bs64encode()->bytes->decode->string->cookie
            # cookie->string->encode->bytes->bs64decode()->bytes->pickle.loads()->数据
            # 如果用户未登录,新增cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # cart_str_bytes = cart_str.encode()
                # cart_dict_bytes = base64.b64.decode(cart_str_bytes)
                # cart_dict = pickle.loads(cart_dict_bytes)
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                cart_dict = {}
            if sku_id in cart_dict:
                # 如果要添加的商品在购物车已存在，累加数量
                count += cart_dict[sku_id]['count']
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = JsonResponse({'code': 0, 'errmsg': '添加购物车成功'})
            response.set_cookie('carts', cart_data)
            return response

    def get(self, request):
        """展示购物车"""
        if request.user.is_authenticated:
            # 用户已登录,查询redis购物车
            redis_conn = get_redis_connection('carts')
            # hgetall(name) return a python dict of the hash's name/value pairs
            # 获取redis中的购物车数据
            # {b'sku_id1': b'count1', ...}
            redis_cart = redis_conn.hgetall('carts_%s' % request.user.id)
            # 获取redis中的选中状态
            # smembers(name) return all members of the set
            # [b'sku_id1']
            redis_selected = redis_conn.smembers('selected_%s' % request.user.id)
            # 将redis购物车转成可操作的对象: 将redis_cart和redis_selected里面的数据合并到一个购物车字典中
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected
                }
        else:
            # 用户未登录,查询cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                 cart_dict = pickle.loads(base64.b64decode(cookie_cart))
            else:
                cart_dict = {}
        sku_ids = cart_dict.keys()
        sku_model_list = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in sku_model_list:
            cart_dict.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'count': cart_dict[sku.id]['count'],
                'amount': sku.price * cart_dict[sku.id]['count']
            })

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': cart_skus})

    def put(self, request):
        """修改购物车
        在购物车页面修改购物车使用局部刷新的效果"""
        # 接受参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        try:
            sku = SKU.objcets.get(id=sku_id)
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
        if request.user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hset('carts_%s' % request.user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % request.user.id, sku_id)
            else:
                pl.srem('selected_%s' % request.user.id, sku_id)
            pl.execute()

            cart_sku = {
                'id': sku.id,
                'count': count,
                'selected': selected
            }

            return JsonResponse({'code': 0, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str))
            else:
                cart_dict = {}

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected
            }
            response = JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_sku': cart_sku})
            response.set_cookie('carts', cookie_cart_str)
            return response

    def delete(self, request):
        """删除购物车"""
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数sku_id错误'})

        if request.user.is_authenticated:
            # 如果用户已登录,删除redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hdel('carts_%s' % request.user.id, sku_id)
            pl.srem('selected_%s' % request.user.id, sku_id)
            pl.execute()

            return JsonResponse({'code': 0, 'errmsg': '删除购物车成功'})
        else:
            # 如果用户未登录,删除cookie购物车
            cart_str = request.COOKIES.get('carts')
            response = JsonResponse({'code': 0, 'errmsg': '删除购物车成功'})
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str))
                # 删除购物车字典中的key,只能删除存在的key,如果删除了不存在的key会抛出异常
                if sku_id in cart_dict:
                    del cart_dict[sku_id]
                cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cookie_cart_str)
            return response






























