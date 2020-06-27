import logging
from django.shortcuts import render
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

































