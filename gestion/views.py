from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
# from django.db.models import Sum
#from django.contrib.auth.models import User
from .models import Proyecto, RegistroHoras, Actividad, Cliente   
from .forms import ProyectoCreateForm, ProyectoUpdateForm,  RegistroHorasForm, ClienteForm, EmpleadoForm, CustomPasswordChangeForm
from django.utils import timezone
from django.db.models import Sum, Prefetch , F, Count
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CustomPasswordChangeForm
from .forms import ReporteFiltroForm

from .models import Proyecto, RegistroHoras, Actividad, AsignacionProyecto
from .forms import ProyectoCreateForm, RegistroHorasForm, AsignarProyectoForm


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


# Asegúrate de que esta línea esté al principio de tu archivo, junto a los otros imports
 

@login_required
def nuevo_proyecto(request):
    """Permite crear un nuevo proyecto (solo admin)."""
    if not request.user.is_staff:
        return redirect('empleado_home')

    if request.method == 'POST':
        # Aquí usamos el nuevo formulario de creación
        form = ProyectoCreateForm(request.POST) 
        if form.is_valid():
            proyecto = form.save()

            # ✅ Registrar acción (si tienes el modelo Actividad)
            # Actividad.objects.create(
            #     usuario=request.user,
            #     accion=f"Creó el proyecto '{proyecto.nombre}'."
            # )

            return redirect('lista_proyectos')
    else:
        # Aquí también usamos el nuevo formulario de creación
        form = ProyectoCreateForm() 

    return render(request, 'gestion/nuevo_proyecto.html', {'form': form})


@login_required
def editar_proyecto(request, proyecto_id):
    """Permite al administrador editar un proyecto existente."""
    if not request.user.is_staff:
        return redirect('empleado_home')

    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        form = ProyectoUpdateForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()

            # ✅ Registrar acción
            Actividad.objects.create(
                usuario=request.user,
                accion=f"Editó el proyecto '{proyecto.nombre}'."
            )

            return redirect('lista_proyectos')
    else:
        form = ProyectoUpdateForm(instance=proyecto)

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
        # 👇 *** AQUÍ: Pasamos el 'user' al formulario ***
        form = RegistroHorasForm(request.POST, user=request.user)
        
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
        # 👇 *** Y AQUÍ TAMBIÉN: Pasamos el 'user' al formulario vacío ***
        form = RegistroHorasForm(user=request.user)

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

    # ===== PASO 1: DEFINE 'registros' Y FILTROS =====
    # Define la variable 'registros' aquí al principio
    registros = RegistroHoras.objects.select_related('empleado', 'proyecto')

    # Obtiene los IDs de los filtros ANTES de calcular resúmenes
    empleado_id = request.GET.get('empleado')
    proyecto_id = request.GET.get('proyecto')

    # Aplica los filtros a 'registros' si existen
    if empleado_id:
        registros = registros.filter(empleado_id=empleado_id)
    if proyecto_id:
        registros = registros.filter(proyecto_id=proyecto_id)
    # ===============================================

    # ===== PASO 2: CALCULA RESÚMENES (usando 'registros') =====
    total_horas = registros.aggregate(total=Sum('horas'))['total'] or 0
    resumen_empleados = (
        registros.values('empleado__username')
        .annotate(total=Sum('horas'))
        .order_by('-total')
    )
    # ... (el resto del cálculo de resumen_proyectos_con_variacion que ya tienes) ...
    proyectos_con_registros_ids = registros.values_list('proyecto_id', flat=True).distinct()
    resumen_proyectos_qs = (
        Proyecto.objects.filter(id__in=proyectos_con_registros_ids)
        .annotate(
            total_horas_registradas=Sum('registros_horas__horas'),
            horas_presupuestadas_valor=F('cantidad_h')
        )
        .order_by('-total_horas_registradas')
    )
    resumen_proyectos_con_variacion = []
    for p in resumen_proyectos_qs:
        variacion = None
        presupuestado = p.horas_presupuestadas_valor
        registrado = p.total_horas_registradas if p.total_horas_registradas is not None else 0
        if presupuestado is not None:
             try:
                 variacion = float(registrado) - float(presupuestado)
             except (ValueError, TypeError):
                 variacion = None
        resumen_proyectos_con_variacion.append({
            'nombre': p.nombre,
            'horas_presupuestadas_valor': presupuestado,
            'total_horas_registradas': registrado,
            'variacion': variacion
        })
    # ====================================================

    # ===== PASO 3: OBTÉN DATOS PARA SELECTS =====
    empleados = User.objects.filter(is_staff=False)
    proyectos = Proyecto.objects.all()
    # ===========================================

    # ===== PASO 4: CREA EL CONTEXT =====
    context = {
        'registros': registros, # Ahora 'registros' ya existe
        'empleados': empleados,
        'proyectos': proyectos,
        'total_horas': total_horas,
        'resumen_empleados': resumen_empleados,
        'resumen_proyectos': resumen_proyectos_con_variacion,
        'empleado_id': empleado_id, # 'empleado_id' también debe estar definido antes
        'proyecto_id': proyecto_id, # 'proyecto_id' también debe estar definido antes
    }
    # ===================================

    return render(request, 'gestion/registro_horas_admin.html', context)


# === ADMINISTRADOR: VER BITÁCORA DE ACTIVIDADES FALTA RELACIONAR EL URLS Y DEFINIR LA BITACORA===
@login_required
def ver_actividades(request):
    """Muestra la bitácora de acciones registradas (solo admin)."""
    if not request.user.is_staff:
        return redirect('empleado_home')

    actividades = Actividad.objects.select_related('usuario').order_by('-fecha')[:100]
    return render(request, 'gestion/actividades.html', {'actividades': actividades})

#def registrar_cliente(request):
    # Más adelante, aquí podrías obtener la lista de clientes desde la base de datos
    # clientes = Cliente.objects.all()
    # context = {'clientes': clientes}

    # Por ahora, solo le decimos que muestre el archivo HTML
   # return render(request, 'gestion/registrar_cliente.html') #, context)

def registrar_usuario(request):
    # Más adelante, aquí podrías obtener la lista de clientes desde la base de datos
    # clientes = Cliente.objects.all()
    # context = {'clientes': clientes}

    # Por ahora, solo le decimos que muestre el archivo HTML
    return render(request, 'gestion/registrar_usuario.html') #, context)

def reportes(request):
    """
    Muestra el formulario de filtros y TRES reportes:
    1. Resumen por Proyecto (Agregado)
    2. Resumen por Empleado (Agregado)
    3. Bitácora de Horas (Detalle)
    """
    
    # 1. Obtenemos la base de todos los registros
    base_query = RegistroHoras.objects.select_related(
        'proyecto', 
        'empleado', 
        'proyecto__cliente'
    )
    
    # 2. Instanciamos el formulario (igual que antes)
    form = ReporteFiltroForm(request.GET)
    
    # 3. Aplicamos los filtros (igual que antes)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        
        if cleaned_data.get('cliente'):
            base_query = base_query.filter(proyecto__cliente=cleaned_data.get('cliente'))
            
        if cleaned_data.get('proyecto'):
            base_query = base_query.filter(proyecto=cleaned_data.get('proyecto'))
            
        if cleaned_data.get('empleado'):
            base_query = base_query.filter(empleado=cleaned_data.get('empleado'))
            
        if cleaned_data.get('fecha_inicio'):
            base_query = base_query.filter(fecha__gte=cleaned_data.get('fecha_inicio'))
            
        if cleaned_data.get('fecha_fin'):
            base_query = base_query.filter(fecha__lte=cleaned_data.get('fecha_fin'))

    reporte_bitacora = base_query.order_by('-fecha')

    # 4. GENERAR REPORTE POR PROYECTO
    reporte_proyectos_query = reporte_bitacora.values(
        'proyecto__id',
        'proyecto__nombre',
        'proyecto__cliente__nombre',
        'proyecto__cantidad_h'
    ).annotate(
        horas_registradas_filtradas=Sum('horas')
    ).order_by('-horas_registradas_filtradas')

    reporte_proyectos = []
    for p in reporte_proyectos_query:
        presupuestadas = p['proyecto__cantidad_h']
        registradas = p['horas_registradas_filtradas']
        
        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
        # Si 'Sum' no encuentra registros, devuelve None.
        # Debemos convertir None a 0 antes de calcular.
        if registradas is None:
            registradas = 0
        # --- FIN DE LA CORRECCIÓN ---
            
        if presupuestadas > 0:
            progreso = (registradas / presupuestadas) * 100
            horas_restantes = presupuestadas - registradas
        else:
            progreso = 0
            horas_restantes = 0
            
        p['progreso'] = round(progreso, 2)
        p['horas_restantes'] = horas_restantes
        reporte_proyectos.append(p)


    # 5. GENERAR REPORTE POR EMPLEADO
    reporte_empleados = reporte_bitacora.values(
        'empleado__id',
        'empleado__first_name',
        'empleado__last_name',
        'empleado__username'
    ).annotate(
        # --- ¡CORRECCIÓN AQUÍ TAMBIÉN! ---
        # Es buena práctica verificar 'None' también en las sumas de empleados.
        horas_totales=Sum('horas'),
        num_registros=Count('id')
    ).order_by('-horas_totales')
    
    # Procesamos los empleados para convertir 'None' en 0 si es necesario
    reporte_empleados_procesado = []
    for e in reporte_empleados:
        if e['horas_totales'] is None:
            e['horas_totales'] = 0
        reporte_empleados_procesado.append(e)


    # 6. Preparamos el contexto para el template
    contexto = {
        'form': form,
        'reporte_bitacora': reporte_bitacora,
        'reporte_proyectos': reporte_proyectos,
        # Pasamos la lista procesada
        'reporte_empleados': reporte_empleados_procesado, 
    }
    
    return render(request, 'gestion/reportes.html', contexto)

def empleados(request):
    # Más adelante, aquí podrías obtener la lista de clientes desde la base de datos
    # clientes = Cliente.objects.all()
    # context = {'clientes': clientes}

    # Por ahora, solo le decimos que muestre el archivo HTML
    return render(request, 'gestion/empleados.html') #, context)


# --- LISTA DE EMPLEADOS ---
@login_required
def lista_empleados(request):
    if not request.user.is_staff:
        return redirect('empleado_home')

    empleados = (
        User.objects
        .filter(is_staff=False, is_active=True)
        .prefetch_related(
            Prefetch(
                'proyectos_como_empleado',
                queryset=Proyecto.objects.only('id', 'nombre', 'situacion')
            ),
            Prefetch(
                'asignaciones',
                queryset=AsignacionProyecto.objects.select_related('proyecto').order_by('-activo', 'proyecto__nombre')
            )
        )
        .order_by('username')
    )

    return render(request, 'gestion/empleados.html', {'empleados': empleados})


# === GESTIÓN DE CLIENTES (ADMIN) ===
@login_required
def lista_clientes(request):
    if not request.user.is_staff:
        return redirect('empleado_home')

    clientes = Cliente.objects.all()

    context = {
        'clientes': clientes
    }

    return render(request, 'gestion/lista_clientes.html', context)


# --- ASIGNAR PROYECTO A EMPLEADO ---
@login_required
def asignar_proyecto_empleado(request, empleado_id):
    if not request.user.is_staff:
        return redirect('empleado_home')

    empleado = get_object_or_404(User, id=empleado_id, is_staff=False)

    if request.method == 'POST':
        form = AsignarProyectoForm(request.POST, empleado=empleado)
        if form.is_valid():
            asig = form.save(commit=False)
            asig.empleado = empleado
            asig.activo = True
            asig.fecha_asignacion = timezone.now().date()
            asig.save()

            Actividad.objects.create(
                usuario=request.user,
                accion=f"Asignó el proyecto '{asig.proyecto.nombre}' a {empleado.username} (rol: {asig.get_rol_en_proyecto_display()})."
            )

            return redirect('lista_empleados')
    else:
        form = AsignarProyectoForm(empleado=empleado)

    return render(request, 'gestion/asignar_proyecto.html', {
        'empleado': empleado,
        'form': form
    })


# --- DESASIGNAR (BAJA) PROYECTO DE EMPLEADO ---
@login_required
def desasignar_proyecto_empleado(request, empleado_id, proyecto_id):
    if not request.user.is_staff:
        return redirect('empleado_home')

    empleado = get_object_or_404(User, id=empleado_id, is_staff=False)
    asignacion = get_object_or_404(
        AsignacionProyecto,
        empleado=empleado,
        proyecto_id=proyecto_id,
        activo=True
    )

    if request.method == 'POST':
        asignacion.activo = False
        asignacion.fecha_baja = timezone.now().date()
        asignacion.save()

        Actividad.objects.create(
            usuario=request.user,
            accion=f"Desasignó el proyecto '{asignacion.proyecto.nombre}' de {empleado.username}."
        )

        return redirect('lista_empleados')

    # Confirmación simple
    return render(request, 'gestion/confirmar_desasignacion.html', {
        'empleado': empleado,
        'proyecto': asignacion.proyecto
    })

@login_required
def registrar_cliente(request):
    """
    Vista para crear un nuevo cliente.
    Solo accesible para administradores.
    """
   
    if not request.user.is_staff:
        return redirect('home') 


    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('admin_home') 
    else:
        
        form = ClienteForm() 

    return render(request, 'gestion/registrar_cliente.html', {'form': form})


@login_required
def registrar_usuario(request):
    # Solo los administradores pueden registrar empleados
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('admin_home') 
    else:
        form = EmpleadoForm()

    return render(request, 'gestion/registrar_usuario.html', {'form': form})

# === VISTA DE CAMBIO DE CONTRASEÑA (RECOMENDADA) ===
class CambiarPasswordView(LoginRequiredMixin, PasswordChangeView):
    """
    Vista para que el usuario cambie su contraseña.
    Usa la vista genérica de Django para máxima seguridad.
    """
    form_class = CustomPasswordChangeForm
    template_name = 'gestion/cambiar_password.html' # El template que crearemos en el Paso 4
    success_url = reverse_lazy('password_exitoso') # Una URL a dónde ir después (Paso 3)

    def get_form_kwargs(self):
        """
        Esto es clave: le pasa el usuario actual al formulario.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

# --- Vista simple para el éxito ---
# También necesitarás una vista simple que muestre un mensaje de éxito.
from django.shortcuts import render

@login_required
def password_exitoso(request):
    """Muestra un mensaje de éxito después de cambiar la contraseña."""
    return render(request, 'gestion/password_exitoso.html')