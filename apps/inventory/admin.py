from django.contrib import admin
from .models.purchases import Supplier, Purchase, PurchaseLine, PurchasePhoto
from .models.inventory import Category, InventoryItem, ItemPhoto
from .models.transactions import Requisition, RequisitionLine, InventoryTxn 


class ItemPhotoInline(admin.TabularInline):
    model = ItemPhoto
    extra = 1


class PurchasePhotoInline(admin.TabularInline):
    model = PurchasePhoto
    extra = 1


class PurchaseLineInline(admin.TabularInline):
    model = PurchaseLine
    extra = 1


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_name", "phone", "email", "rfc", "active")
    search_fields = ("name", "contact_name", "rfc", "email")
    list_filter = ("active",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("sku", "description", "category", "stock")
    search_fields = ("sku", "description")
    inlines = [ItemPhotoInline]

@admin.register(Requisition)
class RequisitionAdmin(admin.ModelAdmin):
    list_display = ("id", "requested_by", "requested_at", "created_at")
    search_fields = ("requested_by__username",)
    
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "purchased_at", "ref", "created_at")
    search_fields = ("supplier__name", "ref")
    list_filter = ("purchased_at",)
    inlines = [PurchaseLineInline, PurchasePhotoInline]

@admin.register(InventoryTxn)
class InventoryTxnAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "txn_type", "qty", "happened_at", "created_at")
    search_fields = ("item__name",)
    
    
@admin.register(PurchaseLine)
class PurchaseLineAdmin(admin.ModelAdmin):
    list_display = ("purchase", "item", "qty", "unit_price")
    search_fields = ("item__name",)
    
@admin.register(RequisitionLine)
class RequisitionLineAdmin(admin.ModelAdmin):
    list_display = ("requisition", "item", "qty")
    search_fields = ("item__name",)
    
