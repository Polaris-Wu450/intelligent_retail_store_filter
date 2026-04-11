import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models import ActionPlan, Store, Customer, Feedback
from ..exceptions import ValidationError
from .. import services
from . import serializers

logger = logging.getLogger(__name__)


# ============================================================================
# Action Plans
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def create_action_plan(request):
    data = json.loads(request.body)
    parsed_data = serializers.parse_create_action_plan_request(data)
    action_plan = services.create_action_plan(**parsed_data)
    services.dispatch_action_plan_task(action_plan.id)
    return JsonResponse(serializers.serialize_action_plan_created(action_plan), status=202)


@require_http_methods(["GET"])
def get_action_plan(request, plan_id):
    try:
        action_plan = services.get_action_plan_by_id(plan_id)
        return JsonResponse(serializers.serialize_action_plan_detail(action_plan))
    except ActionPlan.DoesNotExist:
        return JsonResponse({'error': 'Action plan not found'}, status=404)


@require_http_methods(["GET"])
def get_action_plan_status(request, plan_id):
    """Lightweight polling endpoint — returns only status and content when ready."""
    try:
        action_plan = services.get_action_plan_by_id(plan_id)
        return JsonResponse(serializers.serialize_action_plan_status(action_plan))
    except ActionPlan.DoesNotExist:
        return JsonResponse({'error': 'Action plan not found'}, status=404)


@require_http_methods(["GET"])
def list_action_plans(request):
    action_plans = services.get_all_action_plans()
    return JsonResponse(serializers.serialize_action_plan_list(action_plans))


# ============================================================================
# Feedback
# ============================================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def feedback_endpoint(request):
    if request.method == 'GET':
        return list_feedback(request)
    return create_feedback_entry(request)


def create_feedback_entry(request):
    data = json.loads(request.body)

    store_id = data.get('store_id')
    store_name = data.get('store_name')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone = data.get('phone')
    category_code = data.get('category_code')
    content = data.get('content', '')
    confirm = data.get('confirm', False)

    required_fields = {
        'store_id': store_id,
        'store_name': store_name,
        'first_name': first_name,
        'last_name': last_name,
        'phone': phone,
        'category_code': category_code,
    }
    missing = [k for k, v in required_fields.items() if not v]
    if missing:
        raise ValidationError(
            message='Missing required fields',
            detail={'missing_fields': missing},
        )

    result = services.create_full_feedback_entry(
        store_id=store_id,
        store_name=store_name,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        category_code=category_code,
        content=content,
        confirm=confirm,
    )
    return JsonResponse(serializers.serialize_feedback_created(result), status=201)


def list_feedback(request):
    """
    GET /api/feedback/
    Optional query params: category, store_id
    """
    queryset = (
        Feedback.objects.select_related('store', 'customer')
        .prefetch_related('action_plans')
        .order_by('-created_at')
    )

    category = request.GET.get('category')
    store_id = request.GET.get('store_id')

    if category:
        queryset = queryset.filter(category_code=category.upper())
    if store_id:
        queryset = queryset.filter(store__store_id=store_id)

    return JsonResponse(
        serializers.serialize_feedback_list(queryset, category, store_id)
    )


# ============================================================================
# Stores
# ============================================================================

@require_http_methods(["GET"])
def list_stores(request):
    stores = Store.objects.all().order_by('store_id')
    return JsonResponse({
        'stores': [
            {
                'id': store.id,
                'store_id': store.store_id,
                'name': store.name,
                'display_name': f"{store.name} ({store.store_id})",
            }
            for store in stores
        ]
    })


# ============================================================================
# Customers
# ============================================================================

@require_http_methods(["GET"])
def get_customer_by_id(request):
    """GET /api/customers/?first_name=xx&last_name=xx&phone=xx"""
    first_name = request.GET.get('first_name', '').strip()
    last_name = request.GET.get('last_name', '').strip()
    phone = request.GET.get('phone', '').strip()

    if not all([first_name, last_name, phone]):
        return JsonResponse(
            {'error': 'first_name, last_name, and phone are all required'},
            status=400,
        )

    try:
        customer = Customer.objects.get(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
        return JsonResponse({
            'found': True,
            'customer': {
                'id': customer.id,
                'customer_id': customer.customer_id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone': customer.phone,
            },
        })
    except Customer.DoesNotExist:
        return JsonResponse(
            {'found': False, 'message': 'New customer — will be created upon submission'},
            status=404,
        )
    except Customer.MultipleObjectsReturned:
        return JsonResponse(
            {'error': 'Multiple customers found with same details'},
            status=409,
        )
