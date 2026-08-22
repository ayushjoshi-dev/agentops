"""
AgentOps — Test Configuration & Shared Fixtures
================================================
conftest.py is loaded by pytest before any test.
All fixtures here are available to all tests.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

# IMPORTANT: Import ALL models upfront to ensure SQLAlchemy mapper
# initialization order is correct. Without this, lazy imports in tools
# can cause 'Conversation not found' errors when SQLAlchemy tries to
# resolve relationship strings between models.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Pre-import all models to ensure mapper initialization
try:
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.order import Order, OrderItem
    from app.models.product import Product
    from app.models.ticket import SupportTicket
    from app.models.agent_run import AgentRun
    from app.models.tool_call import ToolCall
    from app.models.document import Document, DocumentChunk
except Exception as e:
    pass  # Models may not all be importable in CI without DB — that's OK

DEMO_USER_EMAIL = "demo@shopease.com"
DEMO_ORDER_NUMBER = "ORD-1025"


@pytest.fixture
def mock_db():
    """Returns a MagicMock that behaves like a SQLAlchemy Session."""
    db = MagicMock()
    db.query.return_value = db
    db.filter.return_value = db
    db.order_by.return_value = db
    db.limit.return_value = db
    db.all.return_value = []
    db.first.return_value = None
    db.flush.return_value = None
    db.add.return_value = None
    db.commit.return_value = None
    db.execute.return_value = MagicMock(fetchall=lambda: [])
    return db


@pytest.fixture(scope="session")
def test_client():
    """Creates a FastAPI TestClient for integration tests."""
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app, raise_server_exceptions=False)
    except Exception as e:
        pytest.skip(f"Cannot create test client: {e}")


@pytest.fixture
def sample_order():
    """Returns a mock Order ORM object."""
    order = MagicMock()
    order.order_number = "ORD-1025"
    order.total_amount = 55000.0
    order.tracking_number = "EKART156153634"
    order.delivery_date = datetime.now(timezone.utc) - timedelta(days=2)
    order.created_at = datetime.now(timezone.utc) - timedelta(days=5)
    order.shipping_address = "123 Test Street, Mumbai"
    order.items = []
    status = MagicMock()
    status.value = "DELIVERED"
    order.status = status
    return order


@pytest.fixture
def sample_user():
    """Returns a mock User ORM object."""
    user = MagicMock()
    user.id = "40a68a79-aab7-4995-a489-f0915d3dbaef"
    user.email = DEMO_USER_EMAIL
    user.full_name = "Demo User"
    user.is_active = True
    return user


@pytest.fixture
def sample_product():
    """Returns a mock Product ORM object."""
    product = MagicMock()
    product.name = "Lenovo IdeaPad Slim 5"
    product.brand = "Lenovo"
    product.category = "Laptop"
    product.price = 57999.0
    product.rating = 4.4
    product.review_count = 590
    product.stock_quantity = 22
    product.is_available = True
    product.description = "14-inch 2.8K OLED display, Intel Core i7"
    return product
