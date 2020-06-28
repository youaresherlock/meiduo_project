from django.urls import path
from . import views

urlpatterns = [
    #  路由转换器uuid:变量名uuid
    path('image_codes/<uuid:uuid>/', views.ImageCodeView.as_view()),
]





















