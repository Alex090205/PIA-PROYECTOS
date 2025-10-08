from django.urls import path
from . import views

urlpatterns = [
    # === AUTENTICACIÓN ===
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # === PÁGINAS PRINCIPALES ===
    path('', views.login_view, name='home'),
    path('admin-home/', views.admin_home, name='admin_home'),
    path('empleado-home/', views.empleado_home, name='empleado_home'),

    # === ADMINISTRADOR: Gestión de proyectos ===
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/nuevo/', views.nuevo_proyecto, name='nuevo_proyecto'),
    path('proyectos/<int:proyecto_id>/editar/', views.editar_proyecto, name='editar_proyecto'),
    path('proyectos/<int:proyecto_id>/eliminar/', views.eliminar_proyecto, name='eliminar_proyecto'),

    # === EMPLEADO: Registro de horas ===
    path('horas/registrar/', views.registrar_horas, name='registrar_horas'),
    path('horas/mis-horas/', views.mis_horas, name='mis_horas'),

    # === ADMINISTRADOR: Ver todos los registros de horas ===
    path('gestion/horas/', views.ver_registros_horas_admin, name='ver_registros_horas_admin'),
    path('admin/actividades/', views.ver_actividades, name='ver_actividades'),

]
