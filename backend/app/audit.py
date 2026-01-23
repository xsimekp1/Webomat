"""Audit logging utility for tracking user actions."""

from typing import Any
from .database import get_supabase


def log_audit(
    user_id: str | None,
    user_email: str | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Log an audit event to the database.

    Actions:
    - login, logout, login_failed
    - business_create, business_update, business_delete
    - project_create, project_update
    - activity_create
    - user_create, user_update, user_deactivate, password_reset, password_change
    - status_change
    """
    try:
        supabase = get_supabase()

        data = {
            "user_id": user_id,
            "user_email": user_email,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        supabase.table("audit_log").insert(data).execute()
    except Exception as e:
        # Don't fail the main operation if audit logging fails
        print(f"Audit log error: {e}")


def log_login(user_id: str, user_email: str, ip_address: str | None = None) -> None:
    """Log successful login."""
    log_audit(user_id, user_email, "login", ip_address=ip_address)


def log_logout(user_id: str, user_email: str) -> None:
    """Log logout."""
    log_audit(user_id, user_email, "logout")


def log_login_failed(user_email: str, ip_address: str | None = None) -> None:
    """Log failed login attempt."""
    log_audit(None, user_email, "login_failed", ip_address=ip_address)


def log_entity_change(
    user_id: str,
    user_email: str,
    action: str,
    entity_type: str,
    entity_id: str,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    """Log entity creation, update, or deletion."""
    log_audit(
        user_id=user_id,
        user_email=user_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
    )
