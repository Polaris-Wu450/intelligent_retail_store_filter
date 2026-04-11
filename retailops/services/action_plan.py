import os
import time
import logging
from ..models import ActionPlan

logger = logging.getLogger(__name__)


def create_action_plan(store_name, store_location, issue_description):
    """Create a new ActionPlan record with pending status."""
    action_plan = ActionPlan.objects.create(
        store_name=store_name,
        store_location=store_location,
        issue_description=issue_description,
        status='pending',
    )
    logger.info(f"[ACTION_PLAN] Created: id={action_plan.id}, store={store_name}")
    return action_plan


def dispatch_action_plan_task(action_plan_id):
    """Dispatch a Celery task to generate the action plan asynchronously."""
    from ..tasks import generate_action_plan
    task_result = generate_action_plan.delay(action_plan_id)
    logger.info(f"[ACTION_PLAN] Task dispatched: plan_id={action_plan_id}, task_id={task_result.id}")


def get_action_plan_by_id(plan_id):
    return ActionPlan.objects.get(id=plan_id)


def get_all_action_plans():
    return ActionPlan.objects.all().order_by('-created_at')


def get_mock_action_plan(action_plan):
    """Return a mock LLM response for testing (no API call, no cost)."""
    feedback = action_plan.feedback if action_plan.feedback_id else None
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
    """Call the configured LLM provider to generate an action plan."""
    from ..llm.llm_service import get_llm_service
    llm = get_llm_service()

    feedback = action_plan.feedback
    store_name = action_plan.store_name
    store_id = feedback.store.store_id if feedback and feedback.store else "N/A"
    category_code = feedback.category_code if feedback else "GENERAL"
    feedback_content = (
        feedback.content if feedback and feedback.content
        else action_plan.issue_description
    )
    created_at = (
        feedback.created_at.strftime("%B %d, %Y") if feedback
        else action_plan.created_at.strftime("%B %d, %Y")
    )

    prompt = f"""You are a retail operations consultant generating an action plan \
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
- If feedback is vague, make reasonable assumptions \
  based on common {category_code} department problems"""

    logger.info(f"[ACTION_PLAN] Using LLM provider: {llm.get_model_name()}")
    return llm.generate(prompt, max_tokens=1000)


def process_action_plan_generation(plan_id):
    """
    Business logic for generating an action plan (runs inside Celery worker).
    Updates DB status throughout: pending → processing → completed/failed.
    """
    logger.info(f"[ACTION_PLAN] process_action_plan_generation() called: plan_id={plan_id}")

    plan = ActionPlan.objects.get(id=plan_id)
    plan.status = 'processing'
    plan.save()

    use_mock = os.getenv('USE_MOCK_LLM', 'false').lower() == 'true'

    if use_mock:
        time.sleep(1)
        plan_content = get_mock_action_plan(plan)
    else:
        plan_content = call_llm_api(plan)

    plan.status = 'completed'
    plan.plan_content = plan_content
    plan.save()

    logger.info(f"[ACTION_PLAN] Completed: plan_id={plan_id}")
    return {'status': 'completed', 'plan_id': plan_id, 'mock': use_mock}


def mark_action_plan_as_failed(plan_id, error_message):
    """Mark an action plan as failed and record the error."""
    plan = ActionPlan.objects.get(id=plan_id)
    plan.status = 'failed'
    plan.error_message = str(error_message)
    plan.save()
