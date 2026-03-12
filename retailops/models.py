from django.db import models
from django.utils import timezone


class Store(models.Model):
    store_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores'
    
    def __str__(self):
        return f"{self.name} ({self.store_id})"


class Customer(models.Model):
    customer_id = models.CharField(max_length=100, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        indexes = [
            models.Index(fields=['first_name', 'last_name', 'phone'], name='idx_customer_name_phone'),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"


class Feedback(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='feedbacks')
    category_code = models.CharField(max_length=50, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'feedbacks'
        indexes = [
            models.Index(fields=['customer', 'category_code', 'created_at'], name='idx_feedback_key'),
        ]
    
    def __str__(self):
        return f"Feedback {self.id} - {self.customer} - {self.category_code}"


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

