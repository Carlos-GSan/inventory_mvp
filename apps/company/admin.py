from django.contrib import admin
from apps.company.models.company import Company

# Register your models here.
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "website")
    search_fields = ("name", "email")