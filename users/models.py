from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [('teacher', 'Учитель'), ('student', 'Ученик')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, blank=True)

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'