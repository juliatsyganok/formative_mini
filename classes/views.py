from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Classroom, ClassMembership
from .forms import ClassroomForm, JoinClassroomForm

@login_required
def teacher_dashboard(request):
    classrooms = Classroom.objects.filter(teacher=request.user)
    form = ClassroomForm(request.POST or None)
    if form.is_valid():
        classroom = form.save(commit=False)
        classroom.teacher = request.user
        classroom.save()
        return redirect('teacher_dashboard')
    return render(request, 'classes/teacher_dashboard.html', {'classrooms': classrooms, 'form': form})

@login_required
def student_dashboard(request):
    memberships = ClassMembership.objects.filter(student=request.user).select_related('classroom')
    return render(request, 'classes/student_dashboard.html', {'memberships': memberships})

@login_required
def classroom_detail(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    tests = classroom.tests.filter(is_published=True) if request.user.is_student() else classroom.tests.all()
    return render(request, 'classes/classroom_detail.html', {'classroom': classroom, 'tests': tests})

@login_required
def create_classroom(request):
    return redirect('teacher_dashboard')

@login_required
def join_classroom(request):
    form = JoinClassroomForm(request.POST or None)
    if form.is_valid():
        token = form.cleaned_data['token'].upper()
        classroom = get_object_or_404(Classroom, token=token)
        ClassMembership.objects.get_or_create(student=request.user, classroom=classroom)
        return redirect('classroom_detail', pk=classroom.pk)
    return render(request, 'classes/join_classroom.html', {'form': form})