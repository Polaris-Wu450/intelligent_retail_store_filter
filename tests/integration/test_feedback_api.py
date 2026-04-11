"""
Integration tests for Feedback API endpoints.
Tests the full workflow from HTTP request to database.
"""
import pytest
import json
from django.test import Client
from retailops.models import Store, Customer, Feedback


@pytest.mark.integration
@pytest.mark.django_db
class TestFeedbackAPIIntegration:

    @pytest.fixture
    def client(self):
        return Client()

    def test_complete_feedback_creation_workflow(self, client, complete_feedback_request):
        """Complete workflow: request → DB — store, customer, feedback all created."""
        response = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )

        assert response.status_code == 201
        data = response.json()
        assert 'message' in data
        assert 'store' in data
        assert 'customer' in data
        assert 'feedback' in data

        # DB records exist
        assert Store.objects.filter(store_id='ST001').exists()
        assert Customer.objects.count() == 1
        assert Feedback.objects.filter(category_code='SERVICE').count() == 1

        # auto-generated customer_id follows C### format
        customer = Customer.objects.first()
        assert customer.customer_id.startswith('C')
        assert customer.first_name == 'John'
        assert customer.last_name == 'Doe'

    def test_store_reuse_on_second_request(self, client, complete_feedback_request):
        """Second request with same store reuses the existing store record."""
        response1 = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )
        assert response1.status_code == 201
        store_db_id_1 = response1.json()['store']['id']

        # Different customer, same store
        request2 = {**complete_feedback_request, 'first_name': 'Jane', 'phone': '9876543210', 'category_code': 'PRODUCT'}
        response2 = client.post(
            '/api/feedback/',
            data=json.dumps(request2),
            content_type='application/json',
        )
        assert response2.status_code == 201
        store_db_id_2 = response2.json()['store']['id']

        assert store_db_id_1 == store_db_id_2
        assert Store.objects.count() == 1

    def test_customer_reuse_on_exact_name_phone_match(self, client, complete_feedback_request):
        """Same first_name + last_name + phone → same customer record reused."""
        response1 = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )
        assert response1.status_code == 201
        customer_db_id_1 = response1.json()['customer']['id']

        # Same customer, different category
        request2 = {**complete_feedback_request, 'category_code': 'PRODUCT'}
        response2 = client.post(
            '/api/feedback/',
            data=json.dumps(request2),
            content_type='application/json',
        )
        assert response2.status_code == 201
        customer_db_id_2 = response2.json()['customer']['id']

        assert customer_db_id_1 == customer_db_id_2
        assert Customer.objects.count() == 1

    def test_different_phone_creates_new_customer(self, client, complete_feedback_request):
        """Different phone → treated as a new customer, no warning raised."""
        response1 = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )
        assert response1.status_code == 201

        request2 = {**complete_feedback_request, 'phone': '9876543210', 'category_code': 'PRODUCT'}
        response2 = client.post(
            '/api/feedback/',
            data=json.dumps(request2),
            content_type='application/json',
        )
        assert response2.status_code == 201
        assert Customer.objects.count() == 2

    def test_store_id_conflict_returns_409(self, client, complete_feedback_request):
        """Same store_id with a different name → 409 STORE_ID_CONFLICT."""
        client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )

        request2 = {**complete_feedback_request, 'store_name': 'Different Store Name', 'phone': '9876543210'}
        response2 = client.post(
            '/api/feedback/',
            data=json.dumps(request2),
            content_type='application/json',
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data['type'] == 'block_error'
        assert data['code'] == 'STORE_ID_CONFLICT'
        assert 'detail' in data

    def test_same_day_feedback_duplicate_returns_409(self, client, complete_feedback_request):
        """Same store + customer + category on the same day → 409 FEEDBACK_DUPLICATE."""
        client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )
        response2 = client.post(
            '/api/feedback/',
            data=json.dumps(complete_feedback_request),
            content_type='application/json',
        )

        assert response2.status_code == 409
        data = response2.json()
        assert data['type'] == 'block_error'
        assert data['code'] == 'FEEDBACK_DUPLICATE'
        assert Feedback.objects.filter(category_code='SERVICE').count() == 1

    def test_missing_required_fields_returns_400(self, client):
        response = client.post(
            '/api/feedback/',
            data=json.dumps({'store_id': 'ST001'}),
            content_type='application/json',
        )
        assert response.status_code == 400
        data = response.json()
        assert data['type'] == 'validation_error'
        assert 'missing_fields' in data['detail']

    def test_multiple_feedbacks_different_categories(self, client, complete_feedback_request):
        """Same customer can submit feedback for different categories on the same day."""
        categories = ['SERVICE', 'PRODUCT', 'ENVIRONMENT', 'STAFF']
        for category in categories:
            response = client.post(
                '/api/feedback/',
                data=json.dumps({**complete_feedback_request, 'category_code': category}),
                content_type='application/json',
            )
            assert response.status_code == 201

        assert Feedback.objects.count() == 4
        assert Customer.objects.count() == 1

    def test_concurrent_requests_with_different_phones_create_separate_customers(self, client, complete_feedback_request):
        """Requests with distinct phones create distinct customer records."""
        phones = ['1230000001', '1230000002', '1230000003']
        for phone in phones:
            response = client.post(
                '/api/feedback/',
                data=json.dumps({**complete_feedback_request, 'phone': phone}),
                content_type='application/json',
            )
            assert response.status_code == 201

        assert Customer.objects.count() == 3


@pytest.mark.integration
@pytest.mark.django_db
class TestExceptionHandlerMiddleware:

    @pytest.fixture
    def client(self):
        return Client()

    def test_json_parse_error_returns_error_status(self, client):
        response = client.post(
            '/api/feedback/',
            data='invalid json{',
            content_type='application/json',
        )
        assert response.status_code >= 400

    def test_all_errors_have_consistent_format(self, client):
        """400 and 409 errors both carry type / code / message."""
        # Validation error (400)
        r400 = client.post(
            '/api/feedback/',
            data=json.dumps({}),
            content_type='application/json',
        )
        assert r400.status_code == 400
        for key in ('type', 'code', 'message'):
            assert key in r400.json()
