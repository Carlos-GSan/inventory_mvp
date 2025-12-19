from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, Count
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import re
from .models.inventory import Category, InventoryItem
from .models.compras import Supplier, Purchase, PurchaseLine
from .models.transactions import Requisition, RequisitionLine, InventoryTxn


def parse_form_lines(post_data):
    """Parsea las líneas del formulario con formato lines[0][field]"""
    lines_data = {}
    pattern = re.compile(r'lines\[(\d+)\]\[(\w+)\]')
    
    for key, value in post_data.items():
        match = pattern.match(key)
        if match:
            line_idx = match.group(1)
            field = match.group(2)
            
            if line_idx not in lines_data:
                lines_data[line_idx] = {}
            lines_data[line_idx][field] = value
    
    return lines_data


@login_required
def dashboard(request):
    """Dashboard principal con estadísticas"""
    now = timezone.now()
    first_day_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stats = {
        'total_items': InventoryItem.objects.filter(active=True).count(),
        'low_stock_items': InventoryItem.objects.filter(
            active=True,
            stock__lte=F('min_stock')
        ).count(),
        'total_purchases': Purchase.objects.filter(created_at__gte=first_day_month).count(),
        'total_requisitions': Requisition.objects.filter(created_at__gte=first_day_month).count(),
    }
    
    low_stock_items = InventoryItem.objects.filter(
        active=True,
        stock__lte=F('min_stock')
    ).select_related('category').order_by('stock')[:10]
    
    recent_transactions = InventoryTxn.objects.select_related(
        'item', 'supplier', 'purchase', 'requisition'
    ).order_by('-happened_at')[:10]
    
    context = {
        'stats': stats,
        'low_stock_items': low_stock_items,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard.html', context)


@login_required
def inventory_list(request):
    """Lista de inventario con filtros"""
    items = InventoryItem.objects.filter(active=True).select_related('category')
    
    # Filtros
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    if search:
        items = items.filter(
            Q(sku__icontains=search) | Q(description__icontains=search)
        )
    
    if category_id:
        items = items.filter(category_id=category_id)
    
    categories = Category.objects.all()
    
    context = {
        'items': items.order_by('sku'),
        'categories': categories,
    }
    return render(request, 'inventory/list.html', context)


@login_required
def inventory_create(request):
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            item = InventoryItem.objects.create(
                sku=request.POST['sku'],
                slug=request.POST['slug'],
                category_id=request.POST['category'],
                description=request.POST['description'],
                stock=int(request.POST['stock']),
                min_stock=int(request.POST['min_stock']),
                max_stock=int(request.POST['max_stock']),
                active='active' in request.POST
            )
            messages.success(request, f'Producto {item.sku} creado exitosamente')
            return redirect('inventory_list')
        except Exception as e:
            messages.error(request, f'Error al crear producto: {str(e)}')
    
    categories = Category.objects.all()
    context = {
        'title': 'Nuevo Producto',
        'categories': categories,
        'form': {}
    }
    return render(request, 'inventory/form.html', context)


@login_required
def inventory_update(request, pk):
    """Actualizar producto existente"""
    item = get_object_or_404(InventoryItem, pk=pk)
    
    if request.method == 'POST':
        try:
            item.sku = request.POST['sku']
            item.slug = request.POST['slug']
            item.category_id = request.POST['category']
            item.description = request.POST['description']
            item.stock = int(request.POST['stock'])
            item.min_stock = int(request.POST['min_stock'])
            item.max_stock = int(request.POST['max_stock'])
            item.active = 'active' in request.POST
            item.save()
            
            messages.success(request, f'Producto {item.sku} actualizado exitosamente')
            return redirect('inventory_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar producto: {str(e)}')
    
    categories = Category.objects.all()
    context = {
        'title': 'Editar Producto',
        'categories': categories,
        'form': {
            'sku': {'value': item.sku},
            'slug': {'value': item.slug},
            'description': {'value': item.description},
            'category': {'value': item.category_id},
            'stock': {'value': item.stock},
            'min_stock': {'value': item.min_stock},
            'max_stock': {'value': item.max_stock},
            'active': {'value': item.active},
        }
    }
    return render(request, 'inventory/form.html', context)


@login_required
def inventory_adjust(request, pk):
    """Ajustar stock de un producto"""
    item = get_object_or_404(InventoryItem, pk=pk)
    
    if request.method == 'POST':
        try:
            qty = int(request.POST['qty'])
            note = request.POST.get('note', '')
            
            # Actualizar stock
            item.stock += qty
            item.save()
            
            # Registrar transacción
            InventoryTxn.objects.create(
                item=item,
                txn_type=InventoryTxn.TXN_ADJUST,
                qty=qty,
                happened_at=timezone.now(),
                note=note
            )
            
            messages.success(request, f'Stock de {item.sku} ajustado exitosamente. Nuevo stock: {item.stock}')
            return redirect('inventory_list')
        except Exception as e:
            messages.error(request, f'Error al ajustar stock: {str(e)}')
    
    context = {'item': item}
    return render(request, 'inventory/adjust.html', context)


@login_required
def purchase_list(request):
    """Lista de compras"""
    purchases = Purchase.objects.select_related('supplier').prefetch_related('lines').order_by('-purchased_at')
    
    # Calcular total de cada compra
    for purchase in purchases:
        purchase.total = sum(line.qty * line.unit_price for line in purchase.lines.all())
    
    context = {'purchases': purchases}
    return render(request, 'purchases/list.html', context)


@login_required
def purchase_create(request):
    """Crear nueva compra"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Procesar líneas usando el helper
                lines_data = parse_form_lines(request.POST)
                
                # Validar que hay líneas con datos completos
                valid_lines = []
                for line_data in lines_data.values():
                    if line_data.get('item') and line_data.get('qty') and line_data.get('unit_price'):
                        valid_lines.append(line_data)
                
                if not valid_lines:
                    raise ValueError('Debe agregar al menos un producto a la compra')
                
                # Crear compra
                purchase = Purchase.objects.create(
                    supplier_id=request.POST['supplier'],
                    purchased_at=request.POST['purchased_at'],
                    ref=request.POST.get('ref', '')
                )
                
                # Crear líneas y actualizar stock
                for line_data in valid_lines:
                    item = InventoryItem.objects.select_for_update().get(pk=line_data['item'])
                    qty = int(line_data['qty'])
                    unit_price = float(line_data['unit_price'])
                    
                    # Crear línea de compra
                    PurchaseLine.objects.create(
                        purchase=purchase,
                        item=item,
                        qty=qty,
                        unit_price=unit_price
                    )
                    
                    # Actualizar stock
                    item.stock += qty
                    item.save()
                    
                    # Registrar transacción
                    InventoryTxn.objects.create(
                        item=item,
                        txn_type=InventoryTxn.TXN_PURCHASE,
                        qty=qty,
                        unit_price=unit_price,
                        supplier=purchase.supplier,
                        purchase=purchase,
                        happened_at=timezone.now(),
                        note=f'Compra #{purchase.id}'
                    )
                
                messages.success(request, f'Compra #{purchase.id} creada exitosamente')
                return redirect('purchase_detail', pk=purchase.pk)
        except Exception as e:
            messages.error(request, f'Error al crear compra: {str(e)}')
    
    suppliers = Supplier.objects.all()
    items = InventoryItem.objects.filter(active=True).order_by('sku')
    
    context = {
        'suppliers': suppliers,
        'items': items,
    }
    return render(request, 'purchases/create.html', context)


@login_required
def purchase_detail(request, pk):
    """Detalle de una compra"""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    # Cargar líneas y calcular subtotales
    lines = list(purchase.lines.all())
    total = 0
    for line in lines:
        line.subtotal = line.qty * line.unit_price
        total += line.subtotal
    
    purchase.total = total
    purchase.lines_with_subtotal = lines
    
    context = {'purchase': purchase}
    return render(request, 'purchases/detail.html', context)


@login_required
def requisition_list(request):
    """Lista de requisiciones"""
    requisitions = Requisition.objects.select_related('requested_by').order_by('-requested_at')
    context = {'requisitions': requisitions}
    return render(request, 'requisitions/list.html', context)


@login_required
def requisition_create(request):
    """Crear nueva requisición"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Procesar líneas usando el helper
                lines_data = parse_form_lines(request.POST)
                
                # Validar que hay líneas con datos completos
                valid_lines = []
                for line_data in lines_data.values():
                    if line_data.get('item') and line_data.get('qty'):
                        valid_lines.append(line_data)
                
                if not valid_lines:
                    raise ValueError('Debe agregar al menos un producto a la requisición')
                
                # Crear requisición
                requisition = Requisition.objects.create(
                    requested_by=request.user,
                    requested_at=request.POST['requested_at'],
                    note=request.POST.get('note', '')
                )
                
                # Crear líneas y actualizar stock
                for line_data in valid_lines:
                    item = InventoryItem.objects.select_for_update().get(pk=line_data['item'])
                    qty = int(line_data['qty'])
                    
                    # Validar stock disponible
                    if item.stock < qty:
                        raise ValueError(f'Stock insuficiente para {item.sku}. Disponible: {item.stock}, Solicitado: {qty}')
                    
                    # Crear línea de requisición
                    RequisitionLine.objects.create(
                        requisition=requisition,
                        item=item,
                        qty=qty
                    )
                    
                    # Reducir stock
                    item.stock -= qty
                    item.save()
                    
                    # Registrar transacción
                    InventoryTxn.objects.create(
                        item=item,
                        txn_type=InventoryTxn.TXN_ISSUE,
                        qty=-qty,
                        requisition=requisition,
                        happened_at=timezone.now(),
                        note=f'Requisición #{requisition.id}'
                    )
                
                messages.success(request, f'Requisición #{requisition.id} creada exitosamente')
                return redirect('requisition_detail', pk=requisition.pk)
        except Exception as e:
            messages.error(request, f'Error al crear requisición: {str(e)}')
    
    items = InventoryItem.objects.filter(active=True).order_by('sku')
    
    context = {'items': items}
    return render(request, 'requisitions/create.html', context)


@login_required
def requisition_detail(request, pk):
    """Detalle de una requisición"""
    requisition = get_object_or_404(Requisition, pk=pk)
    context = {'requisition': requisition}
    return render(request, 'requisitions/detail.html', context)
