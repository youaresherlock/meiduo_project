from django.urls import path
from . import views

urlpatterns = [
    path('carts/', views.CartsView.as_view()),
    path('carts/selection/', views.CartsSelectAllView.as_view()),
    # 展示商品页面简单购物车
    path('carts/simple/', views.CartsSimpleView.as_view()),
]