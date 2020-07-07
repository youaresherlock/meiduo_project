from django.shortcuts import render
from django.core.cache import cache
from django.views import View
from apps.areas.models import Area
from django.http import JsonResponse

# Create your views here.


class SubAreasView(View):
    """获取父级下的所有市区
    GET /areas/<int:parentid>/
    """
    def get(self, request, parentid):
        sub_data = cache.get('sub_area_%s' % parentid)
        if not sub_data:
            parent_area = Area.objects.get(id=parentid)
            sub_model_list = parent_area.subs.all()
            sub_list = []
            for sub_model in sub_model_list:
                sub_list.append({'id': sub_model.id,
                                 'name': sub_model.name})
            sub_data = {
                'id': parent_area.id,
                'name': parent_area.name,
                'subs': sub_list
            }
            cache.set('sub_area_%s' % parentid, sub_data, 3600)

        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'sub_data': sub_data})


class ProvinceAreasView(View):
    """查询省份数据
    GET /areas/
    """
    def get(self, request):
        """实现查询省份数据的逻辑
        省份数据没有父级
        Area.objects.get() 只能查一个
        Area.objects.all() 查询所有的省市区
        """
        province_list = cache.get('province_list')
        if not province_list:
            province_model_list = Area.objects.filter(parent=None)
            # 将查询集模型列表转字典数据
            province_list = []
            for province_model in province_model_list:
                province_dict = {
                    'id': province_model.id,
                    'name': province_model.name,
                }
                province_list.append(province_dict)
            cache.set('province_list', province_list, 3600)
        # JsonResponse不识别模型数据,只识别字典、列表、字典列表
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'province_list': province_list})


