from django.http import HttpResponseForbidden
from .models import RequestLog, BlockedIP

class IPLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if IP is blocked BEFORE processing the request
        if self.is_ip_blocked(request):
            return HttpResponseForbidden("IP address blocked")
        
        # Process the request and get the response
        response = self.get_response(request)
        
        # Log the request details after getting the response
        self.log_request(request)
        
        return response
    
    def is_ip_blocked(self, request):
        """Check if the client IP is in the blocked list"""
        try:
            ip_address = self.get_client_ip(request)
            return BlockedIP.objects.filter(ip_address=ip_address).exists()
        except Exception as e:
            # If there's an error checking, allow the request (fail open)
            print(f"Error checking IP block: {e}")
            return False
    
    def log_request(self, request):
        """Extract and log IP address, timestamp, and path"""
        try:
            # Get client IP address (handles proxies)
            ip_address = self.get_client_ip(request)
            
            # Create and save the log entry
            RequestLog.objects.create(
                ip_address=ip_address,
                path=request.path
            )
        except Exception as e:
            # Log the error but don't break the application
            print(f"Error logging request: {e}")
    
    def get_client_ip(self, request):
        """Extract client IP address, handling proxy headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, the first one is the client
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip