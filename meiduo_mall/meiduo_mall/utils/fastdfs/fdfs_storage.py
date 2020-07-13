# 自定义文件存储类,提供文件下载的全路径
from django.core.files.storage import Storage
from django.conf import settings


class FastDFSStorage(Storage):
    """自定义文件存储类"""
    def _open(name, mode='rb'):
        """
        打开文件时自动调用的
        :param name: 要打开的文件和名字
        :param mode: 打开文件的模式
        :return:
        """
        pass

    def _save(name, content):
        """
        保存文件时自动调用
        :param name:  要保存文件的名字
        :param content:  要保存文件的内容
        :return:
        """
        pass

    def url(self, name):
        """返回文件下载的全路径"""
        return settings.FDFS_URL + name
























