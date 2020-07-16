import re
import json
import logging
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import login
from QQLoginTool.QQtool import OAuthQQ
from apps.oauth.models import OAuthQQUser
from apps.users.models import User
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer
from apps.oauth.utils import generate_access_token_openid, check_access_token_openid
from apps.carts.utils import merge_cart_cookie_to_redis
# 日志输出器
logger = logging.getLogger('django')


# Create your views here.
class QQURLView(View):
    """QQ登录扫码链接
    GET /qq/authorization
    """

    def get(self, request):
        # client端的状态值
        state = request.GET.get('next', '/')
        # 创建OAuthQQ对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=state)
        # 调用提供QQ登录扫码链接的接口函数
        login_url = oauth.get_qq_url()
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'login_url': login_url})


class QQUserView(View):
    """用户扫码登录的回调处理
    GET /oauth_callback/
    """
    def get(self, request):
        """Oauth2.0认证"""
        code = request.GET.get('code')
        if not code:
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少code参数'})

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 根据code请求access_token
            access_token = oauth.get_access_token(code)
            # 根据access_token请求openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                'errmsg': 'oauth2.0认证失败'})

        # 使用openid去判断当前的QQ用户是否应绑定过美多商城的用户
        try:
            # 为了简单处理,我们将openid还给用户自己保存,将来在绑定用户时, 前端再传给我们即可
            oauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 没绑定
            # obj = TimedJsonWebSignatureSerializer(秘钥, 有效期(秒))
            access_token = generate_access_token_openid(openid)

            return JsonResponse({'code': 300, 'errmsg': '用户未绑定的', 'access_token': access_token})
        else:
            # 已绑定
            user = oauth_model.user
            # 实现状态保持
            login(request, user)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('username', user.username)

            # 合并购物车
            response = merge_cart_cookie_to_redis(request, request.user, response)
            return response

    def post(self, request):
        """美多商城用户绑定到openid"""
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')
        sms_code_client = json_dict.get('sms_code')
        access_token = json_dict.get('access_token')

        if not all([mobile, password, sms_code_client]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入正确的手机号码'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入8-20位的密码'})
        # 判断短信验证码是否一致
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        if sms_code_server is None:
            return JsonResponse({'code': 400,
                                 'errmsg': '验证码失效'})
        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code': 400,
                                 'errmsg': '输入的验证码有误'})
        openid = check_access_token_openid(access_token)
        if not openid:
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少openid'})

        # 判断手机号对应的用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果手机号对应的用户不存在,新建用户
            user = User.objects.create_user(username=mobile,
                                            password=password,
                                            mobile=mobile)
        else:
            # 如果手机号对应的用户已存在,校验密码
            if not user.check_password(password):
                return JsonResponse({'code': 400, 'errmsg': '密码有误'})
        # 用户和openid进行绑定
        # create_user(): 只有继承AbstractUser的用户模型类才能去调用的
        # create(): 凡是继承自Model的模型类都可以调用
        try:
            OAuthQQUser.objects.create(openid=openid, user=user)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '往数据库添加数据出错'})
        login(request, user)
        response = JsonResponse({'code': 0,
                                 'errmsg': 'ok'})
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)
        # 合并购物车
        response = merge_cart_cookie_to_redis(request, request.user, response)
        return response






















