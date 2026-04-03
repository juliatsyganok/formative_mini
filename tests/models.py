from django.db import models
from django.conf import settings
from classes.models import Classroom

class Test(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='tests')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Минуты. Пусто = без ограничения')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='created_tests')
    assigned_to_all = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    TYPE_CHOICES = [
        ('single', 'Один вариант'),
        ('multiple', 'Несколько вариантов'),
        ('short', 'Короткий ответ'),
        ('long', 'Развёрнутый ответ'),
        ('file', 'Загрузка файла'),
    ]
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    text = models.TextField()
    image = models.ImageField(upload_to='questions/', null=True, blank=True)
    attachment = models.FileField(upload_to='question_files/', null=True, blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    correct_short_answer = models.TextField(blank=True, help_text='Для короткого ответа — эталон (через | если вариантов несколько)')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.test.title} — вопрос {self.order}'

class AnswerChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class TestSession(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'test')

    @property
    def is_submitted(self):
        return self.submitted_at is not None

class StudentAnswer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True)
    selected_choices = models.ManyToManyField(AnswerChoice, blank=True)
    file_answer = models.FileField(upload_to='student_files/', null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('session', 'question')

class TestAssignment(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments')

    class Meta:
        unique_together = ('test', 'student')