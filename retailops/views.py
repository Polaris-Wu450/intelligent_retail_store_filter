import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ActionPlan
from . import services
from . import serializers

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def create_action_plan(request):
    """
    Async processing with Celery:
    1. Receive request and parse data
    2. Create ActionPlan record with status='pending'
    3. Dispatch Celery task to generate action plan
    4. Return immediately without waiting for LLM processing
    """
    logger.info("=" * 80)
    logger.info("[VIEWS] 📥 Step 1: Request received at views.create_action_plan()")
    logger.info(f"[VIEWS] HTTP Method: {request.method}")
    logger.info(f"[VIEWS] Content-Type: {request.content_type}")
    logger.info(f"[VIEWS] Raw request.body type: {type(request.body)}")
    logger.info(f"[VIEWS] Raw request.body content: {request.body.decode('utf-8')[:200]}")
    
    data = json.loads(request.body)
    logger.info(f"[VIEWS] 📝 After json.loads() - data type: {type(data)}")
    logger.info(f"[VIEWS] 📝 After json.loads() - data content: {data}")
    
    logger.info("[VIEWS] ➡️  Calling serializers.parse_create_action_plan_request()...")
    parsed_data = serializers.parse_create_action_plan_request(data)
    logger.info(f"[VIEWS] ⬅️  Returned from serializers - parsed_data type: {type(parsed_data)}")
    logger.info(f"[VIEWS] ⬅️  Returned from serializers - parsed_data: {parsed_data}")
    
    logger.info("[VIEWS] ➡️  Calling services.create_action_plan()...")
    action_plan = services.create_action_plan(**parsed_data)
    logger.info(f"[VIEWS] ⬅️  Returned from services - action_plan type: {type(action_plan)}")
    logger.info(f"[VIEWS] ⬅️  Returned from services - action_plan: {action_plan}")
    logger.info(f"[VIEWS] ⬅️  ActionPlan ID: {action_plan.id}, Status: {action_plan.status}")
    
    logger.info("[VIEWS] ➡️  Calling services.dispatch_action_plan_task()...")
    services.dispatch_action_plan_task(action_plan.id)
    logger.info(f"[VIEWS] ⬅️  Task dispatched to Celery for plan_id: {action_plan.id}")
    
    logger.info("[VIEWS] ➡️  Calling serializers.serialize_action_plan_created()...")
    response_data = serializers.serialize_action_plan_created(action_plan)
    logger.info(f"[VIEWS] ⬅️  Returned from serializers - response_data type: {type(response_data)}")
    logger.info(f"[VIEWS] ⬅️  Returned from serializers - response_data: {response_data}")
    
    logger.info(f"[VIEWS] 📤 Step 5: Returning JsonResponse with status=202")
    logger.info("=" * 80)
    return JsonResponse(response_data, status=202)


@require_http_methods(["GET"])
def get_action_plan(request, plan_id):
    try:
        action_plan = services.get_action_plan_by_id(plan_id)
        response_data = serializers.serialize_action_plan_detail(action_plan)
        return JsonResponse(response_data)
    except ActionPlan.DoesNotExist:
        return JsonResponse({'error': 'Action plan not found'}, status=404)


@require_http_methods(["GET"])
def get_action_plan_status(request, plan_id):
    """
    Lightweight endpoint for polling task status.
    Returns only essential fields to minimize data transfer.
    """
    try:
        action_plan = services.get_action_plan_by_id(plan_id)
        response_data = serializers.serialize_action_plan_status(action_plan)
        return JsonResponse(response_data)
    except ActionPlan.DoesNotExist:
        return JsonResponse({'error': 'Action plan not found'}, status=404)


@require_http_methods(["GET"])
def list_action_plans(request):
    action_plans = services.get_all_action_plans()
    response_data = serializers.serialize_action_plan_list(action_plans)
    return JsonResponse(response_data)

