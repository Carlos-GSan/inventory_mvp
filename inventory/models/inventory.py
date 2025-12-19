from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    
    def __str__(self):
        return self.name
    
class InventoryItem(models.Model):
    sku = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items")
    
    description = models.CharField(max_length=250)
    
    stock = models.PositiveIntegerField()
    min_stock = models.PositiveIntegerField()
    max_stock = models.PositiveIntegerField()
    
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "active"]),
            models.Index(fields=["slug"]),
        ]
        
    def __str__(self):
        return f"{self.sku} - {self.description}"