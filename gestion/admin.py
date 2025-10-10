from django.contrib import admin
from .models import Cliente, Proyecto, RegistroHoras, Actividad, AsignacionProyecto

# === MODELOS BASE ===
admin.site.register(Cliente)
admin.site.register(Proyecto)
admin.site.register(RegistroHoras)
admin.site.register(Actividad)

# === ADMIN PERSONALIZADO PARA ASIGNACIONES ===
@admin.register(AsignacionProyecto)
class AsignacionProyectoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'proyecto', 'rol_en_proyecto', 'activo', 'fecha_asignacion', 'fecha_baja')
    list_filter = ('activo', 'rol_en_proyecto', 'proyecto')
    search_fields = ('empleado__username', 'proyecto__nombre')
