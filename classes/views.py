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
    if request.user.is_teacher():
        tests = classroom.tests.all()
    else:
        from tests.models import TestAssignment
        tests = []
        for test in classroom.tests.filter(is_published=True):
            if test.assigned_to_all:
                tests.append(test)
            elif TestAssignment.objects.filter(test=test, student=request.user).exists():
                tests.append(test)
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

@login_required
def remove_student(request, classroom_pk, student_pk):
    classroom = get_object_or_404(Classroom, pk=classroom_pk, teacher=request.user)
    ClassMembership.objects.filter(classroom=classroom, student_id=student_pk).delete()
    return redirect('classroom_students', pk=classroom_pk)

@login_required
def classroom_students(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk, teacher=request.user)
    memberships = classroom.memberships.select_related('student')
    return render(request, 'classes/classroom_students.html', {
        'classroom': classroom,
        'memberships': memberships,
    })