"""
Error handling integration tests

Tests that invalid inputs generate the correct error responses
"""
import pytest
import json
from django.test import Client
from retailops.models import Store, Customer


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestValidationErrors:
    """Test validation error handling (400)"""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_missing_all_fields_returns_400(self, client):
        """Test: Empty request returns 400 validation error"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['type'] == 'validation_error'
        assert data['code'] == 'VALIDATION_FAILED'
        assert 'detail' in data
        assert 'missing_fields' in data['detail']
        
        # Should list all missing fields
        missing = data['detail']['missing_fields']
        assert 'store_id' in missing
        assert 'customer_id' in missing
        assert 'first_name' in missing
        assert 'last_name' in missing
        assert 'phone' in missing
        assert 'category_code' in missing
    
    def test_missing_some_fields_returns_400(self, client):
        """Test: Partial request returns 400 with missing fields"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps({
                'store_id': 'ST001',
                'store_name': 'Test Store',
                'customer_id': 'CU001'
                # Missing: first_name, last_name, phone, category_code
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['type'] == 'validation_error'
        
        missing = data['detail']['missing_fields']
        assert 'first_name' in missing
        assert 'last_name' in missing
        assert 'phone' in missing
        assert 'category_code' in missing
        
        # Should NOT include fields that were provided
        assert 'store_id' not in missing
        assert 'customer_id' not in missing
    
    def test_empty_string_fields_treated_as_missing(self, client):
        """Test: Empty strings are treated as missing"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps({
                'store_id': '',  # Empty
                'store_name': 'Test Store',
                'customer_id': 'CU001',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '1234567890',
                'category_code': 'SERVICE'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'store_id' in data['detail']['missing_fields']
    
    def test_null_fields_treated_as_missing(self, client):
        """Test: Null fields are treated as missing"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps({
                'store_id': 'ST001',
                'store_name': None,  # Null
                'customer_id': 'CU001',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '1234567890',
                'category_code': 'SERVICE'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'store_name' in data['detail']['missing_fields']


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestBlockErrors:
    """Test block error handling (409)"""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def initial_feedback(self, client, complete_feedback_request):
        """Create initial feedback for testing"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json'
        )
        assert response.status_code == 201
        return response.json()
    
    def test_store_id_conflict_returns_409(self, client, initial_feedback, complete_feedback_request):
        """Test: Store ID with different name returns 409"""
        # Try to create with same store_id but different name
        request = complete_feedback_request.copy()
        request['store_name'] = 'Completely Different Name'
        request['customer_id'] = 'CU002'
        request['phone'] = '9876543210'
        
        response = client.post(
            '/api/feedback/',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data['type'] == 'block_error'
        assert data['code'] == 'STORE_ID_CONFLICT'
        assert 'already exists' in data['message'].lower()
        
        # Detail should include both names
        assert 'detail' in data
        assert 'existing_name' in data['detail']
        assert 'provided_name' in data['detail']
        assert data['detail']['existing_name'] == 'Test Store A'
        assert data['detail']['provided_name'] == 'Completely Different Name'
    
    def test_same_day_feedback_duplicate_returns_409(self, client, initial_feedback, complete_feedback_request):
        """Test: Duplicate feedback same day returns 409"""
        # Try to create duplicate feedback
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data['type'] == 'block_error'
        assert data['code'] == 'FEEDBACK_DUPLICATE'
        assert 'already submitted' in data['message'].lower()
        
        # Detail should include customer_id and category_code
        assert 'detail' in data
        assert 'customer_id' in data['detail']
        assert 'category_code' in data['detail']
        assert 'existing_feedback_id' in data['detail']
    
    def test_block_errors_prevent_database_changes(self, client, initial_feedback, complete_feedback_request):
        """Test: Block errors don't create partial data"""
        initial_store_count = Store.objects.count()
        initial_customer_count = Customer.objects.count()
        
        # Try store conflict
        request = complete_feedback_request.copy()
        request['store_name'] = 'Different Name'
        request['customer_id'] = 'CU999'
        request['phone'] = '9999999999'
        
        response = client.post(
            '/api/feedback/',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        
        # No new stores or customers should be created
        assert Store.objects.count() == initial_store_count
        assert Customer.objects.count() == initial_customer_count


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestWarningHandling:
    """Test warning handling (200 with warnings)"""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def initial_feedback(self, client, complete_feedback_request):
        """Create initial feedback"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json'
        )
        assert response.status_code == 201
        return response.json()
    
    def test_customer_phone_mismatch_returns_200_with_warning(self, client, initial_feedback, complete_feedback_request):
        """Test: Customer phone mismatch returns 200 with warnings"""
        request = complete_feedback_request.copy()
        request['phone'] = '9876543210'  # Different phone
        request['category_code'] = 'PRODUCT'  # Different category to avoid feedback duplicate
        
        response = client.post(
            '/api/feedback/',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'warnings' in data
        assert len(data['warnings']) > 0
        
        warning = data['warnings'][0]
        assert warning['type'] == 'warning'
        assert warning['code'] == 'CUSTOMER_DATA_MISMATCH'
        assert 'detail' in warning
        assert 'existing_phone' in warning['detail']
        assert 'provided_phone' in warning['detail']
    
    def test_customer_name_mismatch_returns_200_with_warning(self, client, initial_feedback, complete_feedback_request):
        """Test: Customer name mismatch returns 200 with warnings"""
        request = complete_feedback_request.copy()
        request['first_name'] = 'Jane'  # Different name
        request['last_name'] = 'Smith'
        request['category_code'] = 'PRODUCT'
        
        response = client.post(
            '/api/feedback/',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'warnings' in data
        
        warning = data['warnings'][0]
        assert warning['type'] == 'warning'
        assert 'existing_name' in warning['detail']
        assert 'provided_name' in warning['detail']
    
    def test_warnings_array_structure(self, client, initial_feedback, complete_feedback_request):
        """Test: Warnings are in an array for future extensibility"""
        request = complete_feedback_request.copy()
        request['phone'] = '9876543210'
        request['category_code'] = 'PRODUCT'
        
        response = client.post(
            '/api/feedback/',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Warnings should be an array
        assert isinstance(data['warnings'], list)
        assert len(data['warnings']) > 0
        
        # Each warning should have standard fields
        for warning in data['warnings']:
            assert 'type' in warning
            assert 'code' in warning
            assert 'message' in warning


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestErrorResponseConsistency:
    """Test that all errors follow consistent format"""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_all_errors_have_type_field(self, client):
        """Test: All errors include 'type' field"""
        # Validation error
        response = client.post(
            '/api/feedback/',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert 'type' in response.json()
    
    def test_all_errors_have_code_field(self, client):
        """Test: All errors include 'code' field"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert 'code' in response.json()
    
    def test_all_errors_have_message_field(self, client):
        """Test: All errors include 'message' field"""
        response = client.post(
            '/api/feedback/',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert 'message' in response.json()
    
    def test_error_types_match_status_codes(self, client, complete_feedback_request):
        """Test: Error types correctly map to status codes"""
        # Create initial data
        client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json'
        )
        
        test_cases = [
            # (request, expected_status, expected_type)
            ({}, 400, 'validation_error'),
            # Store conflict
            ({
                **complete_feedback_request,
                'store_name': 'Different',
                'customer_id': 'CU999',
                'phone': '9999999999'
            }, 409, 'block_error'),
        ]
        
        for request_data, expected_status, expected_type in test_cases:
            response = client.post(
                '/api/feedback/',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == expected_status
            if response.status_code != 200:  # Warnings return 200
                data = response.json()
                assert data['type'] == expected_type
    
    def test_errors_are_json_serializable(self, client):
        """Test: All error responses are valid JSON"""
        import json as json_module
        
        response = client.post(
            '/api/feedback/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Should not raise exception
        data = response.json()
        assert isinstance(data, dict)
        
        # Re-serialize to ensure it's truly JSON-compatible
        json_str = json_module.dumps(data)
        assert isinstance(json_str, str)
