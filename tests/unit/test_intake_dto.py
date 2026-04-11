"""
Tests for InternalFeedback DTO and FeedbackAdapter
"""
import pytest
from retailops.intake.dto import InternalFeedback, FeedbackAdapter


class TestInternalFeedback:
    """Test InternalFeedback dataclass"""
    
    def test_create_minimal_feedback(self):
        """Test creating feedback with only required fields"""
        feedback = InternalFeedback(
            customer_id="C001",
            store_id="S001",
            category_code="complaint"
        )
        
        assert feedback.customer_id == "C001"
        assert feedback.store_id == "S001"
        assert feedback.category_code == "complaint"
        assert feedback.first_name == ""
        assert feedback.last_name == ""
        assert feedback.phone == ""
        assert feedback.store_name == ""
        assert feedback.content == ""
    
    def test_create_full_feedback(self):
        """Test creating feedback with all fields"""
        feedback = InternalFeedback(
            customer_id="C001",
            first_name="John",
            last_name="Doe",
            phone="1234567890",
            store_id="S001",
            store_name="Downtown Store",
            category_code="complaint",
            content="Product quality issue",
            source="test"
        )
        
        assert feedback.customer_id == "C001"
        assert feedback.first_name == "John"
        assert feedback.last_name == "Doe"
        assert feedback.phone == "1234567890"
        assert feedback.store_id == "S001"
        assert feedback.store_name == "Downtown Store"
        assert feedback.category_code == "complaint"
        assert feedback.content == "Product quality issue"
        assert feedback.source == "test"
    
    def test_missing_required_field_customer_id(self):
        """Test validation fails when customer_id is missing"""
        with pytest.raises(ValueError, match="customer_id is required"):
            InternalFeedback(
                customer_id="",
                store_id="S001",
                category_code="complaint"
            )
    
    def test_missing_required_field_store_id(self):
        """Test validation fails when store_id is missing"""
        with pytest.raises(ValueError, match="store_id is required"):
            InternalFeedback(
                customer_id="C001",
                store_id="",
                category_code="complaint"
            )
    
    def test_missing_required_field_category_code(self):
        """Test validation fails when category_code is missing"""
        with pytest.raises(ValueError, match="category_code is required"):
            InternalFeedback(
                customer_id="C001",
                store_id="S001",
                category_code=""
            )
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        feedback = InternalFeedback(
            customer_id="C001",
            first_name="John",
            last_name="Doe",
            phone="1234567890",
            store_id="S001",
            store_name="Downtown Store",
            category_code="complaint",
            content="Product quality issue",
            source="test",
            raw_data={"original": "data"}
        )
        
        result = feedback.to_dict()
        
        assert result['customer_id'] == "C001"
        assert result['first_name'] == "John"
        assert result['last_name'] == "Doe"
        assert result['phone'] == "1234567890"
        assert result['store_id'] == "S001"
        assert result['store_name'] == "Downtown Store"
        assert result['category_code'] == "complaint"
        assert result['content'] == "Product quality issue"
        assert result['source'] == "test"
        assert 'raw_data' not in result  # raw_data should be excluded


class TestFeedbackAdapter:
    """Test FeedbackAdapter for different data sources"""
    
    def test_from_small_chain_store_minimal(self):
        """Test adapter for small chain store with minimal fields"""
        data = {
            'cust_id': 'C001',
            'cust_fname': 'John',
            'shop_id': 'S001',
            'feedback_type': 'complaint'
        }
        
        feedback = FeedbackAdapter.from_small_chain_store(data)
        
        assert feedback.customer_id == 'C001'
        assert feedback.first_name == 'John'
        assert feedback.last_name == ''
        assert feedback.phone == ''
        assert feedback.store_id == 'S001'
        assert feedback.store_name == ''
        assert feedback.category_code == 'complaint'
        assert feedback.content == ''
        assert feedback.source == 'small_chain_store'
    
    def test_from_small_chain_store_full(self):
        """Test adapter for small chain store with all fields"""
        data = {
            'cust_id': 'C001',
            'cust_fname': 'John',
            'cust_lname': 'Doe',
            'cust_phone': '1234567890',
            'shop_id': 'S001',
            'shop_name': 'Downtown Store',
            'feedback_type': 'complaint',
            'feedback_content': 'Product quality issue'
        }
        
        feedback = FeedbackAdapter.from_small_chain_store(data)
        
        assert feedback.customer_id == 'C001'
        assert feedback.first_name == 'John'
        assert feedback.last_name == 'Doe'
        assert feedback.phone == '1234567890'
        assert feedback.store_id == 'S001'
        assert feedback.store_name == 'Downtown Store'
        assert feedback.category_code == 'complaint'
        assert feedback.content == 'Product quality issue'
        assert feedback.source == 'small_chain_store'
        assert feedback.raw_data == data
    
    def test_from_large_mall_partner_minimal(self):
        """Test adapter for large mall partner with minimal fields"""
        data = {
            'CustomerID': 'C002',
            'StoreCode': 'S002',
            'ComplaintCategory': 'service'
        }
        
        feedback = FeedbackAdapter.from_large_mall_partner(data)
        
        assert feedback.customer_id == 'C002'
        assert feedback.first_name == ''
        assert feedback.last_name == ''
        assert feedback.phone == ''
        assert feedback.store_id == 'S002'
        assert feedback.store_name == ''
        assert feedback.category_code == 'service'
        assert feedback.content == ''
        assert feedback.source == 'large_mall_partner'
    
    def test_from_large_mall_partner_full(self):
        """Test adapter for large mall partner with all fields"""
        data = {
            'CustomerID': 'C002',
            'CustomerFirstName': 'Jane',
            'CustomerLastName': 'Smith',
            'ContactPhone': '0987654321',
            'StoreCode': 'S002',
            'StoreName': 'Mall Branch',
            'ComplaintCategory': 'service',
            'ComplaintDescription': 'Slow checkout process'
        }
        
        feedback = FeedbackAdapter.from_large_mall_partner(data)
        
        assert feedback.customer_id == 'C002'
        assert feedback.first_name == 'Jane'
        assert feedback.last_name == 'Smith'
        assert feedback.phone == '0987654321'
        assert feedback.store_id == 'S002'
        assert feedback.store_name == 'Mall Branch'
        assert feedback.category_code == 'service'
        assert feedback.content == 'Slow checkout process'
        assert feedback.source == 'large_mall_partner'
        assert feedback.raw_data == data
    
    def test_from_ecommerce_platform_minimal(self):
        """Test adapter for e-commerce platform with minimal fields"""
        data = {
            'buyer_id': 'B003',
            'store_no': 'E003',
            'issue_tag': 'delivery'
        }
        
        feedback = FeedbackAdapter.from_ecommerce_platform(data)
        
        assert feedback.customer_id == 'B003'
        assert feedback.first_name == ''
        assert feedback.last_name == ''
        assert feedback.phone == ''
        assert feedback.store_id == 'E003'
        assert feedback.store_name == ''
        assert feedback.category_code == 'delivery'
        assert feedback.content == ''
        assert feedback.source == 'ecommerce_platform'
    
    def test_from_ecommerce_platform_full(self):
        """Test adapter for e-commerce platform with all fields"""
        data = {
            'buyer_id': 'B003',
            'buyer_name': 'Alice Wang',
            'buyer_mobile': '1122334455',
            'store_no': 'E003',
            'store_title': 'Online Store',
            'issue_tag': 'delivery',
            'issue_detail': 'Package arrived late'
        }
        
        feedback = FeedbackAdapter.from_ecommerce_platform(data)
        
        assert feedback.customer_id == 'B003'
        assert feedback.first_name == 'Alice'
        assert feedback.last_name == 'Wang'
        assert feedback.phone == '1122334455'
        assert feedback.store_id == 'E003'
        assert feedback.store_name == 'Online Store'
        assert feedback.category_code == 'delivery'
        assert feedback.content == 'Package arrived late'
        assert feedback.source == 'ecommerce_platform'
        assert feedback.raw_data == data
    
    def test_from_ecommerce_platform_single_name(self):
        """Test adapter handles single name (no space)"""
        data = {
            'buyer_id': 'B004',
            'buyer_name': 'Alice',
            'store_no': 'E004',
            'issue_tag': 'quality'
        }
        
        feedback = FeedbackAdapter.from_ecommerce_platform(data)
        
        assert feedback.first_name == 'Alice'
        assert feedback.last_name == ''
    
    def test_auto_detect_small_chain_store(self):
        """Test auto-detection of small chain store format"""
        data = {
            'cust_id': 'C001',
            'cust_fname': 'John',
            'shop_id': 'S001',
            'feedback_type': 'complaint'
        }
        
        feedback = FeedbackAdapter.auto_detect_and_convert(data)
        
        assert feedback.source == 'small_chain_store'
        assert feedback.customer_id == 'C001'
    
    def test_auto_detect_large_mall_partner(self):
        """Test auto-detection of large mall partner format"""
        data = {
            'CustomerID': 'C002',
            'StoreCode': 'S002',
            'ComplaintCategory': 'service'
        }
        
        feedback = FeedbackAdapter.auto_detect_and_convert(data)
        
        assert feedback.source == 'large_mall_partner'
        assert feedback.customer_id == 'C002'
    
    def test_auto_detect_ecommerce_platform(self):
        """Test auto-detection of e-commerce platform format"""
        data = {
            'buyer_id': 'B003',
            'store_no': 'E003',
            'issue_tag': 'delivery'
        }
        
        feedback = FeedbackAdapter.auto_detect_and_convert(data)
        
        assert feedback.source == 'ecommerce_platform'
        assert feedback.customer_id == 'B003'
    
    def test_auto_detect_unknown_format(self):
        """Test auto-detection fails for unknown format"""
        data = {
            'unknown_field': 'value',
            'another_field': 'value'
        }
        
        with pytest.raises(ValueError, match="Unable to detect data source format"):
            FeedbackAdapter.auto_detect_and_convert(data)
    
    def test_missing_required_field_in_adapter(self):
        """Test adapter fails when required field is missing"""
        data = {
            'cust_fname': 'John',
            'shop_id': 'S001',
            'feedback_type': 'complaint'
            # Missing cust_id
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            FeedbackAdapter.from_small_chain_store(data)
