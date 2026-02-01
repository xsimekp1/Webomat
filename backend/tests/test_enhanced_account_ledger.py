import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.dependencies import require_sales_or_admin
from app.schemas.auth import User

client = TestClient(app)

# Mock user for testing
MOCK_SALES_USER = User(
    id="123e4567-e89b-12d3-a456-426614174000",
    email="sales@test.com",
    first_name="Sales",
    last_name="User",
    role="sales",
    is_active=True,
    must_change_password=False
)

# Sample ledger entries
SAMPLE_LEDGER_DATA = [
    {
        "id": "entry1",
        "seller_id": MOCK_SALES_USER.id,
        "entry_type": "commission_earned",
        "amount": 5000.0,
        "description": "Komise z projektu Web pro Firma ABC",
        "related_business_id": "business123",
        "related_project_id": "project123",
        "created_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "entry2", 
        "seller_id": MOCK_SALES_USER.id,
        "entry_type": "commission_earned",
        "amount": 3000.0,
        "description": "Komise z projektu E-shop pro Obchod XYZ",
        "related_business_id": "business456",
        "related_project_id": "project456",
        "created_at": "2024-01-20T14:30:00Z"
    },
    {
        "id": "entry3",
        "seller_id": MOCK_SALES_USER.id,
        "entry_type": "payout_reserved",
        "amount": -2000.0,
        "description": "Rezervace výplaty - Leden 2024",
        "created_at": "2024-01-25T09:00:00Z"
    }
]

SAMPLE_BUSINESSES = {
    "business123": {"name": "Firma ABC"},
    "business456": {"name": "Obchod XYZ"}
}

SAMPLE_INVOICES = {
    "invoice123": {"invoice_number": "FV2024001", "issue_date": "2024-01-15T00:00:00Z", "approved_at": "2024-01-20T10:00:00Z"},
    "invoice456": {"invoice_number": "FV2024002", "issue_date": "2024-01-20T00:00:00Z", "approved_at": "2024-01-22T15:00:00Z"}
}


class TestSellerAccountLedger:
    """Test GET /crm/seller/account/ledger endpoint."""

    def test_get_ledger_success(self, mock_supabase, mock_current_user):
        """Test successful ledger retrieval with correct balance calculation."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = SAMPLE_LEDGER_DATA
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.get("/crm/seller/account/ledger")
        
        # Assertions
        assert response.status_code == 200
        
        data = response.json()
        assert "available_balance" in data
        assert "ledger_entries" in data
        
        # Balance calculation: 5000 + 3000 - 2000 = 6000
        assert data["available_balance"] == 6000.0
        
        # Verify ledger entries are returned
        assert len(data["ledger_entries"]) == 3
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_ledger_with_filters_range(self, mock_supabase, mock_current_user):
        """Test ledger with date range filter."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = SAMPLE_LEDGER_DATA
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request with month range
        response = client.get("/crm/seller/account/ledger?range=month")
        
        # Assertions
        assert response.status_code == 200
        
        # Verify date filter was applied
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.assert_called()
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_ledger_with_filters_type(self, mock_supabase, mock_current_user):
        """Test ledger with type filter."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = SAMPLE_LEDGER_DATA
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request with type filter
        response = client.get("/crm/seller/account/ledger?type=earned")
        
        # Assertions
        assert response.status_code == 200
        
        # Verify type filter was applied
        mock_supabase.table.return_value.select.return_value.in_.assert_called_with(["commission_earned"])
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_ledger_with_enhanced_data(self, mock_supabase, mock_current_user):
        """Test ledger with enhanced business and invoice data."""
        # Setup mocks with JOIN simulation
        def mock_query_side_effect():
            mock_result = Mock()
            mock_result.data = [
                {
                    **SAMPLE_LEDGER_DATA[0],
                    "related_business_name": "Firma ABC",
                    "related_invoice_number": "FV2024001",
                    "invoice_date": "2024-01-15T00:00:00Z",
                    "approval_date": "2024-01-20T10:00:00Z",
                    "balance_after": 5000.0
                },
                {
                    **SAMPLE_LEDGER_DATA[1], 
                    "related_business_name": "Obchod XYZ",
                    "related_invoice_number": "FV2024002",
                    "invoice_date": "2024-01-20T00:00:00Z",
                    "approval_date": "2024-01-22T15:00:00Z",
                    "balance_after": 8000.0
                },
                {
                    **SAMPLE_LEDGER_DATA[2],
                    "balance_after": 6000.0
                }
            ]
            return mock_result
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_query_side_effect
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.get("/crm/seller/account/ledger")
        
        # Assertions
        assert response.status_code == 200
        
        data = response.json()
        entries = data["ledger_entries"]
        
        # Verify enhanced data is included
        assert entries[0]["related_business_name"] == "Firma ABC"
        assert entries[0]["related_invoice_number"] == "FV2024001"
        assert entries[0]["balance_after"] == 5000.0
        
        assert entries[1]["related_business_name"] == "Obchod XYZ"
        assert entries[1]["related_invoice_number"] == "FV2024002"
        assert entries[1]["approval_date"] == "2024-01-22T15:00:00Z"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_ledger_unauthorized(self, mock_supabase):
        """Test unauthorized access should fail."""
        # Don't override auth dependency - this should trigger authentication failure
        
        # Make request without auth
        response = client.get("/crm/seller/account/ledger")
        
        # Should fail with authentication error
        assert response.status_code in [401, 403]

    def test_get_ledger_weekly_rewards(self, mock_supabase, mock_current_user):
        """Test weekly rewards calculation."""
        # Setup mocks
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = SAMPLE_LEDGER_DATA
        
        def mock_weekly_query():
            mock_result = Mock()
            mock_result.data = [
                {"amount": 2000.0},  # Week 1
                {"amount": 3000.0}   # Week 2
            ]
            return mock_result
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.side_effect = mock_weekly_query
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.get("/crm/seller/account/ledger?range=all")
        
        # Assertions
        assert response.status_code == 200
        
        data = response.json()
        assert "weekly_rewards" in data
        assert len(data["weekly_rewards"]) >= 2
        
        # Clean up
        app.dependency_overrides.clear()

    def test_balance_calculation_accuracy(self, mock_supabase, mock_current_user):
        """Test that balance calculation matches expected formula."""
        # Setup: earned = 10000, reserved = 3000, paid = 2000, available = 5000
        earned_data = [
            {"amount": 6000.0}, {"amount": 4000.0}  # Total 10000
        ]
        payout_data = [
            {"amount": -3000.0},  # Reserved
            {"amount": -2000.0}   # Paid
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            Mock(data=earned_data),   # First call for earned
            Mock(data=payout_data)    # Second call for payouts
        ]
        mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
        
        # Override auth dependency
        app.dependency_overrides[require_sales_or_admin] = mock_current_user()
        
        # Make request
        response = client.get("/crm/seller/account/ledger")
        
        # Assertions
        assert response.status_code == 200
        
        data = response.json()
        # Expected: 10000 - (3000 + 2000) = 5000
        assert data["available_balance"] == 5000.0
        
        # Clean up
        app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('app.routers.crm.get_supabase') as mock_get_supabase:
        mock_client = Mock()
        mock_get_supabase.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_current_user():
    """Mock current user dependency."""
    def _get_user(user=MOCK_SALES_USER):
        def _dependency():
            return user
        return _dependency
    return _get_user