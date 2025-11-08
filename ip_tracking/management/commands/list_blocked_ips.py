from django.core.management.base import BaseCommand
from ip_tracking.models import BlockedIP

class Command(BaseCommand):
    help = 'List all blocked IP addresses'
    
    def handle(self, *args, **options):
        blocked_ips = BlockedIP.objects.all()
        
        if not blocked_ips:
            self.stdout.write(self.style.WARNING('No IP addresses are currently blocked.'))
            return
        
        self.stdout.write(self.style.SUCCESS('Blocked IP addresses:'))
        for blocked_ip in blocked_ips:
            self.stdout.write(
                f"  {blocked_ip.ip_address} - "
                f"Blocked: {blocked_ip.created_at} - "
                f"Reason: {blocked_ip.reason or 'No reason provided'}"
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total blocked IPs: {blocked_ips.count()}')
        )
        