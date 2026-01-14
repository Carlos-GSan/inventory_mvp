from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Employee

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


