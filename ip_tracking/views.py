from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .models import RequestLog

def home(request):
    return JsonResponse({
        'message': 'IP Tracking Project is working!',
        'total_logs': RequestLog.objects.count()
    })

def view_logs(request):
    logs = RequestLog.objects.all()[:10]  # Last 10 logs
    log_data = [
        {'ip': log.ip_address, 'path': log.path, 'timestamp': str(log.timestamp)}
        for log in logs
    ]
    return JsonResponse({'recent_logs': log_data})