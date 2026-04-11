"""
Error handling integration tests.
Tests that invalid or conflicting inputs produce the correct error responses.
"""
import pytest
import json
from datetime import timedelta
from django.test import Client
from django.utils import timezone
from retailops.models import Store, Customer, Feedback


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestValidationErrors:

    @pytest.fixture
    def client(self):
        return Client()

    def test_missing_all_fields_returns_400(self, client):
        response = client.post(
            '/api/feedback/',
            data=json.dumps({}),
            content_type='application/json',
        )
        assert response.status_code == 400
        data = response.json()
        assert data['type'] == 'validation_error'
        assert data['code'] == 'VALIDATION_FAILED'
        assert 'missing_fields' in data['detail']

        missing = data['detail']['missing_fields']
        for field in ('store_id', 'store_name', 'first_name', 'last_name', 'phone', 'category_code'):
            assert field in missing

    def test_missing_some_fields_returns_400(self, client):
        response = client.post(
            '/api/feedback/',
            data=json.dumps({'store_id': 'ST001', 'store_name': 'Test Store'}),
            content_type='application/json',
        )
        assert response.status_code == 400
        data = response.json()
        assert data['type'] == 'validation_error'

        missing = data['detail']['missing_fields']
        assert 'first_name' in missing
        assert 'last_name' in missing
        assert 'phone' in missing
        assert 'category_code' in missing
        assert 'store_id' not in missing
        assert 'store_name' not in missing

    def test_empty_string_fields_treated_as_missing(self, client):
        response = client.post(
            '/api/feedback/',
            data=json.dumps({
                'store_id': '',  # empty
                'store_name': 'Test Store',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '1234567890',
                'category_code': 'SERVICE',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'store_id' in response.json()['detail']['missing_fields']

    def test_null_fields_treated_as_missing(self, client):
        response = client.post(
            '/api/feedback/',
            data=json.dumps({
                'store_id': 'ST001',
                'store_name': None,  # null
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '1234567890',
                'category_code': 'SERVICE',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'store_name' in response.json()['detail']['missing_fields']


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestBlockErrors:

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def initial_feedback(self, client, complete_feedback_request):
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )
        assert response.status_code == 201
        return response.json()

    def test_store_id_conflict_returns_409(self, client, initial_feedback, complete_feedback_request):
        """Same store_id with a different name → 409 STORE_ID_CONFLICT."""
        request = {**complete_feedback_request, 'store_name': 'Completely Different Name', 'phone': '9876543210'}
        response = client.post(
            '/api/feedback/',
            data=json.dumps(request),
            content_type='application/json',
        )

        assert response.status_code == 409
        data = response.json()
        assert data['type'] == 'block_error'
        assert data['code'] == 'STORE_ID_CONFLICT'
        assert 'already exists' in data['message'].lower()
        assert 'detail' in data
        assert data['detail']['existing_name'] == 'Test Store A'
        assert data['detail']['provided_name'] == 'Completely Different Name'

    def test_same_day_feedback_duplicate_returns_409(self, client, initial_feedback, complete_feedback_request):
        """Duplicate feedback on the same day → 409 FEEDBACK_DUPLICATE."""
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )
        assert response.status_code == 409
        data = response.json()
        assert data['type'] == 'block_error'
        assert data['code'] == 'FEEDBACK_DUPLICATE'
        assert 'already submitted' in data['message'].lower()
        assert 'customer_id' in data['detail']
        assert 'category_code' in data['detail']
        assert 'existing_feedback_id' in data['detail']

    def test_block_errors_prevent_database_changes(self, client, initial_feedback, complete_feedback_request):
        initial_store_count = Store.objects.count()
        initial_customer_count = Customer.objects.count()

        request = {**complete_feedback_request, 'store_name': 'Different Name', 'phone': '9999999999'}
        response = client.post(
            '/api/feedback/',
            data=json.dumps(request),
            content_type='application/json',
        )

        assert response.status_code == 409
        assert Store.objects.count() == initial_store_count
        assert Customer.objects.count() == initial_customer_count


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestWarningHandling:
    """FeedbackWarning: same store + customer + category submitted on a different day."""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def initial_feedback(self, client, complete_feedback_request):
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )
        assert response.status_code == 201
        # Back-date the feedback so the next request is treated as a different day
        Feedback.objects.all().update(created_at=timezone.now() - timedelta(days=1))
        return response.json()

    def test_different_day_feedback_returns_200_with_warning(self, client, initial_feedback, complete_feedback_request):
        """Same store + customer + category on a different day → 200 FeedbackWarning."""
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.json()
        assert 'warnings' in data
        assert len(data['warnings']) > 0
        warning = data['warnings'][0]
        assert warning['type'] == 'warning'
        assert warning['code'] == 'FEEDBACK_ALREADY_EXISTS'
        assert 'detail' in warning

    def test_warnings_array_structure(self, client, initial_feedback, complete_feedback_request):
        """Warning payload should be a list with standard fields on each item."""
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['warnings'], list)
        assert len(data['warnings']) > 0
        for warning in data['warnings']:
            assert 'type' in warning
            assert 'code' in warning
            assert 'message' in warning

    def test_different_day_with_confirm_creates_feedback(self, client, initial_feedback, complete_feedback_request):
        """Submitting with confirm=True after a warning → 201 and feedback saved."""
        confirmed = {**complete_feedback_request, 'confirm': True}
        response = client.post(
            '/api/feedback/',
            data=json.dumps(confirmed),
            content_type='application/json',
        )
        assert response.status_code == 201
        # 2 feedback records: one from yesterday, one from today
        assert Feedback.objects.count() == 2


@pytest.mark.error_handling
@pytest.mark.integration
@pytest.mark.django_db
class TestErrorResponseConsistency:

    @pytest.fixture
    def client(self):
        return Client()

    def test_all_errors_have_type_field(self, client):
        response = client.post('/api/feedback/', data=json.dumps({}), content_type='application/json')
        assert 'type' in response.json()

    def test_all_errors_have_code_field(self, client):
        response = client.post('/api/feedback/', data=json.dumps({}), content_type='application/json')
        assert 'code' in response.json()

    def test_all_errors_have_message_field(self, client):
        response = client.post('/api/feedback/', data=json.dumps({}), content_type='application/json')
        assert 'message' in response.json()

    def test_error_types_match_status_codes(self, client, complete_feedback_request):
        # Seed initial feedback first
        client.post('/api/feedback/', data=json.dumps(complete_feedback_request), content_type='application/json')

        test_cases = [
            ({}, 400, 'validation_error'),
            ({**complete_feedback_request, 'store_name': 'Different', 'phone': '9999999999'}, 409, 'block_error'),
        ]
        for request_data, expected_status, expected_type in test_cases:
            response = client.post(
                '/api/feedback/',
                data=json.dumps(request_data),
                content_type='application/json',
            )
            assert response.status_code == expected_status
            assert response.json()['type'] == expected_type

    def test_errors_are_json_serializable(self, client):
        import json as json_module
        response = client.post('/api/feedback/', data=json.dumps({}), content_type='application/json')
        data = response.json()
        assert isinstance(data, dict)
        json_str = json_module.dumps(data)
        assert isinstance(json_str, str)
