# 对openid进行序列化和反序列化
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadData
from django.conf import settings


def generate_access_token_openid(openid):
    """序列化openid
    """
    s = Serializer(settings.SECRET_KEY, 600)
    data = {'openid': openid}
    token = s.dumps(data)

    return token.decode()


def check_access_token_openid(access_token):
    """反序列化openid
    返回密文字符串: 将bytes类型的token转成字符串类型
    """
    s = Serializer(settings.SECRET_KEY, 600)
    try:
        data = s.loads(access_token)
    except BadData:
        return None
    openid = data.get('openid')

    return openid


# 用django的签名来加密openid
# from django.conf import settings
# from django.core import signing
#
#
# def generate_access_token_openid(openid):
#     data = {'openid': openid}
#     data_si = signing.dumps(key="salty", obj=data)
#     return data_si
#
#
# def check_access_token_openid(access_token):
#     data = signing.loads(key="salty", s=access_token)
#
#     return data.get('openid')


if __name__ == '__main__':
    openid = "hello"
    value = generate_access_token_openid(openid)
    print(value)
    value1 = check_access_token_openid(value)
    print(value1)














