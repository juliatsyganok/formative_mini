from django import forms
from .models import Classroom

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name']

class JoinClassroomForm(forms.Form):
    token = forms.CharField(max_length=8, label='Токен класса')