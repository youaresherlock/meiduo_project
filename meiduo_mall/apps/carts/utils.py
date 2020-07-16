import json
import base64
import pickle
from django_redis import get_redis_connection
"""
用户登录时,将cookie购物车数据合并到Redis购物车数据中
QQ登录和账号登录时都要进行购物车合并操作
"""


def merge_cart_cookie_to_redis(request, user, response):
    """合并cookie购物车到redis购物车"""
    cart_str = request.COOKIES.get('carts')
    if not cart_str:
        return response
    cart_dict = pickle.loads(base64.b64decode(cart_str))

    # 准备新的数据容器: {sku_id: count}, [selected_sku_id], [unselected_sku_id]
    new_cart_dict = {}  # 保存商品和数量
    new_add_selected = []  # 保存被勾选的商品编号
    new_remove_selected = []  # 保存未被勾选的商品编号
    for sku_id, cart_dict in cart_dict.items():
        new_cart_dict[sku_id] = cart_dict['count']

        if cart_dict['selected']:
            new_add_selected.append(sku_id)
        else:
            new_remove_selected.append(sku_id)

    redis_conn = get_redis_connection('carts')
    pl = redis_conn.pipeline()
    pl.hmset('carts_%s' % user.id, new_cart_dict)
    if new_add_selected:
        pl.sadd('selected_%s' % user.id, *new_add_selected)
    if new_remove_selected:
        pl.srem('selected_%s' % user.id, *new_remove_selected)
    pl.execute()

    # 清空cookie中购物车的数据
    response.delete_cookie('carts')

    return response


















