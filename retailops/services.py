"""
Business logic layer
Handles: Database operations, LLM API calls, Task dispatching
"""
import os
import time
import logging
import anthropic
from django.conf import settings
from django.db.models import Q
from datetime import date
from .models import ActionPlan, Store, Customer, Feedback
from .exceptions import (
    StoreConflictError,
    CustomerConflictError,
    CustomerWarning,
    FeedbackDuplicateError,
    FeedbackWarning,
)

logger = logging.getLogger(__name__)


def create_action_plan(store_name, store_location, issue_description):
    """Create new action plan record with pending status"""
    logger.info("[SERVICES] 💾 create_action_plan() called")
    logger.info(f"[SERVICES] Input parameters (type: {type(store_name)}, {type(store_location)}, {type(issue_description)}):")
    logger.info(f"[SERVICES]   - store_name: {store_name}")
    logger.info(f"[SERVICES]   - store_location: {store_location}")
    logger.info(f"[SERVICES]   - issue_description: {issue_description}")
    
    logger.info("[SERVICES] 🗄️  Calling ActionPlan.objects.create()...")
    action_plan = ActionPlan.objects.create(
        store_name=store_name,
        store_location=store_location,
        issue_description=issue_description,
        status='pending'
    )
    
    logger.info(f"[SERVICES] ✅ ActionPlan created in database:")
    logger.info(f"[SERVICES]   - Type: {type(action_plan)}")
    logger.info(f"[SERVICES]   - Class: {action_plan.__class__.__name__}")
    logger.info(f"[SERVICES]   - ID: {action_plan.id}")
    logger.info(f"[SERVICES]   - Status: {action_plan.status}")
    logger.info(f"[SERVICES]   - Created at: {action_plan.created_at}")
    
    return action_plan


def dispatch_action_plan_task(action_plan_id):
    """Dispatch Celery task to generate action plan"""
    logger.info("[SERVICES] 🚀 dispatch_action_plan_task() called")
    logger.info(f"[SERVICES] action_plan_id: {action_plan_id} (type: {type(action_plan_id)})")
    
    from .tasks import generate_action_plan
    
    logger.info("[SERVICES] 📨 Sending task to Celery queue (Redis)...")
    task_result = generate_action_plan.delay(action_plan_id)
    logger.info(f"[SERVICES] ✅ Task dispatched! Task ID: {task_result.id}")
    logger.info(f"[SERVICES] 📍 Task will be picked up by Celery worker")


def get_action_plan_by_id(plan_id):
    """Retrieve action plan by ID"""
    return ActionPlan.objects.get(id=plan_id)


def get_all_action_plans():
    """Retrieve all action plans"""
    return ActionPlan.objects.all()


def get_mock_action_plan(store_name, store_location, issue_description):
    """
    Mock LLM response for testing (no API call, no cost, instant)
    """
    return f"""**IMMEDIATE ACTIONS FOR {store_name}**

1. Emergency Response Team
   - Deploy on-site manager to {store_location} within 2 hours
   - Assess severity of: {issue_description}
   - Document current status with photos and incident report

2. Short-term Solution
   - Implement temporary workaround to minimize customer impact
   - Notify affected customers with expected resolution timeline
   - Set up alternative service if primary system unavailable

3. Root Cause Analysis
   - Schedule technical team inspection within 24 hours
   - Review maintenance logs and identify failure patterns
   - Prepare detailed incident report for management review

4. Communication Plan
   - Update store staff with talking points for customer inquiries
   - Post signage explaining situation and workarounds
   - Monitor social media and respond to complaints within 1 hour

5. Follow-up Actions
   - Schedule follow-up inspection in 7 days
   - Update preventive maintenance schedule
   - Train staff on early warning signs

**MOCK DATA - FOR TESTING ONLY**"""


def call_llm_api(store_name, store_location, issue_description):
    """
    Call real LLM API
    """
    client = anthropic.Anthropic(api_key=settings.RETAILOPS_API_KEY)
    
    prompt = f"""You are a retail operations assistant helping B2B managers. Generate a CONCISE, actionable plan for this store issue.

Store Name: {store_name}
Store Location: {store_location}
Issue: {issue_description}

Requirements:
- Provide 3-5 KEY ACTIONS only
- Each action must be SPECIFIC and IMMEDIATELY EXECUTABLE
- Focus on high-impact solutions
- Keep it brief - managers need to act quickly
- Format: Action title, 2-3 bullet points with concrete steps

Generate a short, practical action plan now:"""
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text


def process_action_plan_generation(plan_id):
    """
    Business logic for generating action plan using LLM
    Updates database status throughout process
    """
    logger.info("=" * 80)
    logger.info("[SERVICES] 🤖 process_action_plan_generation() called (in Celery worker)")
    logger.info(f"[SERVICES] plan_id: {plan_id} (type: {type(plan_id)})")
    
    logger.info("[SERVICES] 🗄️  Fetching ActionPlan from database...")
    plan = ActionPlan.objects.get(id=plan_id)
    logger.info(f"[SERVICES] ✅ Found plan: {plan.store_name}, current status: {plan.status}")
    
    logger.info("[SERVICES] 📝 Updating status to 'processing'...")
    plan.status = 'processing'
    plan.save()
    logger.info("[SERVICES] ✅ Status saved to database")
    
    use_mock = os.getenv('USE_MOCK_LLM', 'false').lower() == 'true'
    logger.info(f"[SERVICES] 🔧 USE_MOCK_LLM: {use_mock}")
    
    if use_mock:
        logger.info("[SERVICES] 🎭 Using MOCK LLM (no API call)...")
        time.sleep(1)
        plan_content = get_mock_action_plan(
            plan.store_name, 
            plan.store_location, 
            plan.issue_description
        )
        logger.info(f"[SERVICES] ✅ Mock LLM returned {len(plan_content)} characters")
    else:
        logger.info("[SERVICES] 🌐 Calling REAL Claude API...")
        plan_content = call_llm_api(
            plan.store_name,
            plan.store_location,
            plan.issue_description
        )
        logger.info(f"[SERVICES] ✅ Claude API returned {len(plan_content)} characters")
    
    logger.info("[SERVICES] 📝 Updating status to 'completed' and saving plan_content...")
    plan.status = 'completed'
    plan.plan_content = plan_content
    plan.save()
    logger.info("[SERVICES] ✅ Final status saved to database")
    
    result = {'status': 'completed', 'plan_id': plan_id, 'mock': use_mock}
    logger.info(f"[SERVICES] 🎉 Process complete! Result: {result}")
    logger.info("=" * 80)
    
    return result


def mark_action_plan_as_failed(plan_id, error_message):
    """Mark action plan as failed with error message"""
    plan = ActionPlan.objects.get(id=plan_id)
    plan.status = 'failed'
    plan.error_message = str(error_message)
    plan.save()


# ============================================================================
# Store Duplicate Detection
# ============================================================================

def check_and_get_store(store_id, name):
    """
    Store duplicate detection logic:
    - Store ID same + name same → reuse existing
    - Store ID same + name different → BLOCK (409)
    
    Returns:
        Store object (existing or None if should create new)
    
    Raises:
        StoreConflictError with details if store_id exists but name differs
    """
    try:
        existing_store = Store.objects.get(store_id=store_id)
        
        # Store ID exists, check name
        if existing_store.name == name:
            # Same store_id + same name → reuse
            logger.info(f"[STORE] Reusing existing store: {existing_store.id}")
            return existing_store
        else:
            # Same store_id + different name → BLOCK
            logger.error(
                f"[STORE] Store ID conflict: {store_id} "
                f"existing='{existing_store.name}' provided='{name}'"
            )
            raise StoreConflictError(
                message=f'Store ID {store_id} already exists with name "{existing_store.name}", but you provided "{name}"',
                detail={
                    'store_id': store_id,
                    'existing_store_id': existing_store.id,
                    'existing_name': existing_store.name,
                    'provided_name': name,
                }
            )
    
    except Store.DoesNotExist:
        # No existing store with this ID, can create new
        return None


def create_store_if_needed(store_id, name):
    """
    Create store if it doesn't exist, or reuse existing one.
    
    Returns:
        Store object
    
    Raises:
        StoreConflictError if conflict detected
    """
    existing = check_and_get_store(store_id, name)
    
    if existing:
        return existing
    
    # Create new store
    new_store = Store.objects.create(store_id=store_id, name=name)
    logger.info(f"[STORE] Created new store: {new_store.id}")
    return new_store


# ============================================================================
# Customer Duplicate Detection
# ============================================================================

def check_and_get_customer(customer_id, first_name, last_name, phone):
    """
    Customer duplicate detection logic:
    - CID same + name and phone all same → reuse existing
    - CID same + name or phone different → WARNING (raise exception)
    - Name + phone same + CID different → WARNING (raise exception)
    
    Returns:
        Customer object if perfect match found, None if should create new
    
    Raises:
        CustomerWarning if data conflicts detected
    """
    # Check 1: Customer ID exists?
    try:
        existing_by_cid = Customer.objects.get(customer_id=customer_id)
        
        # CID exists, check if name and phone match
        name_matches = (existing_by_cid.first_name == first_name and 
                       existing_by_cid.last_name == last_name)
        phone_matches = existing_by_cid.phone == phone
        
        if name_matches and phone_matches:
            # Perfect match → reuse
            logger.info(f"[CUSTOMER] Reusing existing customer: {existing_by_cid.id}")
            return existing_by_cid
        else:
            # CID same but name or phone different → WARNING
            logger.warning(
                f"[CUSTOMER] Customer ID {customer_id} exists with different data"
            )
            
            detail = {
                'customer_id': customer_id,
                'existing_customer_id': existing_by_cid.id,
            }
            
            if not name_matches:
                detail['existing_name'] = f"{existing_by_cid.first_name} {existing_by_cid.last_name}"
                detail['provided_name'] = f"{first_name} {last_name}"
            
            if not phone_matches:
                detail['existing_phone'] = existing_by_cid.phone
                detail['provided_phone'] = phone
            
            message_parts = [f"Customer ID {customer_id} exists but with different information."]
            if not name_matches:
                message_parts.append(
                    f"Existing name: '{existing_by_cid.first_name} {existing_by_cid.last_name}', "
                    f"provided: '{first_name} {last_name}'."
                )
            if not phone_matches:
                message_parts.append(
                    f"Existing phone: '{existing_by_cid.phone}', provided: '{phone}'."
                )
            
            raise CustomerWarning(
                message=" ".join(message_parts),
                detail=detail
            )
    
    except Customer.DoesNotExist:
        # CID doesn't exist, check if name+phone combo exists with different CID
        existing_by_name_phone = Customer.objects.filter(
            first_name=first_name,
            last_name=last_name,
            phone=phone
        ).first()
        
        if existing_by_name_phone:
            # Name+phone match but different CID → WARNING
            logger.warning(
                f"[CUSTOMER] Name+phone exists with different CID: "
                f"existing={existing_by_name_phone.customer_id}, provided={customer_id}"
            )
            
            raise CustomerWarning(
                message=(
                    f"Customer with name '{first_name} {last_name}' and phone '{phone}' "
                    f"already exists with Customer ID '{existing_by_name_phone.customer_id}', "
                    f"but you provided Customer ID '{customer_id}'"
                ),
                detail={
                    'existing_customer_id': existing_by_name_phone.id,
                    'existing_cid': existing_by_name_phone.customer_id,
                    'provided_cid': customer_id,
                    'name': f"{first_name} {last_name}",
                    'phone': phone,
                }
            )
    
    # No conflicts, can create new customer
    return None


def create_customer_if_needed(customer_id, first_name, last_name, phone):
    """
    Create customer if it doesn't exist, or reuse existing one.
    
    Returns:
        Customer object
    
    Raises:
        CustomerWarningError if warning detected
    """
    existing = check_and_get_customer(customer_id, first_name, last_name, phone)
    
    if existing:
        return existing
    
    # Create new customer
    new_customer = Customer.objects.create(
        customer_id=customer_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )
    logger.info(f"[CUSTOMER] Created new customer: {new_customer.id}")
    return new_customer


# ============================================================================
# Feedback Duplicate Detection
# ============================================================================

def check_feedback_duplicate(customer, category_code, confirm=False):
    """
    Feedback duplicate detection logic:
    - Same customer + same category_code + same day → BLOCK (raise FeedbackDuplicateError)
    - Same customer + same category_code + different day → WARNING (raise FeedbackWarning unless confirm=True)
    
    Returns:
        None if no duplicates or confirmed
    
    Raises:
        FeedbackDuplicateError for same-day duplicates
        FeedbackWarning for different-day duplicates without confirmation
    """
    today = date.today()
    
    # Check 1: Same customer + category + today?
    same_day_feedback = Feedback.objects.filter(
        customer=customer,
        category_code=category_code,
        created_at__date=today
    ).first()
    
    if same_day_feedback:
        # Same day duplicate → BLOCK
        logger.error(
            f"[FEEDBACK] Same-day duplicate: customer={customer.customer_id}, "
            f"category={category_code}, existing_feedback_id={same_day_feedback.id}"
        )
        
        raise FeedbackDuplicateError(
            message=(
                f"Duplicate feedback detected: Customer {customer.customer_id} "
                f"already submitted feedback for category '{category_code}' today"
            ),
            detail={
                'customer_id': customer.customer_id,
                'category_code': category_code,
                'existing_feedback_id': same_day_feedback.id,
                'existing_feedback_date': same_day_feedback.created_at.date().isoformat(),
            }
        )
    
    # Check 2: Same customer + category but different day?
    other_day_feedback = Feedback.objects.filter(
        customer=customer,
        category_code=category_code
    ).exclude(created_at__date=today).first()
    
    if other_day_feedback and not confirm:
        # Different day duplicate + no confirm → WARNING
        logger.warning(
            f"[FEEDBACK] Different-day duplicate: customer={customer.customer_id}, "
            f"category={category_code}, previous_date={other_day_feedback.created_at.date()}"
        )
        
        raise FeedbackWarning(
            message=(
                f"Customer {customer.customer_id} previously submitted "
                f"feedback for category '{category_code}' on "
                f"{other_day_feedback.created_at.date()}. "
                f"Add 'confirm=true' to proceed anyway."
            ),
            detail={
                'customer_id': customer.customer_id,
                'category_code': category_code,
                'existing_feedback_id': other_day_feedback.id,
                'existing_feedback_date': other_day_feedback.created_at.date().isoformat(),
                'action_required': 'Set confirm=true to proceed',
            }
        )
    
    # No duplicates or user confirmed
    return None


def create_feedback(customer, category_code, content=None, confirm=False):
    """
    Create feedback after duplicate checks.
    
    Returns:
        Feedback object
    
    Raises:
        FeedbackDuplicateError for same-day duplicates (409)
        FeedbackWarningError for different-day duplicates without confirmation (400)
    """
    check_feedback_duplicate(customer, category_code, confirm)
    
    # Create new feedback
    new_feedback = Feedback.objects.create(
        customer=customer,
        category_code=category_code,
        content=content
    )
    logger.info(f"[FEEDBACK] Created new feedback: {new_feedback.id}")
    return new_feedback


# ============================================================================
# Full workflow example
# ============================================================================

def create_full_feedback_entry(store_id, store_name, customer_id, first_name, 
                                last_name, phone, category_code, content=None, 
                                confirm=False):
    """
    Example of full workflow using all duplicate detection functions.
    This is just a demonstration - adapt as needed.
    
    Returns:
        dict with created objects
    
    Raises:
        StoreConflictError: 409 - store_id exists with different name
        CustomerWarningError: 400 - customer data conflicts
        FeedbackDuplicateError: 409 - same-day feedback duplicate
        FeedbackWarningError: 400 - different-day feedback duplicate without confirmation
    """
    # Step 1: Check/Create Store
    store = create_store_if_needed(store_id, store_name)
    
    # Step 2: Check/Create Customer
    customer = create_customer_if_needed(customer_id, first_name, last_name, phone)
    
    # Step 3: Check/Create Feedback
    feedback = create_feedback(customer, category_code, content, confirm)
    
    return {
        'store': store,
        'customer': customer,
        'feedback': feedback
    }
