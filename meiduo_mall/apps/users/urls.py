from django.urls import path, re_path
from .import views

urlpatterns = [
    # re_path('^/usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    # path('usernames/<'匹配用户名的路由转换器:变量'>/count/', views.UsernameCountView.as_view()),
    path('usernames/<username:username>/count/', views.UsernameCountView.as_view()),
    path('mobiles/<mobile:mobile>/count/', views.MobileCountView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('info/', views.UserInfoView.as_view()),
    path('emails/', views.EmailView.as_view()),
    path('emails/verification/', views.EmailActiveView.as_view()),
]

























