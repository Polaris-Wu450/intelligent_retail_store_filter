"""
Prometheus metrics for RetailOps AI
Tracks business-specific metrics beyond django-prometheus defaults

Uses Redis for cross-process metric sharing (web + celery workers)
"""
from prometheus_client import Counter, Histogram, Gauge
import logging
import redis
import os

logger = logging.getLogger(__name__)

# Redis client for cross-process metrics
_redis_client = None

def get_redis_client():
    """Get Redis client for metrics storage"""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client

# ============================================================================
# Business Metrics
# ============================================================================

# Action Plan generation metrics
action_plan_created_total = Counter(
    'retailops_action_plan_created_total',
    'Total number of action plans created',
    ['status']
)

action_plan_generation_duration = Histogram(
    'retailops_action_plan_generation_seconds',
    'Time taken to generate action plan',
    ['status'],
    buckets=(1, 5, 10, 15, 30, 60, 120, 300)
)

# Feedback duplicate detection
feedback_duplicate_blocks = Counter(
    'retailops_feedback_duplicate_blocks_total',
    'Number of same-day duplicate feedback blocked',
    ['category_code']
)

feedback_duplicate_warnings = Counter(
    'retailops_feedback_duplicate_warnings_total',
    'Number of different-day duplicate feedback warnings',
    ['category_code']
)

# ============================================================================
# LLM Metrics
# ============================================================================

llm_api_calls_total = Counter(
    'retailops_llm_api_calls_total',
    'Total number of LLM API calls',
    ['provider', 'model', 'status']
)

llm_api_duration = Histogram(
    'retailops_llm_api_duration_seconds',
    'LLM API call duration',
    ['provider', 'model'],
    buckets=(0.5, 1, 2, 5, 10, 15, 30, 60)
)

llm_tokens_used = Counter(
    'retailops_llm_tokens_used_total',
    'Total tokens consumed by LLM API',
    ['provider', 'model', 'type']  # type: prompt_tokens / completion_tokens
)

llm_response_length = Histogram(
    'retailops_llm_response_length_chars',
    'LLM response length in characters',
    ['provider', 'model'],
    buckets=(100, 500, 1000, 2000, 5000, 10000)
)

# ============================================================================
# Error Metrics
# ============================================================================

store_name_mismatches = Counter(
    'retailops_store_name_mismatches_total',
    'Number of store name mismatch warnings',
    ['store_id']
)

# ============================================================================
# Celery Task Metrics
# ============================================================================

celery_task_queue_size = Gauge(
    'retailops_celery_queue_size',
    'Number of tasks in Celery queue',
    ['queue_name']
)

# ============================================================================
# Helper Functions
# ============================================================================

def record_action_plan_created(status: str):
    """Record action plan creation"""
    action_plan_created_total.labels(status=status).inc()
    try:
        r = get_redis_client()
        r.hincrby('metrics:action_plan_created', status, 1)
    except Exception as e:
        logger.warning(f"[METRICS] Failed to record to Redis: {e}")
    logger.debug(f"[METRICS] Recorded action_plan_created: status={status}")

def record_action_plan_generation(duration_seconds: float, status: str):
    """Record action plan generation duration"""
    action_plan_generation_duration.labels(status=status).observe(duration_seconds)
    try:
        r = get_redis_client()
        r.hincrbyfloat('metrics:action_plan_duration', f'{status}_total', duration_seconds)
        r.hincrby('metrics:action_plan_duration', f'{status}_count', 1)
    except Exception as e:
        logger.warning(f"[METRICS] Failed to record to Redis: {e}")
    logger.debug(f"[METRICS] Recorded action_plan_generation: duration={duration_seconds}s, status={status}")

def record_feedback_duplicate_block(category_code: str):
    """Record same-day duplicate feedback blocked"""
    feedback_duplicate_blocks.labels(category_code=category_code).inc()
    logger.debug(f"[METRICS] Recorded feedback_duplicate_block: category={category_code}")

def record_feedback_duplicate_warning(category_code: str):
    """Record different-day duplicate feedback warning"""
    feedback_duplicate_warnings.labels(category_code=category_code).inc()
    logger.debug(f"[METRICS] Recorded feedback_duplicate_warning: category={category_code}")

def record_llm_api_call(provider: str, model: str, status: str, duration_seconds: float):
    """Record LLM API call"""
    llm_api_calls_total.labels(provider=provider, model=model, status=status).inc()
    llm_api_duration.labels(provider=provider, model=model).observe(duration_seconds)
    try:
        r = get_redis_client()
        key = f'metrics:llm_calls:{provider}:{model}:{status}'
        r.incr(key)
        r.hincrbyfloat('metrics:llm_duration', f'{provider}:{model}', duration_seconds)
    except Exception as e:
        logger.warning(f"[METRICS] Failed to record to Redis: {e}")
    logger.debug(f"[METRICS] Recorded LLM call: provider={provider}, status={status}, duration={duration_seconds}s")

def record_llm_tokens(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    """Record LLM token usage"""
    llm_tokens_used.labels(provider=provider, model=model, type='prompt').inc(prompt_tokens)
    llm_tokens_used.labels(provider=provider, model=model, type='completion').inc(completion_tokens)
    try:
        r = get_redis_client()
        r.hincrby('metrics:llm_tokens', f'{provider}:{model}:prompt', prompt_tokens)
        r.hincrby('metrics:llm_tokens', f'{provider}:{model}:completion', completion_tokens)
    except Exception as e:
        logger.warning(f"[METRICS] Failed to record to Redis: {e}")
    logger.debug(f"[METRICS] Recorded tokens: prompt={prompt_tokens}, completion={completion_tokens}")

def record_llm_response_length(provider: str, model: str, length: int):
    """Record LLM response length"""
    llm_response_length.labels(provider=provider, model=model).observe(length)
    try:
        r = get_redis_client()
        r.hincrby('metrics:llm_response_length', f'{provider}:{model}', length)
    except Exception as e:
        logger.warning(f"[METRICS] Failed to record to Redis: {e}")
    logger.debug(f"[METRICS] Recorded response length: {length} chars")

def record_store_name_mismatch(store_id: str):
    """Record store name mismatch warning"""
    store_name_mismatches.labels(store_id=store_id).inc()
    logger.debug(f"[METRICS] Recorded store_name_mismatch: store_id={store_id}")

def update_celery_queue_size(queue_name: str, size: int):
    """Update Celery queue size gauge"""
    celery_task_queue_size.labels(queue_name=queue_name).set(size)
    logger.debug(f"[METRICS] Updated celery_queue_size: queue={queue_name}, size={size}")

def sync_metrics_from_redis():
    """
    Sync metrics from Redis to Prometheus
    Called when /api/metrics endpoint is accessed
    """
    try:
        r = get_redis_client()
        
        # Sync action plan created counts
        action_plan_data = r.hgetall('metrics:action_plan_created')
        for status, count in action_plan_data.items():
            action_plan_created_total.labels(status=status)._value.set(float(count))
        
        # Sync LLM API calls
        for key in r.scan_iter('metrics:llm_calls:*'):
            parts = key.split(':')
            if len(parts) == 5:
                provider, model, status = parts[2], parts[3], parts[4]
                count = r.get(key)
                if count:
                    llm_api_calls_total.labels(provider=provider, model=model, status=status)._value.set(float(count))
        
        # Sync LLM tokens
        token_data = r.hgetall('metrics:llm_tokens')
        for key, count in token_data.items():
            parts = key.split(':')
            if len(parts) == 3:
                provider, model, token_type = parts[0], parts[1], parts[2]
                llm_tokens_used.labels(provider=provider, model=model, type=token_type)._value.set(float(count))
        
        logger.debug("[METRICS] Synced metrics from Redis")
        
    except Exception as e:
        logger.warning(f"[METRICS] Failed to sync from Redis: {e}")
