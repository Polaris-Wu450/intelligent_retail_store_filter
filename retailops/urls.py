from django.urls import path
from . import views

urlpatterns = [
    path('action-plans/', views.create_action_plan, name='create_action_plan'),
    path('action-plans/<int:plan_id>/', views.get_action_plan, name='get_action_plan'),
    path('action-plans/list/', views.list_action_plans, name='list_action_plans'),
]

