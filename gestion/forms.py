# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Proyecto, RegistroHoras, AsignacionProyecto, Cliente, PerfilEmpleado


# === PROYECTOS ===
class ProyectoCreateForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'descripcion', 'fecha_inicial', 'fecha_final', 'cantidad_h', 'cliente', 'administradores']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicial': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_final': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cantidad_h': forms.NumberInput(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'administradores': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        fi = cleaned.get('fecha_inicial')
        ff = cleaned.get('fecha_final')
        if fi and ff and fi > ff:
            self.add_error('fecha_inicial', 'La fecha inicial no puede ser posterior a la fecha final.')
            self.add_error('fecha_final', 'La fecha final no puede ser anterior a la fecha inicial.')
        return cleaned


class ProyectoUpdateForm(ProyectoCreateForm):
    class Meta(ProyectoCreateForm.Meta):
        fields = ['nombre', 'descripcion', 'fecha_inicial', 'fecha_final', 'cantidad_h', 'situacion', 'cliente', 'administradores']


# === REGISTRO DE HORAS ===
class RegistroHorasForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.user = user
            qs = Proyecto.objects.filter(asignaciones__empleado=user, asignaciones__activo=True)
            qs = qs.exclude(situacion__in=['FIN', 'CAN']).distinct()
            self.fields['proyecto'].queryset = qs

    class Meta:
        model = RegistroHoras
        fields = ['proyecto', 'fecha', 'horas', 'descripcion']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'horas': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        proyecto = cleaned.get('proyecto')
        fecha = cleaned.get('fecha')
        if proyecto and proyecto.situacion in ['FIN', 'CAN']:
            raise forms.ValidationError('No puedes registrar horas en un proyecto no activo.')
        from datetime import date
        if fecha and fecha > date.today():
            self.add_error('fecha', 'No puedes registrar horas en fechas futuras.')
        if proyecto and fecha:
            if fecha < proyecto.fecha_inicial:
                inicio_str = proyecto.fecha_inicial.strftime('%d/%m/%Y')
                self.add_error('fecha', f'La fecha no puede ser anterior al inicio del proyecto ({inicio_str}).')
            if proyecto.fecha_final and fecha > proyecto.fecha_final:
                fin_str = proyecto.fecha_final.strftime('%d/%m/%Y')
                self.add_error('fecha', f'La fecha no puede ser posterior a la finalizacion del proyecto ({fin_str}).')
            if hasattr(self, 'user') and self.user:
                if not AsignacionProyecto.objects.filter(empleado=self.user, proyecto=proyecto, activo=True).exists():
                    self.add_error('proyecto', 'No tienes asignacion activa a este proyecto.')
        return cleaned

    def clean_horas(self):
        horas = self.cleaned_data.get('horas')
        if horas is not None and horas <= 0:
            raise forms.ValidationError('Las horas deben ser mayores a 0.')
        return horas


class AsignarProyectoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        empleado = kwargs.pop('empleado', None)
        super().__init__(*args, **kwargs)
        qs = Proyecto.objects.all()
        if empleado is not None:
            qs = qs.exclude(asignaciones__empleado=empleado, asignaciones__activo=True)
        self.fields['proyecto'].queryset = qs.order_by('nombre')

    class Meta:
        model = AsignacionProyecto
        fields = ['proyecto']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
        }


# === CLIENTE ===
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'rfc', 'direccion', 'correo', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'pattern': '\\d{10}', 'inputmode': 'numeric'}),
            'rfc': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '13', 'minlength': '12', 'pattern': '[A-Za-z&]{3,4}[0-9]{6}[A-Za-z0-9]{3}'})
        }

    def clean_rfc(self):
        import re
        raw = (self.cleaned_data.get('rfc') or '').strip()
        # eliminar espacios, guiones y cualquier caracter no permitido (solo A-Z, 0-9, &)
        rfc = re.sub(r"[^A-Za-z0-9&]", "", raw).upper()
        if not re.match(r'^[A-Z\&]{3,4}\d{6}[A-Z0-9]{3}$', rfc):
            raise forms.ValidationError('RFC invalido. Debe cumplir el formato oficial (12 o 13 caracteres).')
        qs = Cliente.objects.filter(rfc__iexact=rfc)
        if getattr(self, 'instance', None) and getattr(self.instance, 'pk', None):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un cliente con ese RFC.')
        return rfc

    def clean_telefono(self):
        tel = (self.cleaned_data.get('telefono') or '').strip()
        if tel and (not tel.isdigit() or len(tel) != 10):
            raise forms.ValidationError('El telefono debe tener 10 digitos.')
        return tel


# === EMPLEADOS ===
class EmpleadoForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Correo Electronico')
    password = forms.CharField(widget=forms.PasswordInput, label='Contrasena Temporal')

    class Meta:
        model = PerfilEmpleado
        fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido']

    def save(self, commit=True):
        primer_nombre = self.cleaned_data.get('primer_nombre')
        primer_apellido = self.cleaned_data.get('primer_apellido')
        if primer_nombre and primer_apellido:
            base_username = f"{primer_apellido.upper()}{primer_nombre[0].upper()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
        else:
            raise ValueError('El primer nombre y el primer apellido son requeridos.')

        user = User.objects.create_user(
            username=username,
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('password'),
            first_name=primer_nombre,
            last_name=primer_apellido,
        )

        perfil = super().save(commit=False)
        perfil.user = user
        if commit:
            perfil.save()
        return perfil


class EmpleadoUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Correo Electronico')
    primer_nombre = forms.CharField(max_length=150, required=True)
    segundo_nombre = forms.CharField(max_length=150, required=False)
    primer_apellido = forms.CharField(max_length=150, required=True)
    segundo_apellido = forms.CharField(max_length=150, required=False)

    class Meta:
        model = PerfilEmpleado
        fields = ['primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido']

    def __init__(self, *args, user_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'user', None):
            u = self.instance.user
            self.fields['email'].initial = u.email
            self.fields['primer_nombre'].initial = self.instance.primer_nombre
            self.fields['segundo_nombre'].initial = self.instance.segundo_nombre
            self.fields['primer_apellido'].initial = self.instance.primer_apellido
            self.fields['segundo_apellido'].initial = self.instance.segundo_apellido

    def save(self, commit=True):
        perfil = super().save(commit=False)
        user = perfil.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['primer_nombre']
        user.last_name = self.cleaned_data['primer_apellido']
        if commit:
            user.save()
            perfil.save()
        return perfil


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario para que un usuario cambie su propia contraseña.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Estilos (esto ya lo tenías)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña actual'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nueva contraseña'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar nueva contraseña'})
        
        # Etiquetas (labels) con 'ñ' (tu cambio, que es correcto)
        self.fields['old_password'].label = 'Contraseña actual'
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Confirmación de nueva contraseña'


class ReporteFiltroForm(forms.Form):
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), required=False, label='Cliente', widget=forms.Select(attrs={'class': 'form-control'}))
    proyecto = forms.ModelChoiceField(queryset=Proyecto.objects.all(), required=False, label='Proyecto', widget=forms.Select(attrs={'class': 'form-control'}))
    empleado = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=False), required=False, label='Empleado', widget=forms.Select(attrs={'class': 'form-control'}))
    fecha_inicio = forms.DateField(required=False, label='Desde', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    fecha_fin = forms.DateField(required=False, label='Hasta', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].empty_label = 'Todos los Clientes'
        self.fields['proyecto'].empty_label = 'Todos los Proyectos'
        self.fields['empleado'].empty_label = 'Todos los Empleados'
