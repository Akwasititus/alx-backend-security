from django.db import models

# Create your models here.
from django.db import models

class RequestLog(models.Model):
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'request_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.ip_address} - {self.path} - {self.timestamp}"


class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'blocked_ips'
        verbose_name = 'Blocked IP'
        verbose_name_plural = 'Blocked IPs'
    
    def __str__(self):
        return f"{self.ip_address} - {self.created_at}"
        