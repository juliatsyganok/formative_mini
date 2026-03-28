from django.contrib import admin
from .models import Classroom, ClassMembership

admin.site.register(Classroom)
admin.site.register(ClassMembership)