"""
Business logic layer
Handles: Database operations, LLM API calls, Task dispatching
"""
import os
import time
import logging
import anthropic
from django.conf import settings
from .models import ActionPlan

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
