from django.core.management.base import BaseCommand
from ip_tracking.tasks import detect_suspicious_ips

class Command(BaseCommand):
    help = 'Run anomaly detection manually'
    
    def handle(self, *args, **options):
        self.stdout.write("Running anomaly detection...")
        result = detect_suspicious_ips.delay()
        
        # Wait for result (for synchronous execution)
        detection_result = result.get(timeout=30)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Anomaly detection completed. "
                f"Found {detection_result.get('total_detected', 0)} suspicious IPs"
            )
        )