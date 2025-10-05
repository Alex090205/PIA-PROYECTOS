from django.contrib import admin
from .models import Cliente, Proyecto, RegistroHoras

# Register your models here.

admin.site.register(Cliente)
admin.site.register(Proyecto)
admin.site.register(RegistroHoras)
