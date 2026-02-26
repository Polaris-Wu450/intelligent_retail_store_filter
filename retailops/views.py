import json
import redis
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import ActionPlan


@csrf_exempt
@require_http_methods(["POST"])
def create_action_plan(request):
    """
    Async processing approach:
    1. Receive request and parse data
    2. Create ActionPlan record with status='pending'
    3. Push actionplan_id to Redis queue
    4. Return immediately without waiting for LLM processing
    """
    data = json.loads(request.body)
    
    store_name = data.get('store_name')
    store_location = data.get('store_location')
    issue_description = data.get('issue_description')
    
    action_plan = ActionPlan.objects.create(
        store_name=store_name,
        store_location=store_location,
        issue_description=issue_description,
        status='pending'
    )
    
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.rpush(settings.REDIS_QUEUE_NAME, action_plan.id)
    except Exception as e:
        action_plan.status = 'failed'
        action_plan.error_message = f'Redis connection error: {str(e)}'
        action_plan.save()
        return JsonResponse({
            'error': 'Failed to queue task',
            'details': str(e)
        }, status=500)
    
    return JsonResponse({
        'id': action_plan.id,
        'store_name': action_plan.store_name,
        'store_location': action_plan.store_location,
        'issue_description': action_plan.issue_description,
        'status': action_plan.status,
        'message': 'Action plan request received and queued for processing',
        'created_at': action_plan.created_at.isoformat(),
    }, status=202)


@require_http_methods(["GET"])
def get_action_plan(request, plan_id):
    try:
        action_plan = ActionPlan.objects.get(id=plan_id)
        return JsonResponse({
            'id': action_plan.id,
            'store_name': action_plan.store_name,
            'store_location': action_plan.store_location,
            'issue_description': action_plan.issue_description,
            'status': action_plan.status,
            'plan_content': action_plan.plan_content,
            'error_message': action_plan.error_message,
            'created_at': action_plan.created_at.isoformat(),
            'updated_at': action_plan.updated_at.isoformat(),
        })
    except ActionPlan.DoesNotExist:
        return JsonResponse({'error': 'Action plan not found'}, status=404)


@require_http_methods(["GET"])
def list_action_plans(request):
    action_plans = ActionPlan.objects.all()
    data = [{
        'id': plan.id,
        'store_name': plan.store_name,
        'store_location': plan.store_location,
        'issue_description': plan.issue_description,
        'status': plan.status,
        'plan_content': plan.plan_content,
        'error_message': plan.error_message,
        'created_at': plan.created_at.isoformat(),
        'updated_at': plan.updated_at.isoformat(),
    } for plan in action_plans]
    
    return JsonResponse({'action_plans': data})

