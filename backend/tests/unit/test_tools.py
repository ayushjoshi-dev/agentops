"""
AgentOps — Unit Tests for All Tools
=====================================
Tests each LangChain tool with a mocked DB session.
These tests are 100% deterministic — no real DB or LLM is called.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import pytest
from unittest.mock import MagicMock


class TestGetOrderStatus:
    """Tests for get_order_status tool."""

    def test_order_found_returns_status(self, mock_db, sample_order):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = sample_order
        result = order_tools.get_order_status.invoke({"order_number": "ORD-1025"})
        assert "ORD-1025" in result
        assert "DELIVERED" in result

    def test_order_not_found_returns_message(self, mock_db):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = None
        result = order_tools.get_order_status.invoke({"order_number": "ORD-9999"})
        assert "not found" in result.lower()

    def test_normalizes_order_number_without_prefix(self, mock_db, sample_order):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = sample_order
        result = order_tools.get_order_status.invoke({"order_number": "1025"})
        assert "ORD-1025" in result

    def test_no_db_session_returns_error(self):
        from app.tools import order_tools
        order_tools.set_db_session(None)
        result = order_tools.get_order_status.invoke({"order_number": "ORD-1025"})
        assert "Error" in result


class TestGetOrderDetails:
    """Tests for get_order_details tool."""

    def test_returns_items_section(self, mock_db, sample_order):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = sample_order
        result = order_tools.get_order_details.invoke({"order_number": "ORD-1025"})
        assert "Items Ordered" in result

    def test_includes_total_amount(self, mock_db, sample_order):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = sample_order
        result = order_tools.get_order_details.invoke({"order_number": "ORD-1025"})
        assert "55,000" in result

    def test_order_not_found(self, mock_db):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = None
        result = order_tools.get_order_details.invoke({"order_number": "ORD-XXXX"})
        assert "not found" in result.lower()


class TestGetCustomerOrders:
    """Tests for get_customer_orders tool."""

    def test_returns_orders_for_valid_user(self, mock_db, sample_user, sample_order):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = sample_user
        mock_db.all.return_value = [sample_order]
        result = order_tools.get_customer_orders.invoke({"user_email": "demo@shopease.com"})
        assert "ORD-1025" in result

    def test_user_not_found_returns_message(self, mock_db):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = None
        result = order_tools.get_customer_orders.invoke({"user_email": "notfound@test.com"})
        assert "not found" in result.lower() or "No account" in result

    def test_no_orders_returns_message(self, mock_db, sample_user):
        from app.tools import order_tools
        order_tools.set_db_session(mock_db)
        mock_db.first.return_value = sample_user
        mock_db.all.return_value = []
        result = order_tools.get_customer_orders.invoke({"user_email": "demo@shopease.com"})
        assert "No orders" in result or "no orders" in result.lower()


class TestSearchProducts:
    """Tests for search_products tool."""

    def test_returns_products_on_valid_query(self, mock_db, sample_product):
        from app.tools import product_tools
        product_tools.set_db_session(mock_db)
        mock_db.all.return_value = [sample_product]
        result = product_tools.search_products.invoke({"query": "laptop"})
        assert "Lenovo IdeaPad" in result
        assert "57,999" in result

    def test_no_products_found_returns_message(self, mock_db):
        from app.tools import product_tools
        product_tools.set_db_session(mock_db)
        mock_db.all.return_value = []
        result = product_tools.search_products.invoke({"query": "quantum computer"})
        assert "No products found" in result

    def test_price_filter_applied(self, mock_db, sample_product):
        from app.tools import product_tools
        product_tools.set_db_session(mock_db)
        mock_db.all.return_value = [sample_product]
        result = product_tools.search_products.invoke({"query": "laptop", "max_price": 60000.0})
        assert "Found" in result

    def test_no_db_session_returns_error(self):
        from app.tools import product_tools
        product_tools.set_db_session(None)
        result = product_tools.search_products.invoke({"query": "laptop"})
        assert "Error" in result


class TestCreateSupportTicket:
    """Tests for create_support_ticket tool."""

    def test_creates_ticket_successfully(self, mock_db, sample_user):
        from app.tools import ticket_tools
        ticket_tools.set_db_session(mock_db)
        # The tool makes 3 .first() calls:
        # 1. User lookup (returns sample_user)
        # 2. Order lookup by order_number (returns None - no order found is OK)
        # 3. _get_next_ticket_number: last ticket (returns None -> TKT-1016)
        mock_db.first.side_effect = [sample_user, None, None]
        result = ticket_tools.create_support_ticket.invoke({
            "user_email": "demo@shopease.com",
            "issue_title": "Damaged product received",
            "issue_description": "The laptop screen is cracked",
            "priority": "HIGH",
            "order_number": "ORD-1025",
        })
        assert "TKT-" in result
        assert "created successfully" in result.lower()

    def test_user_not_found_returns_error(self, mock_db):
        from app.tools import ticket_tools
        ticket_tools.set_db_session(mock_db)
        mock_db.first.return_value = None
        result = ticket_tools.create_support_ticket.invoke({
            "user_email": "ghost@test.com",
            "issue_title": "Test",
            "issue_description": "Test description",
        })
        assert "not found" in result.lower() or "User not found" in result

    def test_invalid_priority_defaults_to_medium(self, mock_db, sample_user):
        from app.tools import ticket_tools
        ticket_tools.set_db_session(mock_db)
        # 1. User lookup, 2. No order, 3. No last ticket
        mock_db.first.side_effect = [sample_user, None, None]
        result = ticket_tools.create_support_ticket.invoke({
            "user_email": "demo@shopease.com",
            "issue_title": "Test",
            "issue_description": "Test",
            "priority": "INVALID_PRIORITY",
        })
        assert "MEDIUM" in result

    def test_no_db_returns_error(self):
        from app.tools import ticket_tools
        ticket_tools.set_db_session(None)
        result = ticket_tools.create_support_ticket.invoke({
            "user_email": "demo@shopease.com",
            "issue_title": "Test",
            "issue_description": "Test",
        })
        assert "Error" in result


class TestCalculate:
    """Tests for calculator tool."""

    def test_basic_addition(self):
        from app.tools.calculator_tool import calculate
        result = calculate.invoke({"expression": "100 + 200"})
        assert "300" in result

    def test_percentage_calculation(self):
        from app.tools.calculator_tool import calculate
        result = calculate.invoke({"expression": "50000 * 0.18"})
        # Result may be formatted as 9,000 or 9000
        assert "9000" in result.replace(",", "")

    def test_division(self):
        from app.tools.calculator_tool import calculate
        result = calculate.invoke({"expression": "1000 / 4"})
        assert "250" in result

    def test_invalid_expression_handled_gracefully(self):
        from app.tools.calculator_tool import calculate
        result = calculate.invoke({"expression": "drop table users"})
        # Should not raise an exception, should return an error string
        assert isinstance(result, str)
        assert len(result) > 0
