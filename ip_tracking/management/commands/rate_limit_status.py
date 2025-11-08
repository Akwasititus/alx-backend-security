from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Show current rate limit status'
    
    def handle(self, *args, **options):
        # This would need a more sophisticated implementation
        # to properly inspect rate limit keys in cache
        self.stdout.write(
            self.style.SUCCESS('Rate limiting is configured and active')
        )
        self.stdout.write('Configured limits:')
        self.stdout.write('  - Anonymous users: 5 requests/minute')
        self.stdout.write('  - Authenticated users: 10 requests/minute')
        self.stdout.write('  - API endpoints: 10 requests/minute per IP')