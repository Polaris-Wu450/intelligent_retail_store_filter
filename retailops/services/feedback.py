import logging
from datetime import date
from ..models import ActionPlan, Feedback
from ..exceptions import FeedbackDuplicateError, FeedbackWarning
from .store import create_store_if_needed
from .customer import create_customer_if_needed

logger = logging.getLogger(__name__)

_CATEGORY_DISPLAY = {
    'FURNITURE': 'Furniture',
    'ELECTRONICS': 'Electronics',
    'CLOTHING': 'Clothing',
}


def check_feedback_duplicate(store, customer, category_code, confirm=False):
    """
    Duplicate detection rules:
    - Same store + customer + category + today → block (FeedbackDuplicateError 409)
    - Same store + customer + category + different day → warn unless confirm=True (FeedbackWarning 200)
    """
    today = date.today()
    category_display = _CATEGORY_DISPLAY.get(category_code, category_code)

    same_day = Feedback.objects.filter(
        store=store,
        customer=customer,
        category_code=category_code,
        created_at__date=today,
    ).first()

    if same_day:
        logger.error(
            f"[FEEDBACK] Same-day duplicate: store={store.store_id}, "
            f"customer={customer.customer_id}, category={category_code}"
        )
        raise FeedbackDuplicateError(
            message=(
                f"You have already submitted feedback for {category_display} at "
                f"{store.name} today. Please select a different category or submit tomorrow."
            ),
            detail={
                'store_id': store.store_id,
                'store_name': store.name,
                'customer_id': customer.customer_id,
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'category_code': category_code,
                'category_display': category_display,
                'existing_feedback_id': same_day.id,
                'existing_feedback_date': same_day.created_at.isoformat(),
                'reason': 'Duplicate feedback for same store, customer, category, and date',
            },
        )

    other_day = (
        Feedback.objects.filter(
            store=store,
            customer=customer,
            category_code=category_code,
        )
        .exclude(created_at__date=today)
        .order_by('-created_at')
        .first()
    )

    if other_day and not confirm:
        previous_date = other_day.created_at.strftime('%B %d, %Y')
        logger.warning(
            f"[FEEDBACK] Different-day duplicate: store={store.store_id}, "
            f"customer={customer.customer_id}, category={category_code}"
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
                'existing_feedback_id': other_day.id,
                'existing_feedback_date': other_day.created_at.isoformat(),
                'action_required': 'Click "Confirm & Continue" to proceed',
            },
        )

    return None


def create_feedback(store, customer, category_code, content=None, confirm=False):
    """Create feedback after duplicate checks pass."""
    check_feedback_duplicate(store, customer, category_code, confirm)
    feedback = Feedback.objects.create(
        store=store,
        customer=customer,
        category_code=category_code,
        content=content,
    )
    logger.info(f"[FEEDBACK] Created feedback: {feedback.id} (store={store.store_id})")
    return feedback


def create_full_feedback_entry(
    store_id, store_name, first_name, last_name, phone,
    category_code, content=None, confirm=False
):
    """
    Full workflow: resolve store → resolve customer → create feedback → create + dispatch ActionPlan.
    Returns dict with store, customer, feedback, action_plan.
    """
    from .action_plan import dispatch_action_plan_task

    store = create_store_if_needed(store_id, store_name)
    customer = create_customer_if_needed(first_name, last_name, phone)
    feedback = create_feedback(store, customer, category_code, content, confirm)

    action_plan = ActionPlan.objects.create(
        feedback=feedback,
        store_name=store_name,
        store_location=f"Store ID: {store_id}",
        issue_description=(
            f"Customer feedback from {customer.first_name} {customer.last_name} "
            f"regarding {category_code}: {content or '(No details provided)'}"
        ),
        status='pending',
    )
    logger.info(
        f"[FEEDBACK] Created ActionPlan: {action_plan.id} (Feedback: {feedback.id})"
    )

    dispatch_action_plan_task(action_plan.id)

    return {
        'store': store,
        'customer': customer,
        'feedback': feedback,
        'action_plan': action_plan,
    }
