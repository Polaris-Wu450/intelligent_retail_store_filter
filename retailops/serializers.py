"""
Serializers for data validation and format conversion
Handles: Request parsing, Response formatting
"""
import logging

logger = logging.getLogger(__name__)


def parse_create_action_plan_request(data):
    """Parse and extract fields from create action plan request"""
    logger.info("[SERIALIZERS] 🔍 parse_create_action_plan_request() called")
    logger.info(f"[SERIALIZERS] Input data type: {type(data)}")
    logger.info(f"[SERIALIZERS] Input data: {data}")
    
    result = {
        'store_name': data.get('store_name'),
        'store_location': data.get('store_location'),
        'issue_description': data.get('issue_description'),
    }
    
    logger.info(f"[SERIALIZERS] ✅ Parsed result type: {type(result)}")
    logger.info(f"[SERIALIZERS] ✅ Parsed result: {result}")
    return result


def serialize_action_plan_created(action_plan):
    """Serialize action plan response for creation (202 Accepted)"""
    logger.info("[SERIALIZERS] 📦 serialize_action_plan_created() called")
    logger.info(f"[SERIALIZERS] Input action_plan type: {type(action_plan)}")
    logger.info(f"[SERIALIZERS] Input action_plan.__class__.__name__: {action_plan.__class__.__name__}")
    logger.info(f"[SERIALIZERS] ActionPlan fields: id={action_plan.id}, status={action_plan.status}")
    
    result = {
        'id': action_plan.id,
        'store_name': action_plan.store_name,
        'store_location': action_plan.store_location,
        'issue_description': action_plan.issue_description,
        'status': action_plan.status,
        'message': 'Action plan request received and queued for processing',
        'created_at': action_plan.created_at.isoformat(),
    }
    
    logger.info(f"[SERIALIZERS] ✅ Serialized result type: {type(result)}")
    logger.info(f"[SERIALIZERS] ✅ Serialized result: {result}")
    return result


def _serialize_customer_from_plan(action_plan):
    """Extract customer info from action plan's linked feedback"""
    feedback = action_plan.feedback if action_plan.feedback_id else None
    if feedback and feedback.customer:
        return {
            'customer_id': feedback.customer.customer_id,
            'first_name': feedback.customer.first_name,
            'last_name': feedback.customer.last_name,
            'phone': feedback.customer.phone,
        }
    return None


def serialize_action_plan_detail(action_plan):
    """Serialize full action plan details"""
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
    """Serialize lightweight status response for polling"""
    response_data = {
        'id': action_plan.id,
        'status': action_plan.status,
    }
    
    # Only include content when completed
    if action_plan.status == 'completed':
        response_data['plan_content'] = action_plan.plan_content
    
    # Only include error when failed
    if action_plan.status == 'failed':
        response_data['error_message'] = action_plan.error_message
    
    return response_data


def serialize_action_plan_list(action_plans):
    """Serialize list of action plans"""
    data = [{
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
    } for plan in action_plans]
    
    return {'action_plans': data}
