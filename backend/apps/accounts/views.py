from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User


def home(request):
    """Home page - only shows login link"""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return render(request, 'home.html')


def role_login(request):
    """Login page - redirects to role-based dashboard after login"""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Role-based redirect
            if user.is_superuser:
                return redirect('/admin-dashboard/')
            elif user.user_type == 'lecturer':
                return redirect('/lecturer/dashboard/')
            else:
                return redirect('/student/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')


@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.is_superuser:
        return redirect('/admin-dashboard/')
    elif request.user.user_type == 'lecturer':
        return redirect('/lecturer/dashboard/')
    else:
        return redirect('/student/dashboard/')


def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('/login/')


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({'status': 'ok', 'service': 'attendance-system'})
