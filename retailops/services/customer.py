import logging
from ..models import Customer

logger = logging.getLogger(__name__)


def check_and_get_customer(first_name, last_name, phone):
    """Return existing customer matching all three fields, or None."""
    existing = Customer.objects.filter(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    ).first()
    if existing:
        logger.info(
            f"[CUSTOMER] Found existing customer: {existing.customer_id} "
            f"({existing.first_name} {existing.last_name})"
        )
        return existing
    logger.info(f"[CUSTOMER] No match for {first_name} {last_name} / {phone}")
    return None


def create_customer_if_needed(first_name, last_name, phone):
    """Return existing customer or create a new one with an auto-generated ID."""
    existing = check_and_get_customer(first_name, last_name, phone)
    if existing:
        return existing

    last_customer = Customer.objects.order_by('-id').first()
    if last_customer and last_customer.customer_id:
        try:
            last_num = int(last_customer.customer_id.replace('C', ''))
            next_num = last_num + 1
        except (ValueError, AttributeError):
            next_num = Customer.objects.count() + 1
    else:
        next_num = 1

    new_customer_id = f"C{next_num:03d}"
    new_customer = Customer.objects.create(
        customer_id=new_customer_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )
    logger.info(
        f"[CUSTOMER] Created new customer: {new_customer.id} (CID: {new_customer_id})"
    )
    return new_customer
