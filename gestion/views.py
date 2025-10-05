from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 

def login_view(request):

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
    if request.user.is_staff:
        return render(request, 'gestion/admin_home.html')
    else:
        return render(request, 'gestion/empleado_home.html')
