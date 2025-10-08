from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.contrib.auth.models import User
from .models import Proyecto, RegistroHoras, Actividad   # ✅ Importamos Actividad
from .forms import ProyectoForm, RegistroHorasForm


# === LOGIN ===
def login_view(request):
    """Vista para iniciar sesión."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # ✅ Registrar acción en la bitácora
            Actividad.objects.create(
                usuario=user,
                accion=f"Inició sesión en el sistema."
            )

            return redirect('admin_home' if user.is_staff else 'empleado_home')
    else:
        form = AuthenticationForm()
    return render(request, 'gestion/login.html', {'form': form})


# === LOGOUT ===
@login_required
def logout_view(request):
    """Cierra sesión y redirige al login."""
    # ✅ Registrar acción en la bitácora
    Actividad.objects.create(
        usuario=request.user,
        accion=f"Cerró sesión."
    )

    logout(request)
    return redirect('login')


# === ADMINISTRADOR ===
@login_required
def admin_home(request):
    """Panel principal del administrador."""
    return render(request, 'gestion/admin_home.html')


# === EMPLEADO ===
@login_required
def empleado_home(request):
    """Panel principal del empleado."""
    return render(request, 'gestion/empleado_home.html')


# === GESTIÓN DE PROYECTOS (ADMIN) ===
@login_required
def lista_proyectos(request):
    """Muestra todos los proyectos (solo admin)."""
    if not request.user.is_staff:
        return redirect('empleado_home')
    proyectos = Proyecto.objects.select_related('cliente').all()
    return render(request, 'gestion/proyectos.html', {'proyectos': proyectos})


@login_required
def nuevo_proyecto(request):
    """Permite crear un nuevo proyecto (solo admin)."""
    if not request.user.is_staff:
        return redirect('empleado_home')

    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save()

            # ✅ Registrar acción
            Actividad.objects.create(
                usuario=request.user,
                accion=f"Creó el proyecto '{proyecto.nombre}'."
            )

            return redirect('lista_proyectos')
    else:
        form = ProyectoForm()

    return render(request, 'gestion/nuevo_proyecto.html', {'form': form})


@login_required
def editar_proyecto(request, proyecto_id):
    """Permite al administrador editar un proyecto existente."""
    if not request.user.is_staff:
        return redirect('empleado_home')

    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()

            # ✅ Registrar acción
            Actividad.objects.create(
                usuario=request.user,
                accion=f"Editó el proyecto '{proyecto.nombre}'."
            )

            return redirect('lista_proyectos')
    else:
        form = ProyectoForm(instance=proyecto)

    return render(request, 'gestion/editar_proyecto.html', {'form': form, 'proyecto': proyecto})


@login_required
def eliminar_proyecto(request, proyecto_id):
    """Permite al administrador eliminar un proyecto."""
    if not request.user.is_staff:
        return redirect('empleado_home')

    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        nombre = proyecto.nombre
        proyecto.delete()

        # ✅ Registrar acción
        Actividad.objects.create(
            usuario=request.user,
            accion=f"Eliminó el proyecto '{nombre}'."
        )

        return redirect('lista_proyectos')

    return render(request, 'gestion/eliminar_proyecto.html', {'proyecto': proyecto})


# === REGISTRO DE HORAS (EMPLEADOS) ===
@login_required
def registrar_horas(request):
    """Permite al empleado registrar sus horas trabajadas."""
    if request.user.is_staff:
        return redirect('admin_home')

    if request.method == 'POST':
        form = RegistroHorasForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.empleado = request.user
            registro.save()

            # ✅ Registrar acción
            Actividad.objects.create(
                usuario=request.user,
                accion=f"Registró {registro.horas} horas en el proyecto '{registro.proyecto.nombre}'."
            )

            return redirect('mis_horas')
    else:
        form = RegistroHorasForm()

    return render(request, 'gestion/registrar_horas.html', {'form': form})


@login_required
def mis_horas(request):
    """Muestra las horas registradas por el empleado autenticado."""
    if request.user.is_staff:
        return redirect('admin_home')

    horas = RegistroHoras.objects.filter(empleado=request.user).select_related('proyecto')
    return render(request, 'gestion/mis_horas.html', {'horas': horas})


# === ADMINISTRADOR: VER REGISTROS DE HORAS ===
@login_required
def ver_registros_horas_admin(request):
    """
    Muestra todos los registros de horas con filtros y resúmenes.
    Solo accesible para administradores.
    """
    if not request.user.is_staff:
        return redirect('empleado_home')

    registros = RegistroHoras.objects.select_related('empleado', 'proyecto')

    # --- FILTROS OPCIONALES ---
    empleado_id = request.GET.get('empleado')
    proyecto_id = request.GET.get('proyecto')

    if empleado_id:
        registros = registros.filter(empleado_id=empleado_id)
    if proyecto_id:
        registros = registros.filter(proyecto_id=proyecto_id)

    # --- RESÚMENES ---
    total_horas = registros.aggregate(total=Sum('horas'))['total'] or 0
    resumen_empleados = (
        registros.values('empleado__username')
        .annotate(total=Sum('horas'))
        .order_by('-total')
    )
    resumen_proyectos = (
        registros.values('proyecto__nombre')
        .annotate(total=Sum('horas'))
        .order_by('-total')
    )

    # --- DATOS PARA SELECT DE FILTROS ---
    empleados = User.objects.filter(is_staff=False)
    proyectos = Proyecto.objects.all()

    context = {
        'registros': registros,
        'empleados': empleados,
        'proyectos': proyectos,
        'total_horas': total_horas,
        'resumen_empleados': resumen_empleados,
        'resumen_proyectos': resumen_proyectos,
        'empleado_id': empleado_id,
        'proyecto_id': proyecto_id,
    }

    return render(request, 'gestion/registro_horas_admin.html', context)


# === ADMINISTRADOR: VER BITÁCORA DE ACTIVIDADES ===
@login_required
def ver_actividades(request):
    """Muestra la bitácora de acciones registradas (solo admin)."""
    if not request.user.is_staff:
        return redirect('empleado_home')

    actividades = Actividad.objects.select_related('usuario').order_by('-fecha')[:100]
    return render(request, 'gestion/actividades.html', {'actividades': actividades})
