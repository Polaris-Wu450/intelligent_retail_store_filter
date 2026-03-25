from django.urls import path
from . import views

urlpatterns = [
    path('action-plans/', views.create_action_plan, name='create_action_plan'),
    path('action-plans/<int:plan_id>/', views.get_action_plan, name='get_action_plan'),
    path('action-plans/<int:plan_id>/status/', views.get_action_plan_status, name='get_action_plan_status'),
    path('action-plans/list/', views.list_action_plans, name='list_action_plans'),
    path('feedback/', views.feedback_endpoint, name='feedback_endpoint'),
    path('stores/', views.list_stores, name='list_stores'),
    path('customers/', views.get_customer_by_id, name='get_customer_by_id'),
    path('metrics', views.prometheus_metrics, name='prometheus_metrics'),
]

