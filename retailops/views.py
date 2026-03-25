import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ActionPlan, Store, Customer
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


@csrf_exempt
@require_http_methods(["GET", "POST"])
def feedback_endpoint(request):
    """
    Unified endpoint for feedback operations.
    GET: List and filter feedback
    POST: Create new feedback
    """
    if request.method == 'GET':
        return list_feedback(request)
    else:
        return create_feedback_entry(request)


@csrf_exempt
def create_feedback_entry(request):
    """
    Create a complete feedback entry with duplicate detection.
    
    Expected JSON payload:
    {
        "store_id": "ST001",
        "store_name": "Store A",
        "customer_id": "CU001",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
        "category_code": "SERVICE",
        "content": "Great service!",
        "confirm": false  (optional, default false)
    }
    
    Response codes:
    - 201: Successfully created
    - 200: Success with warnings (requires user confirmation)
    - 409: Conflict (same-day feedback duplicate)
    
    Note: All exceptions are handled by ExceptionHandlerMiddleware.
    The view simply raises exceptions and middleware converts them to JSON responses.
    """
    from .exceptions import ValidationError
    
    data = json.loads(request.body)
    
    # Extract fields (customer_id no longer required)
    store_id = data.get('store_id')
    store_name = data.get('store_name')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone = data.get('phone')
    category_code = data.get('category_code')
    content = data.get('content', '')
    confirm = data.get('confirm', False)
    
    # Validate required fields (customer_id removed from requirements)
    required_fields = {
        'store_id': store_id,
        'store_name': store_name,
        'first_name': first_name,
        'last_name': last_name,
        'phone': phone,
        'category_code': category_code
    }
    
    missing = [k for k, v in required_fields.items() if not v]
    if missing:
        raise ValidationError(
            message='Missing required fields',
            detail={'missing_fields': missing}
        )
    
    # Call the full workflow with duplicate detection
    # Customer ID will be auto-generated if customer is new
    # Any exceptions raised here will be caught by ExceptionHandlerMiddleware
    result = services.create_full_feedback_entry(
        store_id=store_id,
        store_name=store_name,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        category_code=category_code,
        content=content,
        confirm=confirm
    )
    
    # Success response (now includes action_plan)
    return JsonResponse({
        'message': 'Feedback submitted and Action Plan generation started',
        'store': {
            'id': result['store'].id,
            'store_id': result['store'].store_id,
            'name': result['store'].name
        },
        'customer': {
            'id': result['customer'].id,
            'customer_id': result['customer'].customer_id,
            'first_name': result['customer'].first_name,
            'last_name': result['customer'].last_name,
            'phone': result['customer'].phone
        },
        'feedback': {
            'id': result['feedback'].id,
            'category_code': result['feedback'].category_code,
            'created_at': result['feedback'].created_at.isoformat(),
            'content': result['feedback'].content
        },
        'action_plan': {
            'id': result['action_plan'].id,
            'status': result['action_plan'].status,
            'store_name': result['action_plan'].store_name,
            'created_at': result['action_plan'].created_at.isoformat()
        }
    }, status=201)


@require_http_methods(["GET"])
def list_stores(request):
    """
    GET /api/stores/
    Returns list of all stores for dropdown selection.
    """
    stores = Store.objects.all().order_by('name')
    
    return JsonResponse({
        'stores': [
            {
                'id': store.id,
                'store_id': store.store_id,
                'name': store.name
            }
            for store in stores
        ]
    })


@require_http_methods(["GET"])
def get_customer_by_id(request):
    """
    GET /api/customers/?first_name=xx&last_name=xx&phone=xx
    Returns customer if all three fields match exactly.
    """
    first_name = request.GET.get('first_name', '').strip()
    last_name = request.GET.get('last_name', '').strip()
    phone = request.GET.get('phone', '').strip()
    
    if not all([first_name, last_name, phone]):
        return JsonResponse({
            'error': 'first_name, last_name, and phone are all required'
        }, status=400)
    
    try:
        # All three fields must match exactly
        customer = Customer.objects.get(
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        return JsonResponse({
            'found': True,
            'customer': {
                'id': customer.id,
                'customer_id': customer.customer_id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone': customer.phone
            }
        })
    except Customer.DoesNotExist:
        return JsonResponse({
            'found': False,
            'message': 'New customer - will be created upon submission'
        }, status=404)
    except Customer.MultipleObjectsReturned:
        # Should not happen with proper data, but handle it
        return JsonResponse({
            'error': 'Multiple customers found with same details'
        }, status=409)


@require_http_methods(["GET"])
def list_stores(request):
    """
    GET /api/stores/
    Returns a list of all stores
    """
    from .models import Store
    
    stores = Store.objects.all().order_by('store_id')
    
    return JsonResponse({
        'stores': [
            {
                'id': store.id,
                'store_id': store.store_id,
                'name': store.name,
                'display_name': f"{store.name} ({store.store_id})"
            }
            for store in stores
        ]
    })


@require_http_methods(["GET"])
def get_customer_by_id(request):
    """
    GET /api/customers/?first_name=xx&last_name=xx&phone=xx
    Returns customer details if found, 404 otherwise
    """
    from .models import Customer
    
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    phone = request.GET.get('phone')
    
    if not (first_name and last_name and phone):
        return JsonResponse({
            'error': 'first_name, last_name, and phone parameters are required'
        }, status=400)
    
    try:
        customer = Customer.objects.get(
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        return JsonResponse({
            'found': True,
            'id': customer.id,
            'customer_id': customer.customer_id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone
        })
    except Customer.DoesNotExist:
        return JsonResponse({
            'found': False,
            'message': 'New customer - will be created upon submission'
        }, status=200)


@require_http_methods(["GET"])
def prometheus_metrics(request):
    """
    Custom metrics endpoint that syncs Celery worker metrics from Redis
    before returning Prometheus metrics
    """
    from .metrics import sync_metrics_from_redis
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    sync_metrics_from_redis()
    
    metrics = generate_latest()
    return HttpResponse(metrics, content_type=CONTENT_TYPE_LATEST)


def list_feedback(request):
    """
    GET /api/feedback/
    
    Query Parameters (all optional):
    - category: Filter by category code (FURNITURE, ELECTRONICS, CLOTHING)
    - store_id: Filter by store ID (e.g., NYC001)
    
    Examples:
    - GET /api/feedback/                          → all feedback
    - GET /api/feedback/?category=FURNITURE       → furniture only
    - GET /api/feedback/?store_id=NYC001          → specific store only
    - GET /api/feedback/?category=FURNITURE&store_id=NYC001 → combined filter
    
    Returns:
    {
        "feedback": [
            {
                "feedback_id": 1,
                "store_id": "NYC001",
                "store_name": "New York Manhattan Flagship",
                "category_code": "FURNITURE",
                "created_at": "2026-03-24T03:33:03.201Z",
                "status": "completed",
                "action_plan": {
                    "id": 38,
                    "content": "... plan content ...",
                    "created_at": "2026-03-24T03:33:03.203Z"
                }
            }
        ]
    }
    """
    from .models import Feedback
    
    # Start with all feedback, ordered by newest first
    queryset = Feedback.objects.select_related('store', 'customer').prefetch_related('action_plans').order_by('-created_at')
    
    # Apply filters if provided
    category = request.GET.get('category')
    store_id = request.GET.get('store_id')
    
    if category:
        queryset = queryset.filter(category_code=category.upper())
    
    if store_id:
        queryset = queryset.filter(store__store_id=store_id)
    
    # Build response data
    feedback_list = []
    for feedback in queryset:
        # Get the most recent action plan (if exists)
        action_plan = feedback.action_plans.order_by('-created_at').first()
        
        feedback_data = {
            'feedback_id': feedback.id,
            'store_id': feedback.store.store_id,
            'store_name': feedback.store.name,
            'category_code': feedback.category_code,
            'created_at': feedback.created_at.isoformat(),
            'status': action_plan.status if action_plan else 'no_plan',
            'action_plan': None
        }
        
        # Include action plan content if completed
        if action_plan and action_plan.status == 'completed':
            feedback_data['action_plan'] = {
                'id': action_plan.id,
                'content': action_plan.plan_content,
                'created_at': action_plan.created_at.isoformat(),
                'updated_at': action_plan.updated_at.isoformat()
            }
        elif action_plan:
            # Include basic info even if not completed
            feedback_data['action_plan'] = {
                'id': action_plan.id,
                'content': None,
                'created_at': action_plan.created_at.isoformat(),
                'updated_at': action_plan.updated_at.isoformat()
            }
        
        feedback_list.append(feedback_data)
    
    return JsonResponse({
        'feedback': feedback_list,
        'count': len(feedback_list),
        'filters': {
            'category': category,
            'store_id': store_id
        }
    })

