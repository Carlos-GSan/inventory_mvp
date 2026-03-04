"""
Business logic for supplier management.
"""

from django.db.models import Q

from ..models.purchases import Supplier


# ---------------------------------------------------------------------------
# Commands (write)
# ---------------------------------------------------------------------------

def create_supplier(*, name, contact_name="", phone=None, email="", rfc="", address="", active=True):
    """Create and return a new supplier (``full_clean`` runs on ``save``)."""
    supplier = Supplier(
        name=name,
        contact_name=contact_name,
        phone=phone,
        email=email,
        rfc=rfc,
        address=address,
        active=active,
    )
    supplier.save()  # triggers full_clean → normalize_name validation
    return supplier


def update_supplier(supplier, *, name, contact_name="", phone=None, email="", rfc="", address="", active=True):
    """Update an existing supplier."""
    supplier.name = name
    supplier.contact_name = contact_name
    supplier.phone = phone
    supplier.email = email
    supplier.rfc = rfc
    supplier.address = address
    supplier.active = active
    supplier.save()
    return supplier


# ---------------------------------------------------------------------------
# Queries (read)
# ---------------------------------------------------------------------------

def get_supplier_list(*, search="", status=""):
    """Return filtered queryset of suppliers."""
    qs = Supplier.objects.all()
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(contact_name__icontains=search)
            | Q(rfc__icontains=search)
            | Q(email__icontains=search)
        )
    if status == "1":
        qs = qs.filter(active=True)
    elif status == "0":
        qs = qs.filter(active=False)
    return qs
