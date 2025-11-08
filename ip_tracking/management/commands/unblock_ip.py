from django.core.management.base import BaseCommand
from ip_tracking.models import BlockedIP

class Command(BaseCommand):
    help = 'Remove IP addresses from the blocklist'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'ip_addresses',
            nargs='+',
            type=str,
            help='IP addresses to unblock (space separated)'
        )
    
    def handle(self, *args, **options):
        ip_addresses = options['ip_addresses']
        
        unblocked_count = 0
        not_found_count = 0
        
        for ip_str in ip_addresses:
            deleted_count, _ = BlockedIP.objects.filter(ip_address=ip_str).delete()
            
            if deleted_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully unblocked IP: {ip_str}')
                )
                unblocked_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'IP not found in blocklist: {ip_str}')
                )
                not_found_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Unblocking complete. {unblocked_count} IPs unblocked, '
                f'{not_found_count} IPs not found in blocklist.'
            )
        )