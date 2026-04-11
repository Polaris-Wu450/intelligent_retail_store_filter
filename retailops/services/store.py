import logging
from ..models import Store
from ..exceptions import StoreConflictError
from ..metrics import dedup_events_total

logger = logging.getLogger(__name__)


def check_and_get_store(store_id, name):
    """
    Store duplicate detection:
    - Same store_id + same name → reuse existing
    - Same store_id + different name → raise StoreWarning (200)
    - Not found → return None (caller should create)
    """
    try:
        existing_store = Store.objects.get(store_id=store_id)
        if existing_store.name == name:
            logger.info(f"[STORE] Reusing existing store: {existing_store.id}")
            return existing_store
        dedup_events_total.labels(type='store_conflict').inc()
        logger.warning(
            f"[STORE] Name mismatch for {store_id}: "
            f"existing='{existing_store.name}' provided='{name}'"
        )
        raise StoreConflictError(
            message=(
                f'Store ID {store_id} already exists with name "{existing_store.name}", '
                f'but you provided "{name}"'
            ),
            detail={
                'store_id': store_id,
                'existing_store_id': existing_store.id,
                'existing_name': existing_store.name,
                'provided_name': name,
            },
        )
    except Store.DoesNotExist:
        return None


def create_store_if_needed(store_id, name):
    """Return existing store or create a new one."""
    existing = check_and_get_store(store_id, name)
    if existing:
        return existing
    new_store = Store.objects.create(store_id=store_id, name=name)
    logger.info(f"[STORE] Created new store: {new_store.id}")
    return new_store
