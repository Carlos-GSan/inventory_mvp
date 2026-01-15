from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum, F, Count
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import re
from .models.inventory import Category, InventoryItem
from .models.purchases import Supplier, Purchase, PurchaseLine
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
    
    if request.user.is_staff:
        # Admin ve todas las estadísticas
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
        
        # Transacciones con filtros y paginación
        transactions_qs = InventoryTxn.objects.select_related(
            'item', 'supplier', 'purchase', 'requisition'
        )
    else:
        # Usuario normal solo ve sus propias estadísticas
        stats = {
            'total_items': 0,
            'low_stock_items': 0,
            'total_purchases': 0,
            'total_requisitions': Requisition.objects.filter(
                requested_by=request.user,
                created_at__gte=first_day_month
            ).count(),
        }
        
        low_stock_items = []
        
        # Solo transacciones de sus requisiciones
        transactions_qs = InventoryTxn.objects.filter(
            requisition__requested_by=request.user
        ).select_related(
            'item', 'supplier', 'purchase', 'requisition'
        )
    
    # Aplicar filtros a transacciones
    item_filter = request.GET.get('item', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if item_filter:
        transactions_qs = transactions_qs.filter(
            Q(item__sku__icontains=item_filter) | 
            Q(item__description__icontains=item_filter)
        )
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            transactions_qs = transactions_qs.filter(happened_at__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Agregar 1 día para incluir todo el día seleccionado
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            transactions_qs = transactions_qs.filter(happened_at__lte=date_to_obj)
        except ValueError:
            pass
    
    transactions_qs = transactions_qs.order_by('-happened_at')
    
    # Paginación
    paginator = Paginator(transactions_qs, 10)  # 10 transacciones por página
    page_number = request.GET.get('page', 1)
    recent_transactions = paginator.get_page(page_number)
    
    # Obtener todos los productos activos para el filtro
    all_items = InventoryItem.objects.filter(active=True).values('id', 'sku', 'description').order_by('sku')
    
    context = {
        'stats': stats,
        'low_stock_items': low_stock_items,
        'recent_transactions': recent_transactions,
        'all_items': all_items,
        'item_filter': item_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    # Si es una petición HTMX, devolver solo la tabla de transacciones
    if request.headers.get('HX-Request'):
        return render(request, 'partials/transactions_table.html', context)
    
    return render(request, 'dashboard.html', context)


@login_required
@permission_required('inventory.view_inventoryitem', raise_exception=True)
def inventory_list(request):
    """Lista de inventario con filtros y paginación"""
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
    
    items = items.order_by('sku')
    
    # Paginación
    per_page = request.GET.get('per_page', '10')
    try:
        per_page_int = int(per_page)
        if per_page_int not in [10, 20, 45]:
            per_page_int = 10
    except (ValueError, TypeError):
        per_page_int = 10
    
    paginator = Paginator(items, per_page_int)
    page_number = request.GET.get('page', 1)
    items_page = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'items': items_page,
        'categories': categories,
        'search': search,
        'category_id': category_id,
        'per_page': per_page,
    }
    
    # Si es una petición HTMX, devolver solo la tabla
    if request.headers.get('HX-Request'):
        return render(request, 'partials/inventory_table.html', context)
    
    return render(request, 'inventory/list.html', context)


@login_required
@permission_required('inventory.add_inventoryitem', raise_exception=True)
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
@permission_required('inventory.change_inventoryitem', raise_exception=True)
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
@permission_required('inventory.view_inventoryitem', raise_exception=True)
def inventory_print_label(request, pk):
    """Imprimir etiqueta con código de barras del producto"""
    item = get_object_or_404(InventoryItem, pk=pk, active=True)
    
    context = {
        'item': item,
    }
    return render(request, 'inventory/print_label.html', context)


@login_required
@permission_required('inventory.view_inventoryitem', raise_exception=True)
def inventory_print_labels(request):
    """Imprimir múltiples etiquetas con códigos de barras"""
    ids_str = request.GET.get('ids', '')
    
    if not ids_str:
        messages.error(request, 'No se seleccionaron productos')
        return redirect('inventory_list')
    
    try:
        ids = [int(id_str.strip()) for id_str in ids_str.split(',') if id_str.strip()]
        items = InventoryItem.objects.filter(pk__in=ids, active=True).select_related('category')
        
        if not items.exists():
            messages.error(request, 'No se encontraron productos válidos')
            return redirect('inventory_list')
        
        context = {
            'items': items,
        }
        return render(request, 'inventory/print_labels.html', context)
    except ValueError:
        messages.error(request, 'IDs de productos inválidos')
        return redirect('inventory_list')


@login_required
@permission_required('inventory.change_inventoryitem', raise_exception=True)
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
@permission_required('inventory.view_purchase', raise_exception=True)
def purchase_list(request):
    """Lista de compras con filtros y paginación"""
    purchases = Purchase.objects.select_related('supplier').prefetch_related('lines').order_by('-purchased_at')
    
    # Filtro por proveedor
    supplier_id = request.GET.get('supplier', '')
    if supplier_id:
        purchases = purchases.filter(supplier_id=supplier_id)
    
    # Calcular total de cada compra
    for purchase in purchases:
        purchase.total = sum(line.qty * line.unit_price for line in purchase.lines.all())
    
    # Paginación
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 45]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    paginator = Paginator(purchases, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Lista de proveedores para el filtro
    suppliers = Supplier.objects.order_by('name')
    
    context = {
        'page_obj': page_obj,
        'per_page': per_page,
        'suppliers': suppliers,
        'supplier_id': supplier_id,
    }
    
    # Si es petición HTMX, devolver solo la tabla
    if request.headers.get('HX-Request'):
        return render(request, 'partials/purchases_table.html', context)
    
    return render(request, 'purchases/list.html', context)


@login_required
@permission_required('inventory.add_purchase', raise_exception=True)
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
@permission_required('inventory.view_purchase', raise_exception=True)
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
@permission_required('inventory.view_requisition', raise_exception=True)
def requisition_list(request):
    """Lista de requisiciones con filtros y paginación"""
    if request.user.is_staff:
        # Admin ve todas las requisiciones
        requisitions = Requisition.objects.select_related('requested_by').order_by('-requested_at')
    else:
        # Usuario normal solo ve sus propias requisiciones
        requisitions = Requisition.objects.filter(
            requested_by=request.user
        ).select_related('requested_by').order_by('-requested_at')
    
    # Filtro por solicitante (solo para staff)
    solicitante_id = request.GET.get('solicitante', '')
    if request.user.is_staff and solicitante_id:
        requisitions = requisitions.filter(requested_by_id=solicitante_id)
    
    # Paginación
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 45]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    paginator = Paginator(requisitions, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Lista de solicitantes para el filtro (solo para staff)
    solicitantes = None
    if request.user.is_staff:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        solicitantes = User.objects.filter(
            requisitions__isnull=False
        ).distinct().order_by('first_name', 'last_name', 'username')
    
    context = {
        'page_obj': page_obj,
        'per_page': per_page,
        'solicitantes': solicitantes,
        'solicitante_id': solicitante_id,
    }
    
    # Si es petición HTMX, devolver solo la tabla
    if request.headers.get('HX-Request'):
        return render(request, 'partials/requisitions_table.html', context)
    
    return render(request, 'requisitions/list.html', context)


@login_required
@permission_required('inventory.add_requisition', raise_exception=True)
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
@permission_required('inventory.view_requisition', raise_exception=True)
def requisition_detail(request, pk):
    """Detalle de una requisición"""
    requisition = get_object_or_404(Requisition, pk=pk)
    
    # Usuario no-admin solo puede ver sus propias requisiciones
    if not request.user.is_staff and requisition.requested_by != request.user:
        raise PermissionDenied("No tienes permiso para ver esta requisición.")
    
    context = {'requisition': requisition}
    return render(request, 'requisitions/detail.html', context)
