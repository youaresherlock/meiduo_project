import logging
from django.conf import settings
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import login
from QQLoginTool.QQtool import OAuthQQ
from apps.oauth.models import OAuthQQUser

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
        print(state)
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
            oauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 没绑定
            pass
        else:
            # 已绑定
            user = oauth_model.user
            # 实现状态保持
            login(request, user)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('username', user.username)
            return response






















