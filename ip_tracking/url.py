from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logs/', views.view_logs, name='view_logs'),
    path('stats/', views.geolocation_stats, name='geolocation_stats'),  # Add this

        # Rate limited endpoints
    path('login/', views.login_view, name='login'),
    path('sensitive/', views.sensitive_operation, name='sensitive_operation'),
    path('api/', views.api_endpoint, name='api_endpoint'),
    path('multi/', views.multi_method_view, name='multi_method_view'),

    path('auth-sensitive/', views.authenticated_sensitive_view, name='auth_sensitive'),
    path('high-api/', views.high_limit_api, name='high_api'),
    path('low-sensitive/', views.low_limit_sensitive, name='low_sensitive'),

]