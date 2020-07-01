import random
import logging
from django.http import HttpResponse, JsonResponse
from django.views import View
from django_redis import get_redis_connection
from apps.verifications.libs.captcha.captcha import captcha
from celery_tasks.sms.tasks import ccp_send_sms_code
# Create your views here.

# 日志输出器
logger = logging.getLogger('django')


class SMSCodeView(View):
    """短信验证码
    GET /sms_codes/18502923577/?image_code=NJEr&image_code_id=42fd66f0-2494-42b9-846e-24f6762922ba
    """

    def get(self, request, mobile):
        redis_conn = get_redis_connection('verify_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 如果数据存在,则说明频繁发送
        if send_flag:
            return JsonResponse({'code': 400,
                                 'errmsg': '发送短信过于频繁'})
        # 1.接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.校验参数
        if not all([image_code_client, uuid]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})
        # 3. 提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({'code': 400,
                                 'errmsg': '图形验证码失效'})
        # 4. 删除图形验证码, 避免恶意测试图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 5. 对比图形验证码
        # bytes转字符串
        image_code_server = image_code_server.decode()
        if image_code_client.lower() != image_code_server.lower():
            return JsonResponse({'code': 400,
                                 'errmsg': '输入图形验证码有误'})
        # 生成短信验证码
        # %06d表示对应的整形数如果小于6位,则在前面补0
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)
        # 保存短信验证码
        # redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        # 使用pipeline管道
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, 300, sms_code)
        pl.setex('send_flag_%s' % mobile, 60, 1)
        pl.execute()

        # 异步发送短信验证码 发送短信和响应分开执行
        ccp_send_sms_code.delay(mobile, sms_code)
        return JsonResponse({'code': 0,
                             'errmsg': '发送短信成功'})


class ImageCodeView(View):
    """图形验证
    GET http://www.meiduo.site:8000/image_codes/uuid/
    """

    def get(self, request, uuid):
        """实现图形验证码逻辑
        uuid前端加载页面时生成保存到用户的浏览器中
        """
        # 接受参数
        # 校验参数
        # 1. 生成图形验证码
        text, image = captcha.generate_captcha()

        # 2. 链接redis,获取链接对象
        redis_conn = get_redis_connection('verify_code')
        # 3. 保存到redis, 图形验证码必须要有,有效期 300s
        redis_conn.setex('img_%s' % uuid, 300, text)
        # 保存图形验证码
        return HttpResponse(image, content_type="image/jpg")















