import json
from decimal import Decimal
from django.views import View
from django.utils import timezone
from apps.goods.models import SKU
from django.db import transaction
from apps.orders.models import OrderGoods, OrderInfo
from django.shortcuts import render
from django.http import JsonResponse
from django_redis import get_redis_connection
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from apps.users.models import Address
# Create your views here.


class OrderCommitView(LoginRequiredJSONMixin, View):
    """订单提交
    POST /orders/commit/
    """
    def post(self, request):
        """保存订单信息和订单商品信息
        Django对于数据库的事务,默认每执行依据数据库操作,便会自动提交
        Django2.x默认事务隔离级别为读取已提交, MYSQL默认的事务隔离级别为可重复读
        """
        # 接受参数
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 校验参数
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code': 400, 'errmsg': '参数address_id有误'})

        # 判断pay_method是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': 400, 'errmsg': '参数pay_method有误'})
        user = request.user
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        # 显式的开启一个事务
        with transaction.atomic():
            # 创建事务保存点
            save_id = transaction.savepoint()
            # 保存订单基本信息,OrderInfo(一)
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=0,
                total_amount=Decimal('0'),
                freight=Decimal('10.00'),
                pay_method=pay_method,
                status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'] else
                OrderInfo.ORDER_STATUS_ENUM['UNSEND']
            )
            # 从redis读取购物车中被勾选的商品信息
            redis_conn = get_redis_connection('carts')
            redis_cart = redis_conn.hgetall('carts_%s' % user.id)
            redis_selected = redis_conn.smembers('selected_%s' % user.id)
            new_cart = {}
            for sku_id in redis_selected:
                new_cart[int(sku_id)] = int(redis_cart[sku_id])
            sku_ids = new_cart.keys()

            # 不能使用filter(id__in=sku_ids), filter返回的是查询集,而查询集有缓存,但是,在提交订单时,
            # 我们都是实时获取和更新库存和销量的, 此时库存和销量不能是缓存
            # 遍历购物车中被勾选的商品信息
            for sku_id in sku_ids:
                while True:
                    # 查询SKU信息
                    sku = SKU.objects.get(id=sku_id)

                    # 获取原始的库存和销量: 作为乐观锁的标记,标记数据操作前的初始状态
                    origin_stock = sku.stock
                    origin_sales = sku.sales

                    sku_count = new_cart[sku.id]
                    # 判断SKU库存
                    if sku_count > sku.stock:
                        # 出错就回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'code': 400, 'errmsg': '库存不足'})

                    # # SKU减少库存,增加销量
                    # sku.stock -= sku_count
                    # sku.sales += sku_count
                    # sku.save()
                    # 修改SPU销量

                    # 计算新的库存和销量
                    new_stock = origin_stock - sku.count
                    new_sales = origin_sales + sku.count

                    # 使用乐观锁操作SKU减少库存,增加销量
                    # update()的返回值,是影响的行数.如果冲突检测发现资源竞争,那么就不执行update,返回0.反之,就执行update,返回影响的行数
                    result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                    if result == 0:
                        continue

                    sku.spu.sales += sku_count
                    sku.spu.save()
                    # 保存订单商品信息 OrderGoods(多)
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=sku_count,
                        price=sku.price
                    )
                    # 保存商品订单中总价和总数量
                    order.total_count += sku_count
                    order.total_amount += sku_count * sku.price
                    break
            # 添加邮费和保存订单信息
            order.total_amount += order.freight
            order.save()

            # 清除保存点
            transaction.savepoint_commit(save_id)
        # 清除购物车中已结算的商品
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *redis_selected)
        pl.srem('selected_%s' % user.id, *redis_selected)
        pl.execute()
        # 响应提交订单结果
        return JsonResponse({'code': 0, 'errmsg': '下单成功', 'order_id': order.order_id})


class OrderSettlementView(View):
    """结算订单"""
    def get(self, request):
        """提供订单结算页面
        GET orders/settlement/
        """
        # 查询当前用户未被逻辑删除的地址
        address_model_list = request.user.addresses.filter(is_deleted=False)
        # 查询redis购物车中未被勾选的商品信息
        user_id = request.user.id
        redis_conn = get_redis_connection('carts')
        redis_cart = redis_conn.hgetall('carts_%s' % user_id)
        redis_selected = redis_conn.smembers('selected_%s' % user_id)
        new_cart = {}
        for sku_id in redis_selected:
            new_cart[int(sku_id)] = int(redis_cart[sku_id])
        # 构造响应的数据
        # 查询商品信息
        sku_list = []
        skus = SKU.objects.filter(id__in=new_cart.keys())
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'count': new_cart[sku.id],
                'price': sku.price
            })

        # 补充运费
        freight = Decimal('10.00')

        address_list = []
        for address in address_model_list:
            address_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })

        # 响应结果
        context = {
            'addresses': address_list,
            'skus': sku_list,
            'freight': freight
        }

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'context': context})




















