import os
from alipay import AliPay
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from apps.payment.models import Payment
from apps.orders.models import OrderInfo


class PaymentStatusView(View):
    """保存订单支付结果"""

    def put(self, request):
        # 获取前端传入的请求参数 request.GET返回的类型是QueryDict
        query_dict = request.GET
        data = query_dict.dict()
        # 获取并从请求参数中剔除signature
        signature = data.pop('sign')

        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        # 校验这个重定向是否是alipay重定向过来的
        success = alipay.verify(data, signature)
        if success:
            # 读取order_id
            order_id = data.get('out_trade_no')
            # 读取支付宝流水号
            trade_id = data.get('trade_no')
            # 保存Payment模型类数据
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )

            # 修改订单状态为待评价
            OrderInfo.objects.filter(order_id=order_id,
                                     status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).\
                update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])

            return JsonResponse({'code': 0,
                                 'errmsg': 'ok',
                                 'trade_id': trade_id})
        else:
            # 订单支付失败，重定向到我的订单
            return JsonResponse({'code': 400,
                                 'errmsg': '非法请求'})


class PaymentView(View):
    """订单支付功能"""

    def get(self,request, order_id):
        # 查询要支付的订单
        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'order_id有误'})

        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 生成登录支付宝连接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 响应登录支付宝连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'alipay_url': alipay_url})