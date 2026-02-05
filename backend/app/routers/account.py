"""
Account endpoints for balance and transactions.
Extended for better dashboard functionality.
"""

from typing import Annotated
from fastapi import APIRouter, Query, HTTPException
from ..database import get_supabase
from ..dependencies import get_current_active_user, require_sales_or_admin
from ..schemas.crm import (
    BusinessListResponse,
    BusinessResponse,
    ActivityCreate,
    ActivityResponse,
    ProjectStatus,
    PackageType,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)
from ..utils.balance_calculator import calculate_seller_balance

router = APIRouter(prefix="/account", tags=["Account"])


@router.get("/balance-history", response_model=BalancePageResponse)
async def get_balance_history(
    current_user: Annotated[dict, Depends(get_current_active_user)],
    range: str = Query("3m", description="Time range: 3m, 6m, 12m"),
    limit: int = Query(100, description="Number of transactions"),
):
    """
    Get balance history for charts (aggregated data).
    Optimized for frontend chart components.
    """
    supabase = get_supabase()
    
    # Get all ledger entries for this seller with date filtering
    ledger_query = supabase.table("ledger_entries").select("*")
    
    if range == "3m":
        # Last 3 months
        ledger_query = ledger_query.gte("created_at", "now", "interval", "-3 months")
    elif range == "6m":
        # Last 6 months
        ledger_query = ledger_query.gte("created_at", "now", "interval", "-6 months")
    elif range == "12m":
        # Last 12 months
        ledger_query = ledger_query.gte("created_at", "now", "interval", "-12 months")
    
    ledger_result = ledger_query.eq("seller_id", current_user["id"]).order("created_at", desc=True).limit(limit).execute()
    
    # Calculate balance properly
    balance_data = calculate_seller_balance(ledger_result.data or [])
    
    # Transform for chart (daily aggregated data)
    chart_data = []
    running_balance = 0
    
    for entry in ledger_result.data or []:
        # Skip pending reservations (they don't affect balance yet)
        if entry["entry_type"] == "payout_reserved":
            continue
            
        date = entry["created_at"].split("T")[0]
        
        # Calculate running balance
        if entry["entry_type"] == "commission_earned":
            running_balance += entry["amount"]
        elif entry["entry_type"] == "admin_adjustment":
            running_balance += entry["amount"]
        elif entry["entry_type"] == "payout_paid":
            running_balance -= abs(entry["amount"])  # payouts are stored as negative
        
        # Only show balance changes for sales users
        if current_user.get("role") == "sales" and entry["entry_type"] in ["commission_earned", "admin_adjustment"]:
            # Check if this date already exists in chart_data
            existing_date = next((d for d in chart_data if d["date"] == date), None)
            
            if not existing_date:
                chart_data.append({
                    "date": date,
                    "earned": entry["amount"] if entry["entry_type"] == "commission_earned" else 0,
                    "balance": running_balance,
                    "adjustments": entry["amount"] if entry["entry_type"] == "admin_adjustment" else 0,
                })
    
    return BalancePageResponse(
        available_balance=balance_data["available_balance"],
        ledger_entries=ledger_result.data or [],
        weekly_rewards=[],  # TODO: Implement weekly aggregation if needed
    )


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    current_user: Annotated[dict, Depends(get_current_active_user)],
    range: str = Query("3m", description="Time range"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of transactions"),
    offset: int = Query(0, description="Page offset"),
):
    """
    Get detailed transaction list for table view.
    Supports pagination and filtering.
    """
    supabase = get_supabase()
    
    # Build query with filters
    query = supabase.table("ledger_entries").select("*").eq("seller_id", current_user["id"])
    
    if range:
        if range == "3m":
            query = query.gte("created_at", "now", "interval", "-3 months")
        elif range == "6m":
            query = query.gte("created_at", "now", "interval", "-6 months")
        elif range == "12m":
            query = query.gte("created_at", "now", "interval", "-12 months")
    
    if status:
        query = query.eq("entry_type", status)
    
    query = query.order("created_at", desc=True).limit(limit).offset(offset)
    
    result = query.execute()
    
    # Calculate current balance for header info
    balance_data = calculate_seller_balance(result.data or [])
    
    return TransactionListResponse(
        transactions=result.data or [],
        available_balance=balance_data["available_balance"],
        total_count=len(result.data) if result.data else 0,
        has_more=(len(result.data or []) >= limit)
    )


@router.post("/export/csv")
async def export_transactions_csv(
    current_user: Annotated[dict, Depends(get_current_active_user)],
    range: str = Query("3m"),
    format_type: str = Query("daily", description="Format: daily, monthly, yearly"),
):
    """
    Export transactions to CSV for accounting purposes.
    """
    from fastapi.responses import Response
    import csv
    from io import StringIO
    
    supabase = get_supabase()
    
    # Get transactions based on format and range
    if range == "3m":
        ledger_query = supabase.table("ledger_entries").select("*").gte("created_at", "now", "interval", "-3 months")
    elif range == "6m":
        ledger_query = supabase.table("ledger_entries").select("*").gte("created_at", "now", "interval", "-6 months")
    elif range == "12m":
        ledger_query = supabase.table("ledger_entries").select("*").gte("created_at", "now", "interval", "-12 months")
    
    ledger_query = ledger_query.eq("seller_id", current_user["id"]).order("created_at", desc=True)
    result = ledger_query.execute()
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # CSV headers
    if current_user.get("role") == "admin":
        writer.writerow(["Datum", "Typ", "Popis", "Částka", "ID faktury", "ID projektu", "Zůstatek"])
    else:
        writer.writerow(["Datum", "Typ", "Popis", "Částka", "Zůstatek"])
    
    # Data rows
    for entry in result.data or []:
        row = [
            entry["created_at"].split("T")[0],
            entry["entry_type"],
            entry.get("description", ""),
            entry["amount"],
            entry.get("related_invoice_id", ""),
            entry.get("related_project_id", ""),
        ]
        
        # Add balance column for admin
        if current_user.get("role") == "admin":
            balance_data = calculate_seller_balance([e for e in result.data if e["created_at"] <= entry["created_at"]])
            row.append(balance_data["available_balance"])
        else:
            row.append("") # Empty balance column for sales
        
        writer.writerow(row)
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        headers={"Content-Disposition": f"attachment; filename=transactions_{range}_{current_user['id']}.csv"},
        "Content-Type": "text/csv; charset=utf-8"
    )