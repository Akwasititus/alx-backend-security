from django.http import JsonResponse
from .models import RequestLog

def home(request):
    return JsonResponse({
        'message': 'IP Tracking Project with Geolocation is working!',
        'total_logs': RequestLog.objects.count(),
        'your_ip': request.META.get('REMOTE_ADDR')
    })

def view_logs(request):
    logs = RequestLog.objects.all()[:10]  # Last 10 logs
    log_data = [
        {
            'ip': log.ip_address, 
            'path': log.path, 
            'timestamp': str(log.timestamp),
            'country': log.country,
            'city': log.city,
            'region': log.region,
            'location': f"{log.city}, {log.country}" if log.city and log.country else "Unknown"
        }
        for log in logs
    ]
    return JsonResponse({'recent_logs': log_data})

def geolocation_stats(request):
    """View to show geolocation statistics"""
    stats = {
        'total_requests': RequestLog.objects.count(),
        'countries': list(RequestLog.objects.exclude(country__isnull=True)
                          .values('country')
                          .distinct()
                          .count()),
        'cities': list(RequestLog.objects.exclude(city__isnull=True)
                       .values('city', 'country')
                       .distinct()),
        'requests_by_country': list(RequestLog.objects.exclude(country__isnull=True)
                                   .values('country')
                                   .annotate(count=models.Count('id'))
                                   .order_by('-count')[:10])
    }
    return JsonResponse(stats)