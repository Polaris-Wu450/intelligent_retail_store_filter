from django.db import models


class ActionPlan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    store_name = models.CharField(max_length=200)
    store_location = models.CharField(max_length=200)
    issue_description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    plan_content = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'action_plans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='idx_status_created'),
        ]
    
    def __str__(self):
        return f"ActionPlan {self.id} - {self.store_name} ({self.status})"

