"""
Pytest fixtures pro backend unit testy.

Mockuje Supabase a autentizaci pro izolované testování.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

# Mock Supabase response helper
class MockSupabaseResponse:
    """Mock pro Supabase execute() response."""
    def __init__(self, data=None, count=None):
        self.data = data or []
        self.count = count


class MockSupabaseQuery:
    """Mock pro Supabase query builder."""
    def __init__(self, data=None, count=None):
        self._data = data or []
        self._count = count
        self._single = False

    def select(self, *args, **kwargs):
        return self

    def insert(self, data):
        # Simulate insert - return data with generated id
        if isinstance(data, dict):
            result = {**data, "id": "test-generated-id", "created_at": datetime.utcnow().isoformat()}
            self._data = [result]
        return self

    def update(self, data):
        if self._data:
            self._data = [{**self._data[0], **data}]
        return self

    def delete(self):
        self._data = []
        return self

    def eq(self, *args, **kwargs):
        return self

    def neq(self, *args, **kwargs):
        return self

    def in_(self, *args, **kwargs):
        return self

    def not_(self, *args, **kwargs):
        return self

    def or_(self, *args, **kwargs):
        return self

    def ilike(self, *args, **kwargs):
        return self

    def lte(self, *args, **kwargs):
        return self

    def gte(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def range(self, *args, **kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        # When .single() is called, return first item as dict instead of list
        if self._single and self._data:
            return MockSupabaseResponse(self._data[0], self._count)
        return MockSupabaseResponse(self._data, self._count)


class MockSupabaseTable:
    """Mock pro supabase.table()."""
    def __init__(self, table_name: str, data_store: dict):
        self.table_name = table_name
        self.data_store = data_store

    def __call__(self, table_name: str):
        return MockSupabaseQuery(self.data_store.get(table_name, []))


class MockSupabase:
    """Mock pro celý Supabase client."""
    def __init__(self):
        self.data_store = {}

    @property
    def mock_data(self):
        """Alias pro data_store pro kompatibilitu s testy."""
        return self.data_store

    def table(self, table_name: str):
        return MockSupabaseQuery(self.data_store.get(table_name, []))

    def set_table_data(self, table_name: str, data: list):
        """Nastaví mock data pro tabulku."""
        self.data_store[table_name] = data


# Fixtures

@pytest.fixture
def mock_supabase():
    """Fixture pro mockovaný Supabase client."""
    return MockSupabase()


@pytest.fixture
def sample_seller():
    """Fixture pro testovacího obchodníka (sales role)."""
    return {
        "id": "seller-123",
        "email": "obchodnik@test.cz",
        "first_name": "Jan",
        "last_name": "Novák",
        "role": "sales",
        "is_active": True,
        "must_change_password": False,
        "onboarded_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_admin():
    """Fixture pro testovacího admina."""
    return {
        "id": "admin-456",
        "email": "admin@test.cz",
        "first_name": "Admin",
        "last_name": "Administrátor",
        "role": "admin",
        "is_active": True,
        "must_change_password": False,
        "onboarded_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_business():
    """Fixture pro testovací business/lead."""
    return {
        "id": "business-789",
        "name": "Test Firma s.r.o.",
        "address_full": "Testovací 123, Praha",
        "phone": "+420 123 456 789",
        "email": "info@testfirma.cz",
        "website": "https://www.testfirma.cz",
        "types": ["restaurant", "cafe"],
        "editorial_summary": "Testovací poznámky",
        "status_crm": "new",
        "owner_seller_id": "seller-123",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_project():
    """Fixture pro testovací projekt."""
    return {
        "id": "project-abc",
        "business_id": "business-789",
        "package": "profi",
        "status": "offer",
        "price_setup": 15000.0,
        "price_monthly": 500.0,
        "domain": "testfirma.cz",
        "notes": "Testovací projekt",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_version():
    """Fixture pro testovací website verzi."""
    return {
        "id": "version-xyz",
        "project_id": "project-abc",
        "version_number": 1,
        "status": "created",
        "source_bundle_path": None,
        "preview_image_path": None,
        "notes": "První verze",
        "created_at": datetime.utcnow().isoformat(),
        "created_by": "seller-123",
    }


@pytest.fixture
def sample_activity():
    """Fixture pro testovací aktivitu."""
    return {
        "id": "activity-001",
        "business_id": "business-789",
        "seller_id": "seller-123",
        "type": "call",
        "content": "Úvodní hovor s klientem",
        "outcome": "positive",
        "occurred_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_ledger_entry():
    """Fixture pro testovací ledger záznam."""
    return {
        "id": "ledger-001",
        "seller_id": "seller-123",
        "entry_type": "commission_earned",
        "amount": 1500.0,
        "description": "Provize za projekt Test Firma",
        "is_test": False,
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_invoice_issued():
    """Fixture pro testovací vydanou fakturu."""
    return {
        "id": "invoice-issued-001",
        "business_id": "business-789",
        "invoice_number": "2024-0001",
        "amount_total": 15000.0,
        "due_date": "2024-12-31",
        "status": "issued",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_invoice_received():
    """Fixture pro testovací přijatou fakturu."""
    return {
        "id": "invoice-received-001",
        "seller_id": "seller-123",
        "invoice_number": "FV-2024-001",
        "amount_total": 1500.0,
        "status": "submitted",
        "issue_date": "2024-12-01",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def app_client(mock_supabase, sample_seller):
    """
    Fixture pro FastAPI TestClient s mockovanou autentizací a databází.
    """
    from app.main import app
    from app.dependencies import get_current_user, require_sales_or_admin
    from app.database import get_supabase
    from app.schemas.auth import User

    # Mock user pro autentizaci
    mock_user = User(
        id=sample_seller["id"],
        email=sample_seller["email"],
        first_name=sample_seller["first_name"],
        last_name=sample_seller["last_name"],
        role=sample_seller["role"],
        is_active=sample_seller["is_active"],
        must_change_password=sample_seller["must_change_password"],
    )

    # Override dependencies
    app.dependency_overrides[get_supabase] = lambda: mock_supabase
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_sales_or_admin] = lambda: mock_user

    client = TestClient(app)
    yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(mock_supabase, sample_admin):
    """
    Fixture pro FastAPI TestClient s admin právy.
    """
    from app.main import app
    from app.dependencies import get_current_user, require_sales_or_admin, require_admin
    from app.database import get_supabase
    from app.schemas.auth import User

    mock_user = User(
        id=sample_admin["id"],
        email=sample_admin["email"],
        first_name=sample_admin["first_name"],
        last_name=sample_admin["last_name"],
        role=sample_admin["role"],
        is_active=sample_admin["is_active"],
        must_change_password=sample_admin["must_change_password"],
    )

    app.dependency_overrides[get_supabase] = lambda: mock_supabase
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[require_sales_or_admin] = lambda: mock_user
    app.dependency_overrides[require_admin] = lambda: mock_user

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
