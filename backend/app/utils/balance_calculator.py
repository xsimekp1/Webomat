"""
Výpočetní utilitky pro balance obchodníků
Správný výpočet s oddělením typů pohybů
"""


def calculate_seller_balance(ledger_entries):
    """
    Spočítá dostupný balance obchodníka.

    Args:
        ledger_entries: List of dicts with 'amount' and 'entry_type' fields

    Returns:
        dict: {
            'total_earned': float,
            'total_paid_out': float,
            'available_balance': float,
            'pending_commissions': float,
            'admin_adjustments': float
        }
    """
    if not ledger_entries:
        return {
            "total_earned": 0.0,
            "total_paid_out": 0.0,
            "available_balance": 0.0,
            "pending_commissions": 0.0,
            "admin_adjustments": 0.0,
        }

    # Oddělit typy pohybů
    earnings = []
    payouts = []
    pending = []
    adjustments = []

    for entry in ledger_entries:
        entry_type = entry.get("entry_type", "")
        amount = float(entry.get("amount", 0))

        if entry_type == "commission_earned":
            earnings.append(amount)
        elif entry_type == "payout_reserved":
            # Reservované výplaty (stále nemůžou být vyplaceny)
            pending.append(abs(amount))
        elif entry_type == "payout_paid":
            # Skutečné výplaty (odečítáme od balance)
            payouts.append(abs(amount))
        elif entry_type == "admin_adjustment":
            # Administrativní úpravy
            adjustments.append(amount)

    total_earned = sum(earnings)
    total_paid_out = sum(payouts)
    pending_commissions = sum(pending)
    admin_adjustments = sum(adjustments)

    # Balance = všechny příjmy - všechny skutečné výdaje
    # Pending komise se nepočítají jako výdaj, protože nejsou ještě vyplaceny
    available_balance = total_earned + admin_adjustments - total_paid_out

    return {
        "total_earned": total_earned,
        "total_paid_out": total_paid_out,
        "available_balance": available_balance,
        "pending_commissions": pending_commissions,
        "admin_adjustments": admin_adjustments,
    }


def get_balance_summary(ledger_entries):
    """
    Vrací human-readable popis balance

    Returns:
        str: Popis stavu účtu
    """
    balance_data = calculate_seller_balance(ledger_entries)

    parts = []

    # Celkové příjmy
    if balance_data["total_earned"] > 0:
        parts.append(f"Celkem vyděláno: CZK {balance_data['total_earned']:,.0f}")

    # Administrativní úpravy
    if balance_data["admin_adjustments"] != 0:
        sign = "+" if balance_data["admin_adjustments"] > 0 else "-"
        parts.append(
            f"Admin úpravy: {sign}CZK {abs(balance_data['admin_adjustments']):,.0f}"
        )

    # Vyplaceno
    if balance_data["total_paid_out"] > 0:
        parts.append(f"Vyplaceno: CZK {balance_data['total_paid_out']:,.0f}")

    # Čeká na vyplacení
    if balance_data["pending_commissions"] > 0:
        parts.append(
            f"Čeká na vyplacení: CZK {balance_data['pending_commissions']:,.0f}"
        )

    # Dostupný balance
    parts.append(f"Dostupný balance: CZK {balance_data['available_balance']:,.0f}")

    return " | ".join(parts)
