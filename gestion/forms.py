from django import forms
from django.contrib.auth.models import User
from .models import Proyecto, RegistroHoras, AsignacionProyecto, Cliente, PerfilEmpleado
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm


# === FORMULARIO DE PROYECTOS (SOLO ACCESO AL ADMINISTRADOR) ===
# gestion/forms.py

# ... (tus otros imports y el ClienteForm se quedan igual) ...

# === FORMULARIO PARA CREAR UN PROYECTO (SIN 'situacion') ===
# gestion/forms.py

class ProyectoCreateForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = [
            'nombre',
            'descripcion',
            'fecha_inicial',
            'fecha_final',
            'cantidad_h',
            'cliente',
            'administradores',
        ]
        # Este es el diccionario que debemos ajustar
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proyecto'}),
            
            # Para que la descripción se vea como un campo normal
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Descripción breve del proyecto',
                'rows': 3  # <--- Esta línea controla la altura
            }),
            # Para el calendario en la fecha inicial
            'fecha_inicial': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            
            # Para el calendario en la fecha final
            'fecha_final': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            
            'cantidad_h': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Horas presupuestadas'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'administradores': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    # Tu método clean() se queda igual
    def clean(self):
        # ... (tu código de validación sin cambios)
        return super().clean()

# === FORMULARIO PARA EDITAR UN PROYECTO (CON 'situacion') ===
class ProyectoUpdateForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        # Esta lista es idéntica a la anterior, pero SÍ incluye 'situacion'
        fields = [
            'nombre',
            'descripcion',
            'fecha_inicial',
            'fecha_final',
            'cantidad_h',
            'situacion',  # <-- La única diferencia es esta línea
            'cliente',
            'administradores',
        ]
        widgets = {
            # ... (todos tus widgets, incluyendo el de 'situacion')
        }

    def clean(self):
        # ... (tu código de validación sin cambios)
        return super().clean()


# === FORMULARIO DE REGISTRO DE HORAS (SOLO PARA EMPLEADOS) ===
class RegistroHorasForm(forms.ModelForm):
    """
    Formulario para que los empleados registren sus horas trabajadas
    en un proyecto activo.
    Incluye validaciones para evitar errores comunes.
    """

    # === NUEVO MÉTODO __init__ ===
    def __init__(self, *args, **kwargs):
        # Extraemos el 'user' que le pasaremos desde la vista
        user = kwargs.pop('user', None)
        
        # Llamamos al constructor original
        super().__init__(*args, **kwargs)
        
        # Si el usuario existe (¡que debería!), filtramos el campo 'proyecto'
        if user:
            # Esta es la magia:
            # Le decimos al campo 'proyecto' que su lista de opciones (queryset)
            # sea SOLAMENTE los proyectos de la relación 'proyectos_como_empleado'
            # que pertenecen a ese usuario.
            self.fields['proyecto'].queryset = user.proyectos_como_empleado.all()

            # --- MEJORA OPCIONAL (Recomendada) ---
            # Basado en tu método clean(), podemos optimizar esto
            # para que ni siquiera muestre proyectos finalizados o cancelados
            # en el dropdown, haciendo la UI más limpia.
            self.fields['proyecto'].queryset = user.proyectos_como_empleado.exclude(
                situacion__in=['FIN', 'CAN']
            )
            # ------------------------------------

    # === FIN DEL NUEVO MÉTODO ===
    class Meta:
        model = RegistroHoras
        fields = ['proyecto', 'fecha', 'horas', 'descripcion']
        widgets = {
            'proyecto': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'horas': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Introduce solo números enteros'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Descripción de la actividad realizada'
            }),
        }

    def clean(self):
        """
        Validaciones:
        - No se pueden registrar horas en proyectos finalizados o cancelados.
        - No se permiten fechas futuras.
        """
        cleaned_data = super().clean()
        proyecto = cleaned_data.get('proyecto')
        fecha = cleaned_data.get('fecha')

        # Validar estado del proyecto
        if proyecto and proyecto.situacion in ['FIN', 'CAN']:
            raise forms.ValidationError(
                f"No puedes registrar horas en un proyecto {proyecto.get_situacion_display().lower()}."
            )

        # Validar fecha futura, para proteccion del codigo.(ESTADO EN REVISION)
        from datetime import date
        if fecha and fecha > date.today():
            self.add_error('fecha', 'No puedes registrar horas en fechas futuras.')

        if proyecto and fecha:
            
            
            if fecha < proyecto.fecha_inicial:
                
                self.add_error('fecha', 
                    f"La fecha ({fecha.strftime('%d/%m/%Y')}) no puede ser anterior al inicio del proyecto "
                    f"({proyecto.fecha_inicial.strftime('%d/%m/%Y')})."
                )
            
            if proyecto.fecha_final and fecha > proyecto.fecha_final:
                self.add_error('fecha',
                    f"La fecha ({fecha.strftime('%d/%m/%Y')}) no puede ser posterior a la finalización del proyecto "
                    f"({proyecto.fecha_final.strftime('%d/%m/%Y')})."
                )
        
        return cleaned_data

    def clean_horas(self):
        """
        Validación: las horas deben ser mayores a 0.
        """
        horas = self.cleaned_data.get('horas')
        if horas is not None and horas <= 0:
            raise forms.ValidationError('Las horas deben ser mayores a 0.')
        return horas
    

class AsignarProyectoForm(forms.ModelForm):
    """
    Form para asignar un proyecto a un empleado (evita duplicar asignaciones activas).
    """
    def __init__(self, *args, **kwargs):
        empleado = kwargs.pop('empleado', None)
        super().__init__(*args, **kwargs)

        # Solo proyectos activos
        qs = Proyecto.objects.all()

        if empleado is not None:
            # Excluir los ya asignados activos
            qs = qs.exclude(asignaciones__empleado=empleado, asignaciones__activo=True)

        self.fields['proyecto'].queryset = qs.order_by('nombre')

    class Meta:
        model = AsignacionProyecto
        fields = ['proyecto', 'rol_en_proyecto']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
            'rol_en_proyecto': forms.Select(attrs={'class': 'form-control'}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'rfc', 'direccion', 'correo', 'telefono']
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EmpleadoForm(forms.ModelForm):
    # Definimos los campos que no están en PerfilEmpleado pero que necesitamos
    email = forms.EmailField(required=True, label="Correo Electrónico")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña Temporal")

    class Meta:
        model = PerfilEmpleado
        # Especificamos los campos del PerfilEmpleado que queremos en el formulario
        fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido']

    def save(self, commit=True):
        # Obtenemos los datos limpios del formulario
        primer_nombre = self.cleaned_data.get('primer_nombre')
        primer_apellido = self.cleaned_data.get('primer_apellido')

        # --- Lógica para generar el nombre de usuario ---
        if primer_nombre and primer_apellido:
            base_username = f"{primer_apellido.upper()}{primer_nombre[0].upper()}"
            username = base_username
            counter = 1
            # Nos aseguramos de que el username sea único
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
        else:
            # Si los campos están vacíos, genera un error (esto no debería pasar por las validaciones)
            raise ValueError("El primer nombre y el primer apellido son requeridos.")

        # --- Creación del User de Django ---
        user = User.objects.create_user(
            username=username,
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('password'),
            first_name=primer_nombre, # Guardamos el primer nombre en el campo por defecto de User
            last_name=primer_apellido, # y el primer apellido
        )

        # --- Creación y enlace del PerfilEmpleado ---
        perfil = super().save(commit=False)
        perfil.user = user # Enlazamos el perfil con el usuario recién creado
        if commit:
            perfil.save()
        return perfil
    
# === FORMULARIO DE CAMBIO DE CONTRASEÑA ===
class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario para que un usuario cambie su propia contraseña.
    Hereda de PasswordChangeForm y solo se personalizan los widgets
    para que coincidan con el estilo (ej. Bootstrap).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Añadimos la clase 'form-control' a todos los campos
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña actual'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nueva contraseña'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar nueva contraseña'})
        
        # Opcional: Cambiar las etiquetas (labels) si quieres
        self.fields['old_password'].label = "Contraseña actual"
        self.fields['new_password1'].label = "Nueva contraseña"
        self.fields['new_password2'].label = "Confirmación de nueva contraseña"

class ReporteFiltroForm(forms.Form):
    """
    Este formulario no guarda nada, solo captura las
    opciones del usuario para filtrar el reporte.
    """
    
    # Filtro 1: Por Cliente
    # (Si filtras por Cliente, los proyectos se autolimitarán en la vista)
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        required=False, # ¡Importante! Para permitir "Todos"
        label="Cliente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro 2: Por Proyecto
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.all(),
        required=False,
        label="Proyecto",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro 3: Por Usuario (Empleado)
    # Asumimos que los empleados son los que no son 'staff'
    empleado = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),
        required=False,
        label="Empleado",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro 4: Periodo de tiempo
    fecha_inicio = forms.DateField(
        required=False,
        label="Desde",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    fecha_fin = forms.DateField(
        required=False,
        label="Hasta",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        """
        Añadimos 'empty_label' para que la opción por defecto
        diga "Todos" en lugar de "---------"
        """
        super().__init__(*args, **kwargs)
        self.fields['cliente'].empty_label = "Todos los Clientes"
        self.fields['proyecto'].empty_label = "Todos los Proyectos"
        self.fields['empleado'].empty_label = "Todos los Empleados"