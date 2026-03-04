"""
Business logic for category management.
"""

from django.db.models import Count

from ..models.inventory import Category


# ---------------------------------------------------------------------------
# Commands (write)
# ---------------------------------------------------------------------------

def create_category(*, name):
    """Create and return a new category (``full_clean`` runs on ``save``)."""
    category = Category(name=name)
    category.save()
    return category


def update_category(category, *, name):
    """Update an existing category."""
    category.name = name
    category.save()
    return category


# ---------------------------------------------------------------------------
# Queries (read)
# ---------------------------------------------------------------------------

def get_category_list(*, search=""):
    """Return filtered queryset of categories with item counts."""
    qs = Category.objects.annotate(item_count=Count("items")).order_by("name")
    if search:
        qs = qs.filter(name__icontains=search)
    return qs
