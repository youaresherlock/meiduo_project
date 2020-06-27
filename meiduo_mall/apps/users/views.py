import re
import json
import logging
from django.shortcuts import render
from django.contrib.auth import login
from django.http import JsonResponse
from django.views import View
from apps.users.models import User

# Create your views here.

# 日志输出器
logger = logging.getLogger('django')


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
        # 实现核心逻辑: 保存注册数据到用户数据表
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '保存到数据库出错'})
        # 实现状态保持
        login(request, user)

        return JsonResponse({'code': 0,
                             'errmsg': 'ok'})

        # 实现状态保持, 注册成功立即登录成功
        # 响应结果






























