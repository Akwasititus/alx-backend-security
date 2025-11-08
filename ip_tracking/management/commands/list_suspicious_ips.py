from django.core.management.base import BaseCommand
from ip_tracking.models import SuspiciousIP

class Command(BaseCommand):
    help = 'List all suspicious IPs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--resolved',
            action='store_true',
            help='Include resolved suspicious IPs'
        )
    
    def handle(self, *args, **options):
        include_resolved = options['resolved']
        
        if include_resolved:
            suspicious_ips = SuspiciousIP.objects.all()
        else:
            suspicious_ips = SuspiciousIP.objects.filter(is_resolved=False)
        
        if not suspicious_ips:
            self.stdout.write(self.style.WARNING('No suspicious IPs found.'))
            return
        
        self.stdout.write(self.style.SUCCESS('Suspicious IP addresses:'))
        for suspicious_ip in suspicious_ips:
            status = "RESOLVED" if suspicious_ip.is_resolved else "ACTIVE"
            self.stdout.write(
                f"  {suspicious_ip.ip_address} - "
                f"{suspicious_ip.get_reason_display()} - "
                f"Requests: {suspicious_ip.request_count} - "
                f"Detected: {suspicious_ip.detected_at} - "
                f"Status: {status}"
            )
            self.stdout.write(f"    Description: {suspicious_ip.description}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Total suspicious IPs: {suspicious_ips.count()}')
        )