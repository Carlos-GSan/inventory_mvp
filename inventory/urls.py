from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Inventario
    path("inventario/", views.inventory_list, name="inventory_list"),
    path("inventario/nuevo/", views.inventory_create, name="inventory_create"),
    path("inventario/<int:pk>/editar/", views.inventory_update, name="inventory_update"),
    path("inventario/<int:pk>/ajustar/", views.inventory_adjust, name="inventory_adjust"),
    
    # Compras
    path("compras/", views.purchase_list, name="purchase_list"),
    path("compras/nueva/", views.purchase_create, name="purchase_create"),
    path("compras/<int:pk>/", views.purchase_detail, name="purchase_detail"),
    
    # Requisiciones
    path("requisiciones/", views.requisition_list, name="requisition_list"),
    path("requisiciones/nueva/", views.requisition_create, name="requisition_create"),
    path("requisiciones/<int:pk>/", views.requisition_detail, name="requisition_detail"),
]
