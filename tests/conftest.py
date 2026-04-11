"""
Pytest configuration and fixtures for all tests
"""
import pytest
from django.conf import settings
from django.core.management import call_command
from datetime import date, timedelta
import os


# Override database settings for tests
@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    """Set up test database with SQLite"""
    # Override database to use SQLite for tests
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    
    # Run migrations
    with django_db_blocker.unblock():
        call_command('migrate', '--noinput', verbosity=0)


@pytest.fixture
def sample_store_data():
    """Sample store data for testing"""
    return {
        'store_id': 'ST001',
        'name': 'Test Store A'
    }


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return {
        'customer_id': 'CU001',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '1234567890'
    }


@pytest.fixture
def sample_feedback_data():
    """Sample feedback data for testing"""
    return {
        'category_code': 'SERVICE',
        'content': 'Great service!'
    }


@pytest.fixture
def complete_feedback_request():
    """Complete feedback request payload. customer_id is not included — backend auto-generates it."""
    return {
        'store_id': 'ST001',
        'store_name': 'Test Store A',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '1234567890',
        'category_code': 'SERVICE',
        'content': 'Great service!',
        'confirm': False,
    }


@pytest.fixture
def today():
    """Get today's date"""
    return date.today()


@pytest.fixture
def yesterday():
    """Get yesterday's date"""
    return date.today() - timedelta(days=1)
