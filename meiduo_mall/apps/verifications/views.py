from django.shortcuts import render
from django.shortcuts import  HttpResponse
from django.views import View
from django_redis import get_redis_connection
from apps.verifications.libs.captcha.captcha import captcha
# Create your views here.


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
        # 3. 保存到redis, 图形验证码必须要有有效期 300s
        redis_conn.setex('img_%s' % uuid, 300, text)
        # 保存图形验证码
        return HttpResponse(image, content_type="image/jpg")















