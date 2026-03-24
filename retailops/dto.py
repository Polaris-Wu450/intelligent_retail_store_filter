"""
Data Transfer Objects (DTOs) for internal data normalization
Provides unified format for feedback data from multiple sources
"""
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class InternalFeedback:
    """
    Internal standard format for feedback data
    All external data sources should be converted to this format
    """
    # Required fields (no defaults)
    customer_id: str
    store_id: str
    category_code: str
    
    # Optional customer information
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    
    # Optional store information
    store_name: str = ""
    
    # Optional feedback information
    content: str = ""
    
    # Optional metadata
    source: str = ""  # Track which data source this came from
    raw_data: dict = field(default_factory=dict, repr=False)  # Keep original data for debugging
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.customer_id:
            raise ValueError("customer_id is required")
        if not self.store_id:
            raise ValueError("store_id is required")
        if not self.category_code:
            raise ValueError("category_code is required")
    
    def to_dict(self):
        """Convert to dictionary (excluding raw_data)"""
        return {
            'customer_id': self.customer_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'store_id': self.store_id,
            'store_name': self.store_name,
            'category_code': self.category_code,
            'content': self.content,
            'source': self.source,
        }


class FeedbackAdapter:
    """
    Adapters to convert different data sources to InternalFeedback format
    Each method handles one specific data source format
    """
    
    @staticmethod
    def from_small_chain_store(data: dict) -> InternalFeedback:
        """
        Adapter for small chain store JSON format
        
        Expected fields:
        - cust_id
        - cust_fname
        - cust_lname (optional)
        - cust_phone (optional)
        - shop_id
        - shop_name (optional)
        - feedback_type
        - feedback_content (optional)
        """
        logger.info(f"[ADAPTER] Converting small chain store data: {data.get('cust_id')}")
        
        try:
            return InternalFeedback(
                customer_id=str(data['cust_id']),
                first_name=data.get('cust_fname', ''),
                last_name=data.get('cust_lname', ''),
                phone=data.get('cust_phone', ''),
                store_id=str(data['shop_id']),
                store_name=data.get('shop_name', ''),
                category_code=data['feedback_type'],
                content=data.get('feedback_content', ''),
                source='small_chain_store',
                raw_data=data
            )
        except KeyError as e:
            logger.error(f"[ADAPTER] Missing required field in small chain store data: {e}")
            raise ValueError(f"Missing required field: {e}")
    
    @staticmethod
    def from_large_mall_partner(data: dict) -> InternalFeedback:
        """
        Adapter for large mall partner XML-to-dict format
        
        Expected fields:
        - CustomerID
        - CustomerFirstName (optional)
        - CustomerLastName (optional)
        - ContactPhone (optional)
        - StoreCode
        - StoreName (optional)
        - ComplaintCategory
        - ComplaintDescription (optional)
        """
        logger.info(f"[ADAPTER] Converting large mall partner data: {data.get('CustomerID')}")
        
        try:
            return InternalFeedback(
                customer_id=str(data['CustomerID']),
                first_name=data.get('CustomerFirstName', ''),
                last_name=data.get('CustomerLastName', ''),
                phone=data.get('ContactPhone', ''),
                store_id=str(data['StoreCode']),
                store_name=data.get('StoreName', ''),
                category_code=data['ComplaintCategory'],
                content=data.get('ComplaintDescription', ''),
                source='large_mall_partner',
                raw_data=data
            )
        except KeyError as e:
            logger.error(f"[ADAPTER] Missing required field in large mall partner data: {e}")
            raise ValueError(f"Missing required field: {e}")
    
    @staticmethod
    def from_ecommerce_platform(data: dict) -> InternalFeedback:
        """
        Adapter for e-commerce platform feedback format
        
        Expected fields:
        - buyer_id
        - buyer_name (optional)
        - buyer_mobile (optional)
        - store_no
        - store_title (optional)
        - issue_tag
        - issue_detail (optional)
        """
        logger.info(f"[ADAPTER] Converting e-commerce platform data: {data.get('buyer_id')}")
        
        try:
            # Handle buyer_name (may contain full name or just first name)
            buyer_name = data.get('buyer_name', '')
            name_parts = buyer_name.split(' ', 1) if buyer_name else ['', '']
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            return InternalFeedback(
                customer_id=str(data['buyer_id']),
                first_name=first_name,
                last_name=last_name,
                phone=data.get('buyer_mobile', ''),
                store_id=str(data['store_no']),
                store_name=data.get('store_title', ''),
                category_code=data['issue_tag'],
                content=data.get('issue_detail', ''),
                source='ecommerce_platform',
                raw_data=data
            )
        except KeyError as e:
            logger.error(f"[ADAPTER] Missing required field in e-commerce platform data: {e}")
            raise ValueError(f"Missing required field: {e}")
    
    @staticmethod
    def auto_detect_and_convert(data: dict) -> InternalFeedback:
        """
        Automatically detect data source format and convert
        
        Detection logic:
        - If has 'cust_id' -> small chain store
        - If has 'CustomerID' -> large mall partner
        - If has 'buyer_id' -> e-commerce platform
        """
        if 'cust_id' in data:
            return FeedbackAdapter.from_small_chain_store(data)
        elif 'CustomerID' in data:
            return FeedbackAdapter.from_large_mall_partner(data)
        elif 'buyer_id' in data:
            return FeedbackAdapter.from_ecommerce_platform(data)
        else:
            raise ValueError(
                "Unable to detect data source format. "
                "Expected one of: cust_id, CustomerID, or buyer_id"
            )
