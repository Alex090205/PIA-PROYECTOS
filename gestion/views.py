# gestion/views.py - VERSIÓN CORREGIDA
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse # ¡No olvides importar HttpResponse!

def login(request):

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'gestion/login.html', {'form': form})

@login_required
def home(request):
    # ESTA ES LA FUNCIÓN CORREGIDA
    # Ahora solo devuelve un mensaje simple y no busca ninguna plantilla.
    return HttpResponse(f"<h1>¡Login Exitoso!</h1><p>Bienvenido, {request.user.username}.</p>")
