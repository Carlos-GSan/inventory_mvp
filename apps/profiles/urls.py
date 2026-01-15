from django.urls import path
from . import views

urlpatterns = [
    path('activate/<str:token>/', views.activate_account, name='activate_account'),
    path('perfil/', views.profile_edit, name='profile_edit'),
    path('empleados/', views.employee_list, name='employee_list'),
    path('empleados/nuevo/', views.employee_create, name='employee_create'),
    path('empleados/<int:pk>/reenviar-invitacion/', views.employee_resend_invitation, name='employee_resend_invitation'),
]