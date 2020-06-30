from django.urls import path
from . import views

urlpatterns = [
    #  路由转换器uuid:变量名uuid
    path('image_codes/<uuid:uuid>/', views.ImageCodeView.as_view()),
    # GET /sms_codes/18502923577/?image_code=NJEr&image_code_id=42fd66f0-2494-42b9-846e-24f6762922ba
    path('sms_codes/<mobile:mobile>/', views.SMSCodeView.as_view()),
]





















