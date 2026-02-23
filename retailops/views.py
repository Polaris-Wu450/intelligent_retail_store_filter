import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import ActionPlan
import anthropic


@csrf_exempt
@require_http_methods(["POST"])
def create_action_plan(request):
    # 🔍 BREAKPOINT 1: Function entry - inspect the raw incoming request
    data = json.loads(request.body)
    
    # 🔍 BREAKPOINT 2: After parsing - check the parsed JSON data
    store_name = data.get('store_name')
    store_location = data.get('store_location')
    issue_description = data.get('issue_description')
    
    # 🔍 BREAKPOINT 3: Database creation - see the newly created ActionPlan object
    action_plan = ActionPlan.objects.create(
        store_name=store_name,
        store_location=store_location,
        issue_description=issue_description,
        status='pending'
    )
    
    # 🔍 BREAKPOINT 4: Status update - confirm status changed to 'processing'
    action_plan.status = 'processing'
    action_plan.save()
    
    try:
        # 🔍 BREAKPOINT 5: LLM client initialization - verify API key is loaded
        client = anthropic.Anthropic(api_key=settings.RETAILOPS_API_KEY)
        
        # 🔍 BREAKPOINT 6: Prompt preparation - inspect the full prompt sent to LLM
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
        
        # 🔍 BREAKPOINT 7: LLM API call - this will take a few seconds to complete
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=800,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # 🔍 BREAKPOINT 8: LLM response - inspect the AI-generated content
        plan_content = message.content[0].text
        
        # 🔍 BREAKPOINT 9: Saving to database - verify data is correctly saved
        action_plan.status = 'completed'
        action_plan.plan_content = plan_content
        action_plan.save()
        
    except Exception as e:
        # 🔍 BREAKPOINT 10: Error handling - catch LLM API failures here
        action_plan.status = 'failed'
        action_plan.error_message = str(e)
        action_plan.save()
    
    # 🔍 BREAKPOINT 11: Before response - inspect the final data returned to frontend
    return JsonResponse({
        'id': action_plan.id,
        'store_name': action_plan.store_name,
        'store_location': action_plan.store_location,
        'issue_description': action_plan.issue_description,
        'status': action_plan.status,
        'plan_content': action_plan.plan_content,
        'error_message': action_plan.error_message,
        'created_at': action_plan.created_at.isoformat(),
        'updated_at': action_plan.updated_at.isoformat(),
    })


@require_http_methods(["GET"])
def get_action_plan(request, plan_id):
    try:
        action_plan = ActionPlan.objects.get(id=plan_id)
        return JsonResponse({
            'id': action_plan.id,
            'store_name': action_plan.store_name,
            'store_location': action_plan.store_location,
            'issue_description': action_plan.issue_description,
            'status': action_plan.status,
            'plan_content': action_plan.plan_content,
            'error_message': action_plan.error_message,
            'created_at': action_plan.created_at.isoformat(),
            'updated_at': action_plan.updated_at.isoformat(),
        })
    except ActionPlan.DoesNotExist:
        return JsonResponse({'error': 'Action plan not found'}, status=404)


@require_http_methods(["GET"])
def list_action_plans(request):
    action_plans = ActionPlan.objects.all()
    data = [{
        'id': plan.id,
        'store_name': plan.store_name,
        'store_location': plan.store_location,
        'issue_description': plan.issue_description,
        'status': plan.status,
        'plan_content': plan.plan_content,
        'error_message': plan.error_message,
        'created_at': plan.created_at.isoformat(),
        'updated_at': plan.updated_at.isoformat(),
    } for plan in action_plans]
    
    return JsonResponse({'action_plans': data})

