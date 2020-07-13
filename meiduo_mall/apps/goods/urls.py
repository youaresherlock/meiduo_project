from django.urls import path, re_path
from .import views

urlpatterns = [
    path('list/<int:category_id>/skus/', views.ListView.as_view()),
    path('hot/<int:category_id>/', views.HotGoodsView.as_view()),
]

























