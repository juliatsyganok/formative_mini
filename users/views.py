from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm

def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('choose_role')
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def choose_role_view(request):
    if request.user.role:
        return redirect('dashboard')
    if request.method == 'POST':
        role = request.POST.get('role')
        if role in ['teacher', 'student']:
            request.user.role = role
            request.user.save()
            return redirect('dashboard')
    return render(request, 'users/choose_role.html')

@login_required
def dashboard_view(request):
    if not request.user.role:
        return redirect('choose_role')
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    return redirect('student_dashboard')