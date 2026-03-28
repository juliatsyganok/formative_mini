from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('classroom/create/', views.create_classroom, name='create_classroom'),
    path('classroom/<int:pk>/', views.classroom_detail, name='classroom_detail'),
    path('classroom/join/', views.join_classroom, name='join_classroom'),
]