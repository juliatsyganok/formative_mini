from django.contrib import admin
from .models import Test, Question, AnswerChoice, TestSession, StudentAnswer

admin.site.register(Test)
admin.site.register(Question)
admin.site.register(AnswerChoice)
admin.site.register(TestSession)
admin.site.register(StudentAnswer)