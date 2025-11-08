from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logs/', views.view_logs, name='view_logs'),
]