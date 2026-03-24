"""
Business logic for processing feedback data
All processing uses InternalFeedback format regardless of source
"""
import logging
from typing import List
from django.db import transaction

from retailops.dto import InternalFeedback, FeedbackAdapter
from retailops.models import Customer, Store, Feedback

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """
    Process feedback data in unified InternalFeedback format
    Handles: data validation, deduplication, persistence
    """
    
    @staticmethod
    def process_feedback(internal_feedback: InternalFeedback) -> Feedback:
        """
        Process a single feedback record
        
        Steps:
        1. Get or create customer
        2. Get or create store
        3. Create feedback record
        """
        logger.info(
            f"[PROCESSOR] Processing feedback from {internal_feedback.source} - "
            f"Customer: {internal_feedback.customer_id}, Store: {internal_feedback.store_id}"
        )
        
        with transaction.atomic():
            # Get or create customer
            customer, created = Customer.objects.get_or_create(
                customer_id=internal_feedback.customer_id,
                defaults={
                    'first_name': internal_feedback.first_name,
                    'last_name': internal_feedback.last_name,
                    'phone': internal_feedback.phone,
                }
            )
            
            if created:
                logger.info(f"[PROCESSOR] Created new customer: {customer.customer_id}")
            else:
                # Update customer info if provided and different
                if internal_feedback.first_name and customer.first_name != internal_feedback.first_name:
                    customer.first_name = internal_feedback.first_name
                if internal_feedback.last_name and customer.last_name != internal_feedback.last_name:
                    customer.last_name = internal_feedback.last_name
                if internal_feedback.phone and customer.phone != internal_feedback.phone:
                    customer.phone = internal_feedback.phone
                customer.save()
                logger.info(f"[PROCESSOR] Updated existing customer: {customer.customer_id}")
            
            # Get or create store
            store, created = Store.objects.get_or_create(
                store_id=internal_feedback.store_id,
                defaults={
                    'name': internal_feedback.store_name or internal_feedback.store_id,
                }
            )
            
            if created:
                logger.info(f"[PROCESSOR] Created new store: {store.store_id}")
            else:
                # Check for store name mismatch
                if internal_feedback.store_name and store.name != internal_feedback.store_name:
                    logger.warning(
                        f"[PROCESSOR] ⚠️ STORE NAME MISMATCH: "
                        f"store_id={store.store_id}, "
                        f"existing_name='{store.name}', "
                        f"new_name='{internal_feedback.store_name}', "
                        f"source={internal_feedback.source}"
                    )
                    # Update store name
                    store.name = internal_feedback.store_name
                    store.save()
                logger.info(f"[PROCESSOR] Using existing store: {store.store_id}")
            
            # Create feedback record
            feedback = Feedback.objects.create(
                customer=customer,
                category_code=internal_feedback.category_code,
                content=internal_feedback.content,
            )
            
            logger.info(f"[PROCESSOR] ✅ Created feedback record: {feedback.id}")
            return feedback
    
    @staticmethod
    def process_batch(raw_data_list: List[dict], auto_detect: bool = True) -> dict:
        """
        Process a batch of feedback records
        
        Args:
            raw_data_list: List of raw data from any source
            auto_detect: If True, auto-detect format. If False, must specify adapter
        
        Returns:
            Summary of processing results
        """
        logger.info(f"[PROCESSOR] Processing batch of {len(raw_data_list)} records")
        
        results = {
            'total': len(raw_data_list),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for idx, raw_data in enumerate(raw_data_list):
            try:
                # Convert to internal format
                if auto_detect:
                    internal_feedback = FeedbackAdapter.auto_detect_and_convert(raw_data)
                else:
                    # If not auto-detecting, caller must provide pre-converted InternalFeedback
                    internal_feedback = raw_data
                
                # Process the feedback
                FeedbackProcessor.process_feedback(internal_feedback)
                results['success'] += 1
                
            except Exception as e:
                logger.error(f"[PROCESSOR] Failed to process record {idx}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'index': idx,
                    'error': str(e),
                    'data': raw_data
                })
        
        logger.info(
            f"[PROCESSOR] ✅ Batch processing complete: "
            f"{results['success']} success, {results['failed']} failed"
        )
        
        return results


# Example usage functions for different data sources

def process_small_chain_store_batch(data_list: List[dict]) -> dict:
    """Process batch from small chain store"""
    logger.info(f"[PROCESSOR] Processing {len(data_list)} records from small chain store")
    
    internal_feedbacks = [
        FeedbackAdapter.from_small_chain_store(data)
        for data in data_list
    ]
    
    return FeedbackProcessor.process_batch(internal_feedbacks, auto_detect=False)


def process_large_mall_partner_batch(data_list: List[dict]) -> dict:
    """Process batch from large mall partner"""
    logger.info(f"[PROCESSOR] Processing {len(data_list)} records from large mall partner")
    
    internal_feedbacks = [
        FeedbackAdapter.from_large_mall_partner(data)
        for data in data_list
    ]
    
    return FeedbackProcessor.process_batch(internal_feedbacks, auto_detect=False)


def process_ecommerce_platform_batch(data_list: List[dict]) -> dict:
    """Process batch from e-commerce platform"""
    logger.info(f"[PROCESSOR] Processing {len(data_list)} records from e-commerce platform")
    
    internal_feedbacks = [
        FeedbackAdapter.from_ecommerce_platform(data)
        for data in data_list
    ]
    
    return FeedbackProcessor.process_batch(internal_feedbacks, auto_detect=False)


def process_mixed_source_batch(data_list: List[dict]) -> dict:
    """Process batch with mixed data sources (auto-detect format)"""
    logger.info(f"[PROCESSOR] Processing {len(data_list)} records with auto-detection")
    
    return FeedbackProcessor.process_batch(data_list, auto_detect=True)
