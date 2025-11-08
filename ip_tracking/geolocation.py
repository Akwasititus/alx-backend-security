import requests
from django.core.cache import cache
import time

class GeolocationService:
    """Enhanced geolocation service with multiple fallbacks"""
    
    def __init__(self):
        self.services = [
            self._ipapi_service,
            self._ipapi_co_service,
        ]
    
    def get_geolocation(self, ip_address):
        """Try multiple geolocation services until one works"""
        cache_key = f"ip_geolocation_{ip_address}"
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Try each service until one succeeds
        for service in self.services:
            try:
                data = service(ip_address)
                if data and data.get('country'):
                    # Cache successful result for 24 hours
                    cache.set(cache_key, data, 86400)
                    return data
                time.sleep(0.1)  # Small delay between services
            except Exception as e:
                print(f"Geolocation service failed: {e}")
                continue
        
        # Return empty data if all services fail
        return {
            'country': None,
            'city': None,
            'region': None,
            'latitude': None,
            'longitude': None,
            'error': 'All geolocation services failed'
        }
    
    def _ipapi_service(self, ip_address):
        """Use ipapi.co service (free tier available)"""
        try:
            response = requests.get(f'http://ipapi.co/{ip_address}/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country_name'),
                    'country_code': data.get('country_code'),
                    'city': data.get('city'),
                    'region': data.get('region'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'timezone': data.get('timezone'),
                    'isp': data.get('org'),
                    'service': 'ipapi.co'
                }
        except Exception as e:
            print(f"ipapi.co service error: {e}")
        return None
    
    def _ipapi_co_service(self, ip_address):
        """Alternative: ip-api.com service (free for non-commercial use)"""
        try:
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country'),
                        'country_code': data.get('countryCode'),
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone'),
                        'isp': data.get('isp'),
                        'service': 'ip-api.com'
                    }
        except Exception as e:
            print(f"ip-api.com service error: {e}")
        return None