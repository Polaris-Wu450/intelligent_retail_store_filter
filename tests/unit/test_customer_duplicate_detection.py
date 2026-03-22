"""
Unit tests for Customer duplicate detection logic

Tests cover all scenarios:
1. Customer ID same + name and phone all same → reuse existing
2. Customer ID same + name or phone different → warning
3. Name + phone same + Customer ID different → warning
4. No conflicts → create new customer
"""
import pytest
from django.test import TestCase
from retailops.models import Customer
from retailops.services import (
    check_and_get_customer,
    create_customer_if_needed
)
from retailops.exceptions import CustomerWarning


@pytest.mark.unit
@pytest.mark.django_db
class TestCheckAndGetCustomer:
    """Unit tests for check_and_get_customer function"""
    
    def test_no_existing_customer_returns_none(self, sample_customer_data):
        """Test: No existing customer → returns None (should create new)"""
        result = check_and_get_customer(
            customer_id=sample_customer_data['customer_id'],
            first_name=sample_customer_data['first_name'],
            last_name=sample_customer_data['last_name'],
            phone=sample_customer_data['phone']
        )
        
        assert result is None
    
    def test_exact_match_reuses_existing_customer(self, sample_customer_data):
        """Test: CID same + name and phone same → reuse existing"""
        # Create existing customer
        existing = Customer.objects.create(**sample_customer_data)
        
        # Try to check with same data
        result = check_and_get_customer(
            customer_id=sample_customer_data['customer_id'],
            first_name=sample_customer_data['first_name'],
            last_name=sample_customer_data['last_name'],
            phone=sample_customer_data['phone']
        )
        
        assert result is not None
        assert result.id == existing.id
        assert result.customer_id == sample_customer_data['customer_id']
    
    def test_same_cid_different_name_raises_warning(self, sample_customer_data):
        """Test: CID same + name different → raises CustomerWarning"""
        # Create existing customer
        Customer.objects.create(**sample_customer_data)
        
        # Try with same CID but different name
        with pytest.raises(CustomerWarning) as exc_info:
            check_and_get_customer(
                customer_id=sample_customer_data['customer_id'],
                first_name='Jane',  # Different first name
                last_name=sample_customer_data['last_name'],
                phone=sample_customer_data['phone']
            )
        
        # Verify exception details
        exception = exc_info.value
        assert exception.type == 'warning'
        assert exception.code == 'CUSTOMER_DATA_MISMATCH'
        assert 'different information' in exception.message.lower()
        assert exception.detail is not None
        assert 'existing_name' in exception.detail
        assert 'provided_name' in exception.detail
    
    def test_same_cid_different_phone_raises_warning(self, sample_customer_data):
        """Test: CID same + phone different → raises CustomerWarning"""
        # Create existing customer
        Customer.objects.create(**sample_customer_data)
        
        # Try with same CID but different phone
        with pytest.raises(CustomerWarning) as exc_info:
            check_and_get_customer(
                customer_id=sample_customer_data['customer_id'],
                first_name=sample_customer_data['first_name'],
                last_name=sample_customer_data['last_name'],
                phone='9876543210'  # Different phone
            )
        
        # Verify exception details
        exception = exc_info.value
        assert exception.type == 'warning'
        assert exception.code == 'CUSTOMER_DATA_MISMATCH'
        assert 'different information' in exception.message.lower()
        assert exception.detail is not None
        assert 'existing_phone' in exception.detail
        assert 'provided_phone' in exception.detail
    
    def test_same_cid_different_name_and_phone_raises_warning(self, sample_customer_data):
        """Test: CID same + both name and phone different → raises CustomerWarning"""
        # Create existing customer
        Customer.objects.create(**sample_customer_data)
        
        # Try with same CID but different name and phone
        with pytest.raises(CustomerWarning) as exc_info:
            check_and_get_customer(
                customer_id=sample_customer_data['customer_id'],
                first_name='Jane',  # Different
                last_name='Smith',  # Different
                phone='9876543210'  # Different
            )
        
        # Verify exception details
        exception = exc_info.value
        assert exception.type == 'warning'
        assert 'existing_name' in exception.detail
        assert 'provided_name' in exception.detail
        assert 'existing_phone' in exception.detail
        assert 'provided_phone' in exception.detail
    
    def test_different_cid_same_name_phone_raises_warning(self, sample_customer_data):
        """Test: Name+phone same + CID different → raises CustomerWarning"""
        # Create existing customer
        Customer.objects.create(**sample_customer_data)
        
        # Try with different CID but same name and phone
        with pytest.raises(CustomerWarning) as exc_info:
            check_and_get_customer(
                customer_id='CU999',  # Different CID
                first_name=sample_customer_data['first_name'],
                last_name=sample_customer_data['last_name'],
                phone=sample_customer_data['phone']
            )
        
        # Verify exception details
        exception = exc_info.value
        assert exception.type == 'warning'
        assert exception.code == 'CUSTOMER_DATA_MISMATCH'
        assert 'already exists' in exception.message.lower()
        assert exception.detail is not None
        assert 'existing_cid' in exception.detail
        assert 'provided_cid' in exception.detail
        assert exception.detail['existing_cid'] == sample_customer_data['customer_id']
        assert exception.detail['provided_cid'] == 'CU999'
    
    def test_multiple_customers_only_checks_exact_matches(self, sample_customer_data):
        """Test: Multiple customers exist, but none match → returns None"""
        # Create multiple customers with different data
        Customer.objects.create(
            customer_id='CU002',
            first_name='Jane',
            last_name='Smith',
            phone='9876543210'
        )
        Customer.objects.create(
            customer_id='CU003',
            first_name='Bob',
            last_name='Johnson',
            phone='5555555555'
        )
        
        # Try with new customer data
        result = check_and_get_customer(
            customer_id=sample_customer_data['customer_id'],
            first_name=sample_customer_data['first_name'],
            last_name=sample_customer_data['last_name'],
            phone=sample_customer_data['phone']
        )
        
        assert result is None


@pytest.mark.unit
@pytest.mark.django_db
class TestCreateCustomerIfNeeded:
    """Unit tests for create_customer_if_needed function"""
    
    def test_creates_new_customer_when_none_exists(self, sample_customer_data):
        """Test: No existing customer → creates new one"""
        initial_count = Customer.objects.count()
        
        customer = create_customer_if_needed(
            customer_id=sample_customer_data['customer_id'],
            first_name=sample_customer_data['first_name'],
            last_name=sample_customer_data['last_name'],
            phone=sample_customer_data['phone']
        )
        
        assert Customer.objects.count() == initial_count + 1
        assert customer.customer_id == sample_customer_data['customer_id']
        assert customer.first_name == sample_customer_data['first_name']
        assert customer.last_name == sample_customer_data['last_name']
        assert customer.phone == sample_customer_data['phone']
    
    def test_reuses_existing_customer_on_exact_match(self, sample_customer_data):
        """Test: Exact match → reuses existing, doesn't create new"""
        # Create existing customer
        existing = Customer.objects.create(**sample_customer_data)
        initial_count = Customer.objects.count()
        
        # Try to create with same data
        customer = create_customer_if_needed(
            customer_id=sample_customer_data['customer_id'],
            first_name=sample_customer_data['first_name'],
            last_name=sample_customer_data['last_name'],
            phone=sample_customer_data['phone']
        )
        
        # Should reuse, not create new
        assert Customer.objects.count() == initial_count
        assert customer.id == existing.id
    
    def test_raises_warning_on_cid_conflict(self, sample_customer_data):
        """Test: CID conflict → raises CustomerWarning, doesn't create"""
        # Create existing customer
        Customer.objects.create(**sample_customer_data)
        initial_count = Customer.objects.count()
        
        # Try with same CID but different data
        with pytest.raises(CustomerWarning):
            create_customer_if_needed(
                customer_id=sample_customer_data['customer_id'],
                first_name='Jane',  # Different
                last_name='Smith',  # Different
                phone=sample_customer_data['phone']
            )
        
        # Should not create new customer
        assert Customer.objects.count() == initial_count
    
    def test_raises_warning_on_name_phone_conflict(self, sample_customer_data):
        """Test: Name+phone conflict → raises CustomerWarning, doesn't create"""
        # Create existing customer
        Customer.objects.create(**sample_customer_data)
        initial_count = Customer.objects.count()
        
        # Try with different CID but same name+phone
        with pytest.raises(CustomerWarning):
            create_customer_if_needed(
                customer_id='CU999',  # Different
                first_name=sample_customer_data['first_name'],
                last_name=sample_customer_data['last_name'],
                phone=sample_customer_data['phone']
            )
        
        # Should not create new customer
        assert Customer.objects.count() == initial_count


@pytest.mark.unit
@pytest.mark.django_db
class TestCustomerWarningExceptionDetails:
    """Test CustomerWarning exception provides correct details"""
    
    def test_warning_contains_all_required_fields(self, sample_customer_data):
        """Test: CustomerWarning has type, code, message, detail, status"""
        Customer.objects.create(**sample_customer_data)
        
        with pytest.raises(CustomerWarning) as exc_info:
            check_and_get_customer(
                customer_id=sample_customer_data['customer_id'],
                first_name='Jane',
                last_name='Smith',
                phone=sample_customer_data['phone']
            )
        
        exception = exc_info.value
        assert hasattr(exception, 'type')
        assert hasattr(exception, 'code')
        assert hasattr(exception, 'message')
        assert hasattr(exception, 'detail')
        assert hasattr(exception, 'http_status')
        
        assert exception.http_status == 200  # Warnings return 200
    
    def test_warning_to_dict_serializable(self, sample_customer_data):
        """Test: CustomerWarning.to_dict() returns serializable dict"""
        Customer.objects.create(**sample_customer_data)
        
        with pytest.raises(CustomerWarning) as exc_info:
            check_and_get_customer(
                customer_id=sample_customer_data['customer_id'],
                first_name='Jane',
                last_name='Smith',
                phone='9876543210'
            )
        
        exception = exc_info.value
        data = exception.to_dict()
        
        assert isinstance(data, dict)
        assert 'type' in data
        assert 'code' in data
        assert 'message' in data
        assert 'detail' in data
        
        # Should be JSON serializable
        import json
        json_str = json.dumps(data)
        assert isinstance(json_str, str)


@pytest.mark.unit
@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases for customer duplicate detection"""
    
    def test_empty_name_fields(self):
        """Test: Empty name fields are handled"""
        # This should work without error
        result = check_and_get_customer(
            customer_id='CU001',
            first_name='',
            last_name='',
            phone='1234567890'
        )
        assert result is None
    
    def test_empty_phone(self):
        """Test: Empty phone is handled"""
        result = check_and_get_customer(
            customer_id='CU001',
            first_name='John',
            last_name='Doe',
            phone=''
        )
        assert result is None
    
    def test_case_sensitive_name_matching(self):
        """Test: Names are case-sensitive"""
        # Create customer
        Customer.objects.create(
            customer_id='CU001',
            first_name='John',
            last_name='Doe',
            phone='1234567890'
        )
        
        # Try with different case
        with pytest.raises(CustomerWarning):
            check_and_get_customer(
                customer_id='CU001',
                first_name='john',  # lowercase
                last_name='doe',     # lowercase
                phone='1234567890'
            )
    
    def test_whitespace_in_names(self):
        """Test: Whitespace is not trimmed"""
        # Create customer
        Customer.objects.create(
            customer_id='CU001',
            first_name='John',
            last_name='Doe',
            phone='1234567890'
        )
        
        # Try with extra spaces
        with pytest.raises(CustomerWarning):
            check_and_get_customer(
                customer_id='CU001',
                first_name=' John ',  # Extra spaces
                last_name='Doe',
                phone='1234567890'
            )
