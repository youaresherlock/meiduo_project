import re
import json
import logging
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
from apps.users.models import User
from django_redis import get_redis_connection
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from apps.users.utils import generate_email_verify_url
from apps.users.utils import check_email_verify_url
# Create your views here.

# 日志输出器
logger = logging.getLogger('django')


class CreateAddressView(LoginRequiredJSONMixin, View):
    """新增地址
    POST /address/create/
    """
    def post(self, request):
        """实现新增地址的逻辑"""
        pass


class EmailActiveView(View):
    """认证激活邮箱
    PUT /emails/verification/
    """
    def put(self, request):
        """实现邮箱验证逻辑"""
        token = request.GET.get('token')
        if not token:
            return JsonResponse({'code': 400, 'errmsg': '缺少token'})

        user = check_email_verify_url(token)
        if not user:
            return JsonResponse({'code': 400, 'errmsg': '无效的token'})

        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'errmsg': '激活邮箱失败'})

        return JsonResponse({'code': 0, 'errmsg': 'ok'})


class EmailView(View):
    """添加邮箱
    PUT /emails/
    """
    def put(self, request):
        """实现添加邮箱的逻辑"""
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        if not email:
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式错误'})
        
        try:
            request.user.email = email 
            request.user.save() 
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 
                                 'errmsg': '添加邮箱失败'})
        email = '<' + email + '>'
        verify_url = generate_email_verify_url(request.user)
        # 发送邮箱的验证激活邮件
        send_verify_email.delay(email, verify_url)
        
        return JsonResponse({'code': 0, 
                             'errmsg': '添加邮箱成功'})


class UserInfoView(LoginRequiredJSONMixin, View):
    """用户中心
    GET /info/
    """

    def get(self, request):
        """实现用户基本信息展示
        由于我们在该接口中,判断了用户是否是登录用户
        所以能够进入到该接口的请求,一定是登录用户发送的
        所以request.user里面获取的用户信息一定是当前登录的用户信息
        如果不理解查看AuthenticationMiddleware的源码,里面都封装好的逻辑
        重要的技巧:
            如果该接口只有登录用户可以访问,那么在接口内部可以直接使用request.user
        :param request:
        :return:
        """
        # username = request.COOKIES.get('username')
        # print(username)
        # if not username:
        #     return JsonResponse({'code': 400, 'errmsg': '用户名不存在'})
        # try:
        #     user = User.objects.get(username=username)
        # except Exception:
        #     return JsonResponse({'code': 400, 'errmsg': '用户不存在'})

        data_dict = {
            'code': 0,
            'errmsg': 'ok',
            'info_data': {
                'username': request.user.username,
                'mobile': request.user.mobile,
                'email': request.user.email,
                'email_active': request.user.email_active
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

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        # 记住登录用来指定状态保持的时间周期
        if remembered:
            # 如果记住, 设置为两周有效
            request.session.set_expiry(None)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        else:
            # 如果没有记住, 关闭立刻失效
            request.session.set_expiry(0)
            response.set_cookie('username', user.username)
        # 响应结果
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
        # redis_conn = get_redis_connection('verify_code')
        # sms_code_server = redis_conn.get('sms_%s' % mobile)
        # if not sms_code_server:
        #     return JsonResponse({'code': 400,
        #                          'errmsg': '短信验证码过期'})
        # if sms_code_client != sms_code_server.decode():
        #     return JsonResponse({'code': 400,
        #                          'errmsg': '验证码有误'})
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

































