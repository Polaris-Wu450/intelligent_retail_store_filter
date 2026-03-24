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
    StoreWarning,
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
    """Retrieve all action plans, ordered by newest first"""
    return ActionPlan.objects.all().order_by('-created_at')


def get_mock_action_plan(action_plan):
    """
    Mock LLM response for testing (no API call, no cost, instant)
    """
    feedback = action_plan.feedback
    store_name = action_plan.store_name
    category_code = feedback.category_code if feedback else "GENERAL"
    
    return f"""## 🔴 PROBLEM SUMMARY
The {category_code} department at {store_name} is experiencing quality and availability issues that are frustrating customers.

---

## 🎯 GOALS (SMART)
1. Restore {category_code} inventory to 95% availability — Deadline: within 48 hours — Metric: Stock count audit shows <5% out-of-stock items
2. Achieve customer satisfaction rating of 4.5/5 for {category_code} — Deadline: by end of week — Metric: Post-purchase survey average

---

## ✅ MANAGER INTERVENTIONS
1. Store Manager → Conduct emergency inventory audit of {category_code} section and expedite restock orders → Due: within 6 hours
2. Department Lead → Train staff on product knowledge and customer service protocols for {category_code} → Due: by tomorrow
3. Regional Manager → Review supplier performance and negotiate faster delivery SLA → Due: within 3 days

---

## 📊 MONITORING PLAN
- Check-in 1: 24 hours — Verify inventory levels restored and staff training completed
- Check-in 2: 7 days — Review customer satisfaction scores and complaint volume
Success looks like: Zero customer complaints about {category_code} availability and quality for 3 consecutive days.

**MOCK DATA - FOR TESTING ONLY**"""


def call_llm_api(action_plan):
    """
    Call real LLM API with structured prompt
    """
    client = anthropic.Anthropic(api_key=settings.RETAILOPS_API_KEY)
    
    # Extract information from linked feedback
    feedback = action_plan.feedback
    store_name = action_plan.store_name
    store_id = feedback.store.store_id if feedback else "N/A"
    category_code = feedback.category_code if feedback else "GENERAL"
    feedback_content = feedback.content if feedback and feedback.content else action_plan.issue_description
    created_at = feedback.created_at.strftime("%B %d, %Y") if feedback else action_plan.created_at.strftime("%B %d, %Y")
    
    prompt = f"""You are a retail operations consultant generating an action plan 
for a regional manager. Be specific, actionable, and concise.

STORE INFORMATION:
- Store: {store_name} (ID: {store_id})
- Category with issue: {category_code}
- Customer feedback: {feedback_content}
- Date reported: {created_at}

Generate a structured action plan with EXACTLY these 4 sections.
Be specific to the {category_code} department. 
Do not use generic advice that could apply to any store.

---

## 🔴 PROBLEM SUMMARY
One sentence. What is the core issue in the {category_code} department?

---

## 🎯 GOALS (SMART)
Exactly 2 goals. Each must have:
- What: specific measurable outcome
- By when: exact deadline (e.g., "within 48 hours", "by end of week")
- How measured: one metric to confirm completion

Format:
1. [Goal] — Deadline: [X] — Metric: [Y]
2. [Goal] — Deadline: [X] — Metric: [Y]

---

## ✅ MANAGER INTERVENTIONS
Exactly 3 actions. Each must have:
- Owner: who does this (Store Manager / Department Lead / Regional Manager)
- Action: one specific thing to do, not vague
- Deadline: exact timeframe

Format:
1. [Owner] → [Specific action] → Due: [timeframe]
2. [Owner] → [Specific action] → Due: [timeframe]  
3. [Owner] → [Specific action] → Due: [timeframe]

---

## 📊 MONITORING PLAN
Exactly 2 checkpoints:
- Check-in 1: [when] — [what to verify]
- Check-in 2: [when] — [what to verify]
Success looks like: [one sentence defining resolution]

---

RULES:
- Total response must be under 300 words
- No bullet points except where format requires
- No generic advice like "improve customer service" or "conduct training"
- Every action must be specific to {category_code} issues
- If feedback is vague, make reasonable assumptions 
  based on common {category_code} department problems"""
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
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
        plan_content = get_mock_action_plan(plan)
        logger.info(f"[SERVICES] ✅ Mock LLM returned {len(plan_content)} characters")
    else:
        logger.info("[SERVICES] 🌐 Calling REAL Claude API...")
        plan_content = call_llm_api(plan)
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
    - Store ID same + name different → WARNING (200)
    
    Returns:
        Store object (existing or None if should create new)
    
    Raises:
        StoreWarning with details if store_id exists but name differs
    """
    try:
        existing_store = Store.objects.get(store_id=store_id)
        
        # Store ID exists, check name
        if existing_store.name == name:
            # Same store_id + same name → reuse
            logger.info(f"[STORE] Reusing existing store: {existing_store.id}")
            return existing_store
        else:
            # Same store_id + different name → WARNING
            logger.warning(
                f"[STORE] Store name mismatch: {store_id} "
                f"existing='{existing_store.name}' provided='{name}'"
            )
            raise StoreWarning(
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
        StoreWarning if name mismatch detected
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

def check_and_get_customer(first_name, last_name, phone):
    """
    Simplified customer lookup logic:
    - Searches for existing customer by first_name + last_name + phone
    - Returns customer if found, None if not
    
    Returns:
        Customer object if found, None otherwise
    """
    existing = Customer.objects.filter(
        first_name=first_name,
        last_name=last_name,
        phone=phone
    ).first()
    
    if existing:
        logger.info(f"[CUSTOMER] Found existing customer: {existing.customer_id} ({existing.first_name} {existing.last_name})")
        return existing
    
    logger.info(f"[CUSTOMER] No existing customer found for {first_name} {last_name} / {phone}")
    return None


def create_customer_if_needed(first_name, last_name, phone):
    """
    Create customer if it doesn't exist, or reuse existing one.
    Customer ID is auto-generated by database (not provided by user).
    
    Returns:
        Customer object (existing or newly created)
    """
    existing = check_and_get_customer(first_name, last_name, phone)
    
    if existing:
        return existing
    
    # Generate next customer ID (auto-increment pattern)
    # Get highest existing customer_id number
    last_customer = Customer.objects.order_by('-id').first()
    if last_customer and last_customer.customer_id:
        # Extract number from customer_id (e.g., "C001" → 1)
        try:
            last_num = int(last_customer.customer_id.replace('C', ''))
            next_num = last_num + 1
        except (ValueError, AttributeError):
            # Fallback if format is unexpected
            next_num = Customer.objects.count() + 1
    else:
        next_num = 1
    
    new_customer_id = f"C{next_num:03d}"  # e.g., C001, C002, C003
    
    # Create new customer
    new_customer = Customer.objects.create(
        customer_id=new_customer_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )
    logger.info(
        f"[CUSTOMER] Created new customer: {new_customer.id} "
        f"(Auto-generated CID: {new_customer_id})"
    )
    return new_customer


# ============================================================================
# Feedback Duplicate Detection
# ============================================================================

def check_feedback_duplicate(store, customer, category_code, confirm=False):
    """
    Feedback duplicate detection logic (now includes Store):
    - Same store + same customer + same category + same day → BLOCK (raise FeedbackDuplicateError)
    - Same store + same customer + same category + different day → WARNING (raise FeedbackWarning unless confirm=True)
    
    Returns:
        None if no duplicates or confirmed
    
    Raises:
        FeedbackDuplicateError for same-day duplicates
        FeedbackWarning for different-day duplicates without confirmation
    """
    today = date.today()
    
    # Category display names for user-friendly messages
    category_names = {
        'FURNITURE': 'Furniture',
        'ELECTRONICS': 'Electronics',
        'CLOTHING': 'Clothing'
    }
    category_display = category_names.get(category_code, category_code)
    
    # Check 1: Same store + customer + category + today?
    same_day_feedback = Feedback.objects.filter(
        store=store,
        customer=customer,
        category_code=category_code,
        created_at__date=today
    ).first()
    
    if same_day_feedback:
        # Same day duplicate → BLOCK
        logger.error(
            f"[FEEDBACK] Same-day duplicate: store={store.store_id}, "
            f"customer={customer.customer_id}, category={category_code}, "
            f"existing_feedback_id={same_day_feedback.id}"
        )
        
        raise FeedbackDuplicateError(
            message=(
                f"You have already submitted feedback for {category_display} at "
                f"{store.name} today. Duplicate submissions are not allowed for the same "
                f"store, customer, category, and date. Please select a different category "
                f"or submit tomorrow if you have additional concerns."
            ),
            detail={
                'store_id': store.store_id,
                'store_name': store.name,
                'customer_id': customer.customer_id,
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'category_code': category_code,
                'category_display': category_display,
                'existing_feedback_id': same_day_feedback.id,
                'existing_feedback_date': same_day_feedback.created_at.isoformat(),
                'reason': 'Duplicate feedback for same store, customer, category, and date'
            }
        )
    
    # Check 2: Same store + customer + category but different day?
    other_day_feedback = Feedback.objects.filter(
        store=store,
        customer=customer,
        category_code=category_code
    ).exclude(created_at__date=today).order_by('-created_at').first()
    
    if other_day_feedback and not confirm:
        # Different day duplicate + no confirm → WARNING
        previous_date = other_day_feedback.created_at.strftime('%B %d, %Y')
        logger.warning(
            f"[FEEDBACK] Different-day duplicate: store={store.store_id}, "
            f"customer={customer.customer_id}, category={category_code}, "
            f"previous_date={other_day_feedback.created_at.date()}"
        )
        
        raise FeedbackWarning(
            message=(
                f"You previously submitted feedback for {category_display} at "
                f"{store.name} on {previous_date}. Are you sure you want to submit again?"
            ),
            detail={
                'store_id': store.store_id,
                'store_name': store.name,
                'customer_id': customer.customer_id,
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'category_code': category_code,
                'category_display': category_display,
                'existing_feedback_id': other_day_feedback.id,
                'existing_feedback_date': other_day_feedback.created_at.isoformat(),
                'action_required': 'Click "Confirm & Continue" to proceed'
            }
        )
    
    # No duplicates or user confirmed
    return None


def create_feedback(store, customer, category_code, content=None, confirm=False):
    """
    Create feedback after duplicate checks (now includes Store).
    
    Returns:
        Feedback object
    
    Raises:
        FeedbackDuplicateError for same-day duplicates (409)
        FeedbackWarningError for different-day duplicates without confirmation (400)
    """
    check_feedback_duplicate(store, customer, category_code, confirm)
    
    # Create new feedback with store
    new_feedback = Feedback.objects.create(
        store=store,
        customer=customer,
        category_code=category_code,
        content=content
    )
    logger.info(f"[FEEDBACK] Created new feedback: {new_feedback.id} for store {store.store_id}")
    return new_feedback


# ============================================================================
# Full workflow example
# ============================================================================

def create_full_feedback_entry(store_id, store_name, first_name,
                                last_name, phone, category_code, content=None,
                                confirm=False):
    """
    Full workflow for creating feedback entry.
    Now automatically creates ActionPlan after successful feedback submission.
    
    Returns:
        dict with created objects (store, customer, feedback, action_plan)
    
    Raises:
        StoreWarning: 200 - store_id exists with different name
        FeedbackDuplicateError: 409 - same-day feedback duplicate
        FeedbackWarning: 200 - different-day feedback duplicate without confirmation
    """
    # Step 1: Check/Create Store
    store = create_store_if_needed(store_id, store_name)
    
    # Step 2: Check/Create Customer (auto-generates customer_id if new)
    customer = create_customer_if_needed(first_name, last_name, phone)
    
    # Step 3: Check/Create Feedback (now includes store)
    feedback = create_feedback(store, customer, category_code, content, confirm)
    
    # Step 4: Auto-create ActionPlan (linked to Feedback)
    logger.info("[FEEDBACK] Creating ActionPlan automatically...")
    action_plan = ActionPlan.objects.create(
        feedback=feedback,
        store_name=store_name,
        store_location=f"Store ID: {store_id}",
        issue_description=(
            f"Customer feedback from {customer.first_name} {customer.last_name} "
            f"regarding {category_code}: {content or '(No details provided)'}"
        ),
        status='pending'
    )
    logger.info(f"[FEEDBACK] Created ActionPlan: {action_plan.id} (linked to Feedback: {feedback.id})")
    
    # Step 5: Dispatch task to generate action plan
    logger.info("[FEEDBACK] Dispatching task to generate action plan...")
    dispatch_action_plan_task(action_plan.id)
    logger.info(f"[FEEDBACK] Task dispatched for ActionPlan: {action_plan.id}")
    
    return {
        'store': store,
        'customer': customer,
        'feedback': feedback,
        'action_plan': action_plan
    }
