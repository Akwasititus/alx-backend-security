from django.test import TestCase

# Create your tests here.
from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from .models import RequestLog, SuspiciousIP, BlockedIP
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def detect_suspicious_ips():
    """
    Celery task to detect suspicious IPs based on:
    - High request volume (>100 requests per hour)
    - Access to sensitive paths
    - Multiple sensitive path accesses
    """
    logger.info("Starting suspicious IP detection task")
    
    one_hour_ago = timezone.now() - timedelta(hours=1)
    results = {
        'high_volume_ips': [],
        'sensitive_access_ips': [],
        'total_detected': 0
    }
    
    try:
        # 1. Detect IPs with high request volume
        high_volume_ips = detect_high_volume_ips(one_hour_ago)
        results['high_volume_ips'] = high_volume_ips
        
        # 2. Detect IPs accessing sensitive paths
        sensitive_ips = detect_sensitive_path_access(one_hour_ago)
        results['sensitive_access_ips'] = sensitive_ips
        
        # 3. Combine and create SuspiciousIP records
        all_suspicious_ips = combine_suspicious_ips(high_volume_ips, sensitive_ips)
        results['total_detected'] = len(all_suspicious_ips)
        
        logger.info(f"Anomaly detection completed. Found {len(all_suspicious_ips)} suspicious IPs")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in anomaly detection task: {e}")
        return {'error': str(e)}

def detect_high_volume_ips(since_time):
    """Detect IPs with request volume exceeding threshold"""
    threshold = settings.ANOMALY_DETECTION['REQUESTS_PER_HOUR_THRESHOLD']
    
    high_volume_ips = (
        RequestLog.objects
        .filter(timestamp__gte=since_time)
        .values('ip_address')
        .annotate(request_count=Count('id'))
        .filter(request_count__gt=threshold)
        .order_by('-request_count')
    )
    
    detected_ips = []
    for ip_data in high_volume_ips:
        ip_address = ip_data['ip_address']
        request_count = ip_data['request_count']
        
        # Check if already marked as suspicious
        if not SuspiciousIP.objects.filter(
            ip_address=ip_address, 
            reason='high_volume',
            is_resolved=False
        ).exists():
            
            suspicious_ip = SuspiciousIP.objects.create(
                ip_address=ip_address,
                reason='high_volume',
                description=f'High request volume: {request_count} requests in the last hour (threshold: {threshold})',
                request_count=request_count
            )
            detected_ips.append({
                'ip_address': ip_address,
                'request_count': request_count,
                'suspicious_ip_id': suspicious_ip.id
            })
            logger.warning(f"Detected high volume IP: {ip_address} with {request_count} requests")
    
    return detected_ips

def detect_sensitive_path_access(since_time):
    """Detect IPs accessing sensitive paths"""
    sensitive_paths = settings.ANOMALY_DETECTION['SENSITIVE_PATHS']
    
    # Build query for sensitive paths
    sensitive_path_query = Q()
    for path in sensitive_paths:
        sensitive_path_query |= Q(path__startswith=path)
    
    sensitive_access = (
        RequestLog.objects
        .filter(timestamp__gte=since_time)
        .filter(sensitive_path_query)
        .values('ip_address', 'path')
        .annotate(access_count=Count('id'))
        .order_by('-access_count')
    )
    
    detected_ips = []
    ip_path_access = {}
    
    # Group by IP address to count total sensitive accesses
    for access in sensitive_access:
        ip_address = access['ip_address']
        path = access['path']
        access_count = access['access_count']
        
        if ip_address not in ip_path_access:
            ip_path_access[ip_address] = {
                'paths': {},
                'total_accesses': 0
            }
        
        ip_path_access[ip_address]['paths'][path] = access_count
        ip_path_access[ip_address]['total_accesses'] += access_count
    
    # Create SuspiciousIP records
    for ip_address, data in ip_path_access.items():
        total_accesses = data['total_accesses']
        paths_accessed = list(data['paths'].keys())
        
        # Determine reason based on access pattern
        if len(paths_accessed) > 1:
            reason = 'multiple_sensitive'
            description = f"Accessed multiple sensitive paths: {', '.join(paths_accessed)}. Total accesses: {total_accesses}"
        else:
            reason = 'sensitive_access'
            description = f"Accessed sensitive path: {paths_accessed[0]}. Total accesses: {total_accesses}"
        
        # Check if already marked as suspicious for this reason
        if not SuspiciousIP.objects.filter(
            ip_address=ip_address, 
            reason=reason,
            is_resolved=False
        ).exists():
            
            suspicious_ip = SuspiciousIP.objects.create(
                ip_address=ip_address,
                reason=reason,
                description=description,
                request_count=total_accesses
            )
            detected_ips.append({
                'ip_address': ip_address,
                'paths_accessed': paths_accessed,
                'total_accesses': total_accesses,
                'suspicious_ip_id': suspicious_ip.id
            })
            logger.warning(f"Detected sensitive path access from IP: {ip_address} - {description}")
    
    return detected_ips

def combine_suspicious_ips(high_volume_ips, sensitive_ips):
    """Combine detected IPs and handle duplicates"""
    all_ips = {}
    
    # Add high volume IPs
    for ip_data in high_volume_ips:
        ip_address = ip_data['ip_address']
        all_ips[ip_address] = ip_data
    
    # Add sensitive access IPs, update if already exists
    for ip_data in sensitive_ips:
        ip_address = ip_data['ip_address']
        if ip_address in all_ips:
            # IP has both high volume and sensitive access - update reason
            existing_data = all_ips[ip_address]
            suspicious_ip = SuspiciousIP.objects.get(id=existing_data['suspicious_ip_id'])
            suspicious_ip.reason = 'suspicious_pattern'
            suspicious_ip.description += f" | Also: {ip_data['description']}"
            suspicious_ip.save()
        else:
            all_ips[ip_address] = ip_data
    
    return list(all_ips.values())

@shared_task
def auto_block_suspicious_ips():
    """
    Optional task to automatically block IPs that are repeatedly suspicious
    """
    threshold = 3  # Number of times IP must be flagged as suspicious
    lookback_days = 7
    
    cutoff_time = timezone.now() - timedelta(days=lookback_days)
    
    repeat_offenders = (
        SuspiciousIP.objects
        .filter(detected_at__gte=cutoff_time, is_resolved=False)
        .values('ip_address')
        .annotate(suspicious_count=Count('id'))
        .filter(suspicious_count__gte=threshold)
    )
    
    blocked_count = 0
    for offender in repeat_offenders:
        ip_address = offender['ip_address']
        suspicious_count = offender['suspicious_count']
        
        # Check if not already blocked
        if not BlockedIP.objects.filter(ip_address=ip_address).exists():
            BlockedIP.objects.create(
                ip_address=ip_address,
                reason=f"Automatically blocked: flagged as suspicious {suspicious_count} times in the last {lookback_days} days"
            )
            blocked_count += 1
            logger.warning(f"Auto-blocked repeat offender: {ip_address}")
    
    return {'auto_blocked_count': blocked_count}

@shared_task
def cleanup_old_suspicious_ips():
    """
    Clean up resolved suspicious IP records older than 30 days
    """
    cutoff_time = timezone.now() - timedelta(days=30)
    
    deleted_count, _ = SuspiciousIP.objects.filter(
        detected_at__lt=cutoff_time,
        is_resolved=True
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old resolved suspicious IP records")
    return {'cleaned_up_count': deleted_count}