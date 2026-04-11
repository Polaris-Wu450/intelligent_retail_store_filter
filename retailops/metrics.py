"""
Prometheus custom metrics for RetailOps.

Business metrics are instrumented here and incremented in the service layer.
HTTP and DB metrics are provided automatically by django-prometheus.
"""
from prometheus_client import Counter, Histogram

# ── Business ──────────────────────────────────────────────────────────────────

feedback_submissions_total = Counter(
    'retailops_feedback_submissions_total',
    'Feedback submission outcomes',
    ['result'],  # created | blocked | warning
)

dedup_events_total = Counter(
    'retailops_dedup_events_total',
    'Duplicate-detection events fired',
    ['type'],  # same_day | different_day | store_conflict
)

action_plan_total = Counter(
    'retailops_action_plan_total',
    'Action plan lifecycle events',
    ['status'],  # created | completed | failed
)

# ── Performance ───────────────────────────────────────────────────────────────

celery_task_duration_seconds = Histogram(
    'retailops_celery_task_duration_seconds',
    'Celery task execution time in seconds',
    ['task_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)
