from django.urls import path
from . import views

urlpatterns = [
    path('carts/', views.CartsView.as_view()),
]