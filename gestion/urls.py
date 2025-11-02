from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Páginas principales
    path('', views.login_view, name='home'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('empleado-home/', views.empleado_home, name='empleado_home'),

    # Proyectos (admin)
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/nuevo/', views.nuevo_proyecto, name='nuevo_proyecto'),
    path('proyectos/<int:proyecto_id>/editar/', views.editar_proyecto, name='editar_proyecto'),
    path('proyectos/<int:proyecto_id>/eliminar/', views.eliminar_proyecto, name='eliminar_proyecto'),

    # Clientes (admin)
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('registrar/cliente/', views.registrar_cliente, name='registrar_cliente'),
    path('clientes/<int:cliente_id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:cliente_id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),

    # Empleados (admin)
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('registrar/usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('empleados/<int:empleado_id>/asignar/', views.asignar_proyecto_empleado, name='asignar_proyecto_empleado'),
    path('empleados/<int:empleado_id>/desasignar/<int:proyecto_id>/', views.desasignar_proyecto_empleado, name='desasignar_proyecto_empleado'),
    path('empleados/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('empleados/<int:usuario_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),

    # Registro de horas
    path('horas/registrar/', views.registrar_horas, name='registrar_horas'),
    path('horas/mis-horas/', views.mis_horas, name='mis_horas'),
    path('gestion/horas/', views.ver_registros_horas_admin, name='ver_registros_horas_admin'),

    # Reportes
    path('reportes/', views.reportes, name='reportes'),

    # Actividades (admin)
    path('admin/actividades/', views.ver_actividades, name='ver_actividades'),

    # Cambio de contraseña
    path('cambiar-password/', views.CambiarPasswordView.as_view(), name='cambiar_password'),
    path('password-exitoso/', views.password_exitoso, name='password_exitoso'),
]
