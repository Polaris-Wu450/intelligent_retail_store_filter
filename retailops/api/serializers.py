"""
Serializers: request parsing and response formatting for all API endpoints.
"""
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Action Plan
# ============================================================================

def parse_create_action_plan_request(data):
    return {
        'store_name': data.get('store_name'),
        'store_location': data.get('store_location'),
        'issue_description': data.get('issue_description'),
    }


def serialize_action_plan_created(action_plan):
    """202 Accepted response after queuing an action plan."""
    return {
        'id': action_plan.id,
        'store_name': action_plan.store_name,
        'store_location': action_plan.store_location,
        'issue_description': action_plan.issue_description,
        'status': action_plan.status,
        'message': 'Action plan request received and queued for processing',
        'created_at': action_plan.created_at.isoformat(),
    }


def serialize_action_plan_detail(action_plan):
    return {
        'id': action_plan.id,
        'store_name': action_plan.store_name,
        'store_location': action_plan.store_location,
        'issue_description': action_plan.issue_description,
        'status': action_plan.status,
        'plan_content': action_plan.plan_content,
        'error_message': action_plan.error_message,
        'customer': _serialize_customer_from_plan(action_plan),
        'created_at': action_plan.created_at.isoformat(),
        'updated_at': action_plan.updated_at.isoformat(),
    }


def serialize_action_plan_status(action_plan):
    """Lightweight polling response — only include content/error when relevant."""
    data = {'id': action_plan.id, 'status': action_plan.status}
    if action_plan.status == 'completed':
        data['plan_content'] = action_plan.plan_content
    if action_plan.status == 'failed':
        data['error_message'] = action_plan.error_message
    return data


def serialize_action_plan_list(action_plans):
    return {
        'action_plans': [
            {
                'id': plan.id,
                'store_name': plan.store_name,
                'store_location': plan.store_location,
                'issue_description': plan.issue_description,
                'status': plan.status,
                'plan_content': plan.plan_content,
                'error_message': plan.error_message,
                'customer': _serialize_customer_from_plan(plan),
                'created_at': plan.created_at.isoformat(),
                'updated_at': plan.updated_at.isoformat(),
            }
            for plan in action_plans
        ]
    }


def _serialize_customer_from_plan(action_plan):
    feedback = action_plan.feedback if action_plan.feedback_id else None
    if feedback and feedback.customer:
        c = feedback.customer
        return {
            'customer_id': c.customer_id,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'phone': c.phone,
        }
    return None


# ============================================================================
# Feedback
# ============================================================================

def serialize_feedback_created(result):
    """201 response after successfully creating feedback + action plan."""
    store = result['store']
    customer = result['customer']
    feedback = result['feedback']
    action_plan = result['action_plan']
    return {
        'message': 'Feedback submitted and Action Plan generation started',
        'store': {
            'id': store.id,
            'store_id': store.store_id,
            'name': store.name,
        },
        'customer': {
            'id': customer.id,
            'customer_id': customer.customer_id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone,
        },
        'feedback': {
            'id': feedback.id,
            'category_code': feedback.category_code,
            'content': feedback.content,
            'created_at': feedback.created_at.isoformat(),
        },
        'action_plan': {
            'id': action_plan.id,
            'status': action_plan.status,
            'store_name': action_plan.store_name,
            'created_at': action_plan.created_at.isoformat(),
        },
    }


def serialize_feedback_list(queryset, category_filter=None, store_id_filter=None):
    """Response for GET /api/feedback/ with optional filters."""
    feedback_list = []

    for feedback in queryset:
        action_plan = feedback.action_plans.order_by('-created_at').first()

        item = {
            'feedback_id': feedback.id,
            'store_id': feedback.store.store_id,
            'store_name': feedback.store.name,
            'customer': {
                'customer_id': feedback.customer.customer_id,
                'first_name': feedback.customer.first_name,
                'last_name': feedback.customer.last_name,
                'phone': feedback.customer.phone,
            },
            'category_code': feedback.category_code,
            'content': feedback.content,
            'created_at': feedback.created_at.isoformat(),
            'status': action_plan.status if action_plan else 'no_plan',
            'action_plan': _serialize_action_plan_for_feedback(action_plan),
        }
        feedback_list.append(item)

    return {
        'feedback': feedback_list,
        'count': len(feedback_list),
        'filters': {
            'category': category_filter,
            'store_id': store_id_filter,
        },
    }


def _serialize_action_plan_for_feedback(action_plan):
    if not action_plan:
        return None
    return {
        'id': action_plan.id,
        'content': action_plan.plan_content if action_plan.status == 'completed' else None,
        'created_at': action_plan.created_at.isoformat(),
        'updated_at': action_plan.updated_at.isoformat(),
    }
