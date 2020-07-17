from django.urls import path
from .import views

urlpatterns = [
    path('payment/<int:order_id>/', views.PaymentView.as_view()),
    path('payment/status/', views.PaymentStatusView.as_view()),
]