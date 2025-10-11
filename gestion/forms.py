from django import forms
from django.contrib.auth.models import User
from .models import Proyecto, RegistroHoras, AsignacionProyecto, Cliente


# === FORMULARIO DE PROYECTOS (SOLO ACCESO AL ADMINISTRADOR) ===
class ProyectoForm(forms.ModelForm):
    """
    Formulario para crear y editar proyectos.
    Solo lo usa el administrador.
    Incluye validaciones y campos estéticamente formateados.
    """
    class Meta:
        model = Proyecto
        fields = [
            'nombre',
            'descripcion',
            'fecha_inicial',
            'fecha_final',
            'cantidad_h',
            'situacion',
            'cliente',
            'administradores',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proyecto'
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Descripción breve del proyecto'
            }),
            'fecha_inicial': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'fecha_final': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'cantidad_h': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Horas presupuestadas'
            }),
            'situacion': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'administradores': forms.SelectMultiple(attrs={
                'class': 'form-control'
            }),
        }

    def clean(self):
        """
        Validación personalizada:
        - La fecha final no puede ser anterior a la inicial.
        - Las horas presupuestadas deben ser mayores a 0 si se proporcionan.
        """
        cleaned_data = super().clean()
        fecha_inicial = cleaned_data.get('fecha_inicial')
        fecha_final = cleaned_data.get('fecha_final')
        cantidad_h = cleaned_data.get('cantidad_h')

        if fecha_final and fecha_inicial and fecha_final < fecha_inicial:
            self.add_error('fecha_final', 'La fecha final no puede ser anterior a la inicial.')

        if cantidad_h is not None and cantidad_h <= 0:
            self.add_error('cantidad_h', 'Las horas presupuestadas deben ser mayores a 0.')

        return cleaned_data


# === FORMULARIO DE REGISTRO DE HORAS (SOLO PARA EMPLEADOS) ===
class RegistroHorasForm(forms.ModelForm):
    """
    Formulario para que los empleados registren sus horas trabajadas
    en un proyecto activo.
    Incluye validaciones para evitar errores comunes.
    """
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
                'placeholder': 'Ejemplo: 3.5'
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