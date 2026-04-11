import logging
import time
from celery import shared_task
from .models import ActionPlan
from . import services
from .metrics import action_plan_total, celery_task_duration_seconds

logger = logging.getLogger(__name__)


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
    - Exponential backoff: 2s, 4s, 8s
    - Updates database status throughout process
    - Mock mode for testing (set USE_MOCK_LLM=true)
    """
    logger.info("🔥" * 40)
    logger.info("[TASKS] 📬 Celery task generate_action_plan() received!")
    logger.info(f"[TASKS] Task ID: {self.request.id}")
    logger.info(f"[TASKS] plan_id: {plan_id} (type: {type(plan_id)})")
    logger.info(f"[TASKS] Retry count: {self.request.retries}")
    
    start = time.time()
    try:
        logger.info("[TASKS] ➡️  Calling services.process_action_plan_generation()...")
        result = services.process_action_plan_generation(plan_id)
        logger.info(f"[TASKS] ⬅️  Services returned: {result}")
        logger.info("🔥" * 40)
        celery_task_duration_seconds.labels(task_name='generate_action_plan').observe(time.time() - start)
        action_plan_total.labels(status='completed').inc()
        return result

    except ActionPlan.DoesNotExist:
        logger.error(f"[TASKS] ❌ ActionPlan {plan_id} not found in database!")
        action_plan_total.labels(status='failed').inc()
        return {'status': 'error', 'message': f'ActionPlan {plan_id} not found'}

    except Exception as e:
        logger.error(f"[TASKS] ❌ Exception occurred: {type(e).__name__}: {str(e)}")
        logger.info("[TASKS] ➡️  Calling services.mark_action_plan_as_failed()...")
        services.mark_action_plan_as_failed(plan_id, e)
        logger.info("[TASKS] ⬅️  Plan marked as failed in database")
        action_plan_total.labels(status='failed').inc()
        celery_task_duration_seconds.labels(task_name='generate_action_plan').observe(time.time() - start)
        raise
