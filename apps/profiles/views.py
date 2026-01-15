from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Employee
from .utils import send_activation_email

def activate_account(request, token):
    """Vista para que el empleado cree su cuenta"""
    employee = get_object_or_404(Employee, activation_token=token)
    
    if not employee.is_token_valid(token):
        messages.error(request, 'El enlace de activación ha expirado o es inválido.')
        return redirect('login')
    
    if employee.user:
        messages.info(request, 'Esta cuenta ya ha sido activada.')
        return redirect('login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validaciones
        if not username or not password:
            messages.error(request, 'Usuario y contraseña son requeridos.')
        elif password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
        else:
            # Crear usuario
            employee.activate_account(username, password)
            messages.success(request, '¡Cuenta activada exitosamente! Ya puedes iniciar sesión.')
            return redirect('login')
    
    context = {
        'employee': employee,
        'token': token
    }
    return render(request, 'profiles/activate_account.html', context)


@login_required
def profile_edit(request):
    """Vista para editar el perfil del usuario"""
    # Obtener o crear Employee
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        # Crear Employee con email único temporal si el user.email ya existe
        email = request.user.email if request.user.email else f"{request.user.username}@temp.local"
        employee = Employee.objects.create(
            user=request.user,
            first_name=request.user.first_name or '',
            last_name=request.user.last_name or '',
            email=email,
            position='',
            department='',
            hire_date=timezone.now().date()
        )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                position = request.POST.get('position', '').strip()
                department = request.POST.get('department', '').strip()
                
                # Validar email único (excepto el propio)
                if email and Employee.objects.filter(email=email).exclude(id=employee.id).exists():
                    messages.error(request, 'Este correo electrónico ya está en uso por otro usuario.')
                    return redirect('profile_edit')
                
                # Validar teléfono único (excepto el propio)
                if phone and Employee.objects.filter(phone=phone).exclude(id=employee.id).exists():
                    messages.error(request, 'Este número de teléfono ya está en uso por otro usuario.')
                    return redirect('profile_edit')
                
                # Actualizar User
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()
                
                # Actualizar Employee
                employee.first_name = first_name
                employee.last_name = last_name
                employee.email = email
                employee.phone = phone if phone else None
                employee.position = position
                employee.department = department
                
                # Manejar foto
                if request.FILES.get('photo'):
                    employee.photo = request.FILES['photo']
                
                employee.save()
                
                messages.success(request, '¡Perfil actualizado exitosamente!')
                return redirect('profile_edit')
        except Exception as e:
            messages.error(request, f'Error al actualizar perfil: {str(e)}')
    
    context = {
        'employee': employee
    }
    return render(request, 'profiles/edit.html', context)


@login_required
@permission_required('profiles.view_employee', raise_exception=True)
def employee_list(request):
    """Lista de empleados para RRHH"""
    employees = Employee.objects.select_related('user').order_by('-created_at')
    
    # Filtros
    search = request.GET.get('search', '')
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    
    if search:
        employees = employees.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    if department:
        employees = employees.filter(department__icontains=department)
    
    if status == 'active':
        employees = employees.filter(is_active=True)
    elif status == 'inactive':
        employees = employees.filter(is_active=False)
    elif status == 'with_access':
        employees = employees.filter(user__isnull=False)
    elif status == 'without_access':
        employees = employees.filter(user__isnull=True)
    
    # Paginación
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 45]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    paginator = Paginator(employees, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Departamentos únicos para filtro
    departments = Employee.objects.values_list('department', flat=True).distinct().order_by('department')
    
    context = {
        'page_obj': page_obj,
        'per_page': per_page,
        'search': search,
        'department': department,
        'status': status,
        'departments': departments,
    }
    
    # Si es petición HTMX, devolver solo la tabla
    if request.headers.get('HX-Request'):
        return render(request, 'partials/employees_table.html', context)
    
    return render(request, 'profiles/employee_list.html', context)


@login_required
@permission_required('profiles.add_employee', raise_exception=True)
def employee_create(request):
    """Crear nuevo empleado"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                position = request.POST.get('position', '').strip()
                department = request.POST.get('department', '').strip()
                hire_date = request.POST.get('hire_date', '')
                send_invitation = request.POST.get('send_invitation') == 'on'
                
                # Validaciones
                if not all([first_name, last_name, email, position, department, hire_date]):
                    messages.error(request, 'Todos los campos obligatorios deben ser completados.')
                    return redirect('employee_create')
                
                # Verificar email único
                if Employee.objects.filter(email=email).exists():
                    messages.error(request, 'Ya existe un empleado con este correo electrónico.')
                    return redirect('employee_create')
                
                # Verificar teléfono único
                if phone and Employee.objects.filter(phone=phone).exists():
                    messages.error(request, 'Ya existe un empleado con este número de teléfono.')
                    return redirect('employee_create')
                
                # Crear empleado
                employee = Employee.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone if phone else None,
                    position=position,
                    department=department,
                    hire_date=hire_date,
                    is_active=True
                )
                
                # Manejar foto
                if request.FILES.get('photo'):
                    employee.photo = request.FILES['photo']
                    employee.save()
                
                # Enviar invitación
                if send_invitation:
                    try:
                        send_activation_email(employee)
                        messages.success(request, f'Empleado creado exitosamente. Se ha enviado una invitación a {email}.')
                    except Exception as e:
                        messages.warning(request, f'Empleado creado pero hubo un error al enviar el email: {str(e)}')
                else:
                    messages.success(request, 'Empleado creado exitosamente.')
                
                return redirect('employee_list')
        except Exception as e:
            messages.error(request, f'Error al crear empleado: {str(e)}')
    
    return render(request, 'profiles/employee_create.html')


@login_required
@permission_required('profiles.change_employee', raise_exception=True)
def employee_resend_invitation(request, pk):
    """Reenviar invitación de activación"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if employee.user:
        messages.warning(request, 'Este empleado ya tiene una cuenta activada.')
        return redirect('employee_list')
    
    try:
        send_activation_email(employee)
        messages.success(request, f'Invitación reenviada a {employee.email}.')
    except Exception as e:
        messages.error(request, f'Error al enviar invitación: {str(e)}')
    
    return redirect('employee_list')


