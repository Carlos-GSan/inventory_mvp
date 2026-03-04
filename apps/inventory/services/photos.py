"""
Photo management services.
"""

from django.shortcuts import get_object_or_404

from ..models.inventory import ItemPhoto
from ..models.purchases import PurchasePhoto


def delete_item_photo(pk):
    """Delete an inventory item photo and its file."""
    photo = get_object_or_404(ItemPhoto, pk=pk)
    photo.image.delete(save=False)
    photo.delete()


def delete_purchase_photo(pk):
    """Delete a purchase photo and its file."""
    photo = get_object_or_404(PurchasePhoto, pk=pk)
    photo.image.delete(save=False)
    photo.delete()
