from django.contrib import admin
from django.contrib import messages
from .models import Employee
from .utils import send_activation_email  

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'position', 'is_active', 'platform_status']
    actions = ['send_activation_link']
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def platform_status(self, obj):
        if obj.user:
            return "✓ Activo"
        elif obj.activation_token:
            return "⏳ Pendiente"
        else:
            return "- Sin acceso"
    platform_status.short_description = 'Estado'
    
    def send_activation_link(self, request, queryset):
        """Envía link de activación a empleados seleccionados"""
        count = 0
        for employee in queryset:
            if not employee.user and employee.is_active:
                send_activation_email(employee)
                count += 1
        
        self.message_user(
            request,
            f"Link de activación enviado a {count} empleado(s)",
            messages.SUCCESS
        )
    send_activation_link.short_description = "📧 Enviar link de activación"