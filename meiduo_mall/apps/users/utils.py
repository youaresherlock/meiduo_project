from django.conf import settings
from apps.users.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadData


def generate_email_verify_url(user):
    s = Serializer(settings.SECRET_KEY, 3600 * 24)
    data = {'user_id': user.id, 'email': user.email}
    # 加密生成token值,这个值是bytes类型,所以解码为str
    token = s.dumps(data).decode()
    verify_url = settings.EMAIL_VERIFY_URL + token

    return verify_url


def check_email_verify_url(token):
    """反序列化用户信息密文"""
    s = Serializer(settings.SECRET_KEY, 3600 * 24)
    try:
        data = s.loads(token)
    except BadData:
        return None
    else:
        # 提取用户信息
        user_id = data.get('user_id')
        email = data.get('email')
    try:
        user = User.objects.get(id=user_id, email=email)
    except Exception as e:
        return None
    else:
        return user


















