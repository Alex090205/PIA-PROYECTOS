from django.urls import path
from . import views

urlpatterns = [
    # Cuando alguien visite '.../login/', se mostrará la vista 'login_view'
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
]