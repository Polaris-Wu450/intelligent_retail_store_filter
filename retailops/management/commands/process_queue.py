import redis
from django.core.management.base import BaseCommand
from django.conf import settings
from retailops.models import ActionPlan
from retailops.llm_service import get_llm_service


class Command(BaseCommand):
    help = 'Process pending action plans from Redis queue'
    
    def handle(self, *args, **options):
        redis_client = redis.from_url(settings.REDIS_URL)
        llm_service = get_llm_service()
        
        self.stdout.write(self.style.SUCCESS('Worker started. Listening to Redis queue...'))
        self.stdout.write(f'Queue: {settings.REDIS_QUEUE_NAME}')
        self.stdout.write(f'LLM Provider: {llm_service.get_model_name()}\n')
        
        while True:
            try:
                result = redis_client.blpop(settings.REDIS_QUEUE_NAME, timeout=5)
                
                if result is None:
                    self.stdout.write('.', ending='')
                    continue
                
                _, plan_id_bytes = result
                plan_id = int(plan_id_bytes.decode('utf-8'))
                
                self.stdout.write(f'\n📥 Received task: ActionPlan ID={plan_id}')
                self.process_action_plan(plan_id, llm_service)
                
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n\nWorker stopped by user.'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n❌ Error: {e}'))
    
    def process_action_plan(self, plan_id, llm_service):
        try:
            plan = ActionPlan.objects.get(id=plan_id)
            
            self.stdout.write(f'   Store: {plan.store_name}')
            self.stdout.write(f'   Issue: {plan.issue_description[:50]}...')
            
            plan.status = 'processing'
            plan.save()
            self.stdout.write(f'   Status: processing')
            
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
            
            self.stdout.write(f'   Calling LLM...')
            plan_content = llm_service.generate(prompt, max_tokens=800)
            
            plan.status = 'completed'
            plan.plan_content = plan_content
            plan.save()
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Completed! Plan saved to database\n'))
            
        except ActionPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'   ❌ ActionPlan {plan_id} not found in database'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Failed: {e}'))
            try:
                plan = ActionPlan.objects.get(id=plan_id)
                plan.status = 'failed'
                plan.error_message = str(e)
                plan.save()
            except:
                pass
