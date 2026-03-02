import anthropic
from celery import shared_task
from django.conf import settings
from .models import ActionPlan


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=False
)
def generate_action_plan(self, plan_id):
    """
    Celery task to generate action plan using LLM
    
    Features:
    - Automatic retry on failure (max 3 times)
    - Exponential backoff: 1s, 2s, 4s
    - Updates database status throughout process
    """
    try:
        plan = ActionPlan.objects.get(id=plan_id)
        
        plan.status = 'processing'
        plan.save()
        
        client = anthropic.Anthropic(api_key=settings.RETAILOPS_API_KEY)
        
        prompt = f"""You are a retail operations assistant helping B2B managers. Generate a CONCISE, actionable plan for this store issue.

Store Name: {plan.store_name}
Store Location: {plan.store_location}
Issue: {plan.issue_description}

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
        
        plan_content = message.content[0].text
        
        plan.status = 'completed'
        plan.plan_content = plan_content
        plan.save()
        
        return {'status': 'completed', 'plan_id': plan_id}
        
    except ActionPlan.DoesNotExist:
        return {'status': 'error', 'message': f'ActionPlan {plan_id} not found'}
    
    except Exception as e:
        plan = ActionPlan.objects.get(id=plan_id)
        plan.status = 'failed'
        plan.error_message = str(e)
        plan.save()
        raise
