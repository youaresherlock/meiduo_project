import re
import json
import logging
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views import View
from apps.users.models import User
from django_redis import get_redis_connection
from meiduo_mall.utils.views import LoginRequiredJSONMixin
# Create your views here.

# 日志输出器
logger = logging.getLogger('django')


class UserInfoView(LoginRequiredJSONMixin, View):
    """用户中心
    GET /info/
    """

    def get(self, request):
        data_dict = {
            'code': 0,
            'errmsg': 'ok',
            'info_data': {
                'username': '',
                'mobile': '',
                'email': '',
                'email_active': ''
            }
        }
        return JsonResponse(data_dict)


class LogoutView(View):
    """定义退出登录的接口"""

    def delete(self, request):
        """实现退出登录逻辑"""
        # 清理session
        logout(request)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.delete_cookie('username')
        return response


class LoginView(View):
    """用户登录
    GET /login/
    """

    def post(self, request):
        """实现用户登录功能"""
        json_dict = json.loads(request.body.decode())
        account = json_dict.get('username')
        password = json_dict.get('password')
        remembered = json_dict.get('remembered')
        # 校验参数
        if not all([account, password]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        # if not re.math(r'^[a-zA-Z0-9_-]{5,20}$', username):
        #     return JsonResponse({'code': 400, 'errmsg': '参数username格式错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400, 'errmsg': '参数password格式错误'})

        # 实现多账号登录
        if re.match(r'^1[3-9]\d{9}$', account):
            User.USERNAME_FIELD = "mobile"
        else:
            User.USERNAME_FIELD = "username"
        """
        认证登录用户核心思想: 先使用用户名作为条件去用户表查询该记录是否存在,如果该用户名对应的记录存在,再去校验密码是否正确
        Django的用户认证系统默认已经封装好了这个逻辑
        """
        user = authenticate(request=request, username=account, password=password)
        if user is None:
            return JsonResponse({'code': 400, 'errmsg': '用户名或者密码错误'})
        # 实现状态保持
        login(request, user)

        # 记住登录用来指定状态保持的时间周期
        if remembered:
            # 如果记住, 设置为两周有效
            request.session.set_expiry(None)
        else:
            # 如果没有记住, 关闭立刻失效
            request.session.set_expiry(0)
        # 响应结果
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        return response


class UsernameCountView(View):
    """判断用户名是否重复注册
    GET /usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/
    """

    def get(self, request, username):
        """查询用户名对应的记录的个数"""
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '访问数据库失败'
            })

        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count': count})


class MobileCountView(View):

    def get(self, request, mobile):
        """判断手机号是否重复注册"""
        # 1.查询mobile在mysql中的个数
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '查询数据库出错'})

        # 2.返回结果(json)
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count': count})


class RegisterView(View):
    """用户注册
    POST http://www.meiduo.site:8000/register/
    """

    def post(self, request):
        """实现注册逻辑"""
        # 接受参数,请求体中的json数据
        json_bytes = request.body
        json_str = json_bytes.decode()
        json_dict = json.loads(json_str)
        # 提取参数
        username = json_dict.get('username')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        mobile = json_dict.get('mobile')
        # 提取短信验证码参数
        sms_code_client = json_dict.get('sms_code')
        allow = json_dict.get('allow')
        # 校验参数
        # 判断是否缺少必传参数
        # all() 判断给定的可迭代参数iterable中的所有元素是否都为True
        if not all([username, password, password2, mobile, allow]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})
        # 3.username检验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400,
                                      'errmsg': 'username格式有误'})

        # 4.password检验
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400,
                                      'errmsg': 'password格式有误'})

        # 5.password2 和 password
        if password != password2:
            return JsonResponse({'code': 400,
                                      'errmsg': '两次输入不对'})
        # 6.mobile检验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                      'errmsg': 'mobile格式有误'})
        # 7.allow检验
        if not allow:
            return JsonResponse({'code': 400,
                                      'errmsg': 'allow格式有误'})
        # 从redis取出短信验证码并判断是否过期,然后与用户输入的验证码进行对比
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return JsonResponse({'code': 400,
                                 'errmsg': '短信验证码过期'})
        if sms_code_client != sms_code_server.decode():
            return JsonResponse({'code': 400,
                                 'errmsg': '验证码有误'})
        # 实现核心逻辑: 保存注册数据到用户数据表
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '注册失败'})
        # 实现状态保持
        login(request, user)

        response = JsonResponse({'code': 0,
                             'errmsg': '注册成功'})

        # 在注册成功之后,将用户名写入到cookie,将来会在页面右上角展示
        response.set_cookie('username', user.username, max_age=14*24*3600)

        return response

































