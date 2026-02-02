# ============================================
# Invoices Received Management (faktury od obchodníků)
# ============================================


@router.post("/invoices-received", response_model=InvoiceReceivedResponse)
async def create_seller_invoice(
    invoice_data: InvoiceReceivedCreate,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Create a new invoice from seller to platform."""
    supabase = get_supabase()

    # Check if invoice number already exists for this seller
    existing_result = (
        supabase.table("invoices_received")
        .select("id")
        .eq("seller_id", current_user.id)
        .eq("invoice_number", invoice_data.invoice_number)
        .single()
        .execute()
    )
    
    if existing_result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice number already exists for this seller"
        )

    # Create invoice
    invoice_dict = invoice_data.dict()
    invoice_dict.update({
        "seller_id": current_user.id,
        "status": "draft",  # Always start as draft
        "is_test": False,
    })

    result = (
        supabase.table("invoices_received")
        .insert(invoice_dict)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invoice"
        )

    invoice = result.data[0]

    # Add seller info
    seller_result = (
        supabase.table("sellers")
        .select("first_name, last_name, email")
        .eq("id", invoice["seller_id"])
        .single()
        .execute()
    )
    
    if seller_result.data:
        seller = seller_result.data
        invoice["seller_name"] = f"{seller['first_name']} {seller['last_name']}"
        invoice["seller_email"] = seller["email"]

    return InvoiceReceivedResponse(**invoice)


@router.put("/invoices-received/{invoice_id}/submit")
async def submit_seller_invoice(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_sales_or_admin)],
):
    """Submit invoice for approval."""
    supabase = get_supabase()

    # Get invoice and verify ownership
    invoice_result = (
        supabase.table("invoices_received")
        .select("*")
        .eq("id", invoice_id)
        .eq("seller_id", current_user.id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    invoice = invoice_result.data
    if invoice["status"] != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft invoices can be submitted"
        )

    # Update status to submitted
    result = (
        supabase.table("invoices_received")
        .update({"status": "submitted"})
        .eq("id", invoice_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit invoice"
        )

    return result.data[0]


@router.put("/invoices-received/{invoice_id}/pay")
async def mark_invoice_paid(
    invoice_id: str,
    current_user: Annotated[User, Depends(require_admin)],
):
    """Mark invoice as paid (admin only)."""
    supabase = get_supabase()

    # Get invoice
    invoice_result = (
        supabase.table("invoices_received")
        .select("*")
        .eq("id", invoice_id)
        .single()
        .execute()
    )

    if not invoice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    invoice = invoice_result.data
    if invoice["status"] != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved invoices can be marked as paid"
        )

    # Update status and mark as paid
    update_data = {
        "status": "paid",
        "paid_at": datetime.utcnow().isoformat(),
    }

    result = (
        supabase.table("invoices_received")
        .update(update_data)
        .eq("id", invoice_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark invoice as paid"
        )

    return result.data[0]


@router.get("/admin/invoices-received", response_model=list[InvoiceReceivedResponse])
async def list_admin_invoices(
    current_user: Annotated[User, Depends(require_admin)],
    status: str | None = None,
):
    """List all invoices received from sellers (admin only)."""
    supabase = get_supabase()

    query = supabase.table("invoices_received").select("*")
    
    if status:
        query = query.eq("status", status)

    result = (
        query
        .order("created_at", desc=True)
        .execute()
    )

    invoices = []
    for invoice in result.data or []:
        # Add seller info
        seller_result = (
            supabase.table("sellers")
            .select("first_name, last_name, email")
            .eq("id", invoice["seller_id"])
            .single()
            .execute()
        )
        
        if seller_result.data:
            seller = seller_result.data
            invoice["seller_name"] = f"{seller['first_name']} {seller['last_name']}"
            invoice["seller_email"] = seller["email"]

        invoices.append(invoice)

    return [InvoiceReceivedResponse(**inv) for inv in invoices]