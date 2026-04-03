from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Test, Question, AnswerChoice, TestSession, StudentAnswer
from classes.models import Classroom

@login_required
def create_test(request, classroom_pk):
    classroom = get_object_or_404(Classroom, pk=classroom_pk)
    if request.method == 'POST':
        test = Test.objects.create(
            classroom=classroom,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            time_limit=request.POST.get('time_limit') or None,
            created_by=request.user,
        )
        return redirect('edit_test', pk=test.pk)
    return render(request, 'tests/create_test.html', {'classroom': classroom})

@login_required
def test_detail(request, pk):
    test = get_object_or_404(Test, pk=pk)
    return render(request, 'tests/test_detail.html', {'test': test})

@login_required
def take_test(request, pk):
    test = get_object_or_404(Test, pk=pk)
    session, _ = TestSession.objects.get_or_create(student=request.user, test=test)
    if session.is_submitted:
        return redirect('test_results', pk=pk)
    questions = test.questions.prefetch_related('choices')

    # собираем сохранённые ответы в удобный словарь
    existing_answers = {}
    for answer in session.answers.prefetch_related('selected_choices'):
        existing_answers[answer.question_id] = {
            'text': answer.text_answer,
            'selected_ids': list(answer.selected_choices.values_list('id', flat=True)),
        }

    return render(request, 'tests/take_test.html', {
        'test': test,
        'session': session,
        'questions': questions,
        'existing_answers': existing_answers,
    })

@login_required
def submit_test(request, pk):
    test = get_object_or_404(Test, pk=pk)
    session = get_object_or_404(TestSession, student=request.user, test=test)
    if session.is_submitted:
        return redirect('test_results', pk=pk)

    total_points = 0
    earned_points = 0

    for question in test.questions.all():
        total_points += question.points
        answer, _ = StudentAnswer.objects.get_or_create(session=session, question=question)

        if question.question_type == 'single':
            choice_id = request.POST.get(f'q_{question.id}')
            if choice_id:
                choice = AnswerChoice.objects.get(pk=choice_id)
                answer.selected_choices.set([choice])
                if choice.is_correct:
                    answer.is_correct = True
                    answer.points_earned = question.points
                    earned_points += question.points
                else:
                    answer.is_correct = False
                    answer.points_earned = 0

        elif question.question_type == 'multiple':
            choice_ids = request.POST.getlist(f'q_{question.id}')
            if choice_ids:
                choices = AnswerChoice.objects.filter(pk__in=choice_ids)
                answer.selected_choices.set(choices)
                correct_ids = set(question.choices.filter(is_correct=True).values_list('id', flat=True))
                selected_ids = set(int(i) for i in choice_ids)
                if correct_ids == selected_ids:
                    answer.is_correct = True
                    answer.points_earned = question.points
                    earned_points += question.points
                else:
                    answer.is_correct = False
                    answer.points_earned = 0

        elif question.question_type == 'short':
            text = request.POST.get(f'q_{question.id}', '').strip()
            answer.text_answer = text
            correct_variants = [v.strip().lower() for v in question.correct_short_answer.split('|')]
            if text.lower() in correct_variants:
                answer.is_correct = True
                answer.points_earned = question.points
                earned_points += question.points
            else:
                answer.is_correct = False
                answer.points_earned = 0

        elif question.question_type in ['long']:
            answer.text_answer = request.POST.get(f'q_{question.id}', '')
            answer.is_correct = None
            answer.points_earned = None

        elif question.question_type == 'file':
            if f'q_{question.id}' in request.FILES:
                answer.file_answer = request.FILES[f'q_{question.id}']
            answer.is_correct = None
            answer.points_earned = None

        answer.save()

    session.submitted_at = timezone.now()
    session.score = earned_points
    session.save()
    return redirect('test_results', pk=pk)

@login_required
def test_results(request, pk):
    test = get_object_or_404(Test, pk=pk)
    session = get_object_or_404(TestSession, student=request.user, test=test)
    answers = session.answers.select_related('question').prefetch_related('selected_choices')
    total_points = sum(q.points for q in test.questions.all())
    return render(request, 'tests/test_results.html', {
        'test': test, 'session': session, 'answers': answers, 'total_points': total_points
    })

@login_required
def test_stats(request, pk):
    test = get_object_or_404(Test, pk=pk)
    sessions = TestSession.objects.filter(
        test=test, submitted_at__isnull=False
    ).select_related('student').prefetch_related('answers__question', 'answers__selected_choices')
    questions = test.questions.prefetch_related('choices')
    total_points = sum(q.points for q in questions)
    stats = []
    for question in questions:
        q_answers = StudentAnswer.objects.filter(question=question, session__submitted_at__isnull=False)
        correct_count = q_answers.filter(is_correct=True).count()
        total_count = q_answers.count()
        stats.append({
            'question': question,
            'correct_count': correct_count,
            'total_count': total_count,
            'percent': round(correct_count / total_count * 100) if total_count else 0
        })
    return render(request, 'tests/test_stats.html', {
        'test': test, 'sessions': sessions, 'stats': stats, 'total_points': total_points
    })

@login_required
def edit_test(request, pk):
    test = get_object_or_404(Test, pk=pk)
    questions = test.questions.prefetch_related('choices')
    if request.method == 'POST':
        test.title = request.POST.get('title', test.title)
        test.description = request.POST.get('description', test.description)
        test.time_limit = request.POST.get('time_limit') or None
        test.is_published = request.POST.get('is_published') == 'on'
        test.save()
        return redirect('edit_test', pk=pk)
    return render(request, 'tests/edit_test.html', {'test': test, 'questions': questions})

@login_required
def add_question(request, test_pk):
    test = get_object_or_404(Test, pk=test_pk)
    if request.method == 'POST':
        q_type = request.POST.get('question_type')
        question = Question.objects.create(
            test=test,
            question_type=q_type,
            text=request.POST.get('text'),
            points=request.POST.get('points', 1),
            order=test.questions.count() + 1,
            correct_short_answer=request.POST.get('correct_short_answer', ''),
        )
        if request.FILES.get('image'):
            question.image = request.FILES['image']
        if request.FILES.get('attachment'):
            question.attachment = request.FILES['attachment']
        question.save()

        # сохраняем варианты ответов
        if q_type in ['single', 'multiple']:
            choices = request.POST.getlist('choice_text')
            correct = request.POST.getlist('choice_correct')
            for i, text in enumerate(choices):
                if text.strip():
                    AnswerChoice.objects.create(
                        question=question,
                        text=text.strip(),
                        is_correct=str(i) in correct
                    )
    return redirect('edit_test', pk=test_pk)

@login_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    test_pk = question.test.pk
    question.delete()
    return redirect('edit_test', pk=test_pk)

@login_required
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.text = request.POST.get('text')
        question.points = request.POST.get('points', 1)
        question.correct_short_answer = request.POST.get('correct_short_answer', '')
        if request.FILES.get('image'):
            question.image = request.FILES['image']
        if request.FILES.get('attachment'):
            question.attachment = request.FILES['attachment']
        question.save()

        # обновляем варианты если это single/multiple
        if question.question_type in ['single', 'multiple']:
            question.choices.all().delete()
            choices = request.POST.getlist('choice_text')
            correct = request.POST.getlist('choice_correct')
            for i, text in enumerate(choices):
                if text.strip():
                    AnswerChoice.objects.create(
                        question=question,
                        text=text.strip(),
                        is_correct=str(i) in correct
                    )
        return redirect('edit_test', pk=question.test.pk)
    return render(request, 'tests/edit_question.html', {'question': question})

@login_required
def save_progress(request, pk):
    test = get_object_or_404(Test, pk=pk)
    session, _ = TestSession.objects.get_or_create(student=request.user, test=test)
    if session.is_submitted:
        return redirect('test_results', pk=pk)

    for question in test.questions.all():
        answer, _ = StudentAnswer.objects.get_or_create(session=session, question=question)

        if question.question_type == 'single':
            choice_id = request.POST.get(f'q_{question.id}')
            if choice_id:
                choice = AnswerChoice.objects.get(pk=choice_id)
                answer.selected_choices.set([choice])

        elif question.question_type == 'multiple':
            choice_ids = request.POST.getlist(f'q_{question.id}')
            if choice_ids:
                choices = AnswerChoice.objects.filter(pk__in=choice_ids)
                answer.selected_choices.set(choices)

        elif question.question_type in ['short', 'long']:
            text = request.POST.get(f'q_{question.id}', '')
            if text:
                answer.text_answer = text

        elif question.question_type == 'file':
            if f'q_{question.id}' in request.FILES:
                answer.file_answer = request.FILES[f'q_{question.id}']

        answer.save()

    return redirect('take_test', pk=pk)


@login_required
def assign_test(request, pk):
    test = get_object_or_404(Test, pk=pk)
    classroom = test.classroom
    memberships = classroom.memberships.select_related('student')

    if request.method == 'POST':
        assign_to = request.POST.get('assign_to')
        test.is_published = True

        if assign_to == 'all':
            test.assigned_to_all = True
            test.assignments.all().delete()
        else:
            test.assigned_to_all = False
            test.assignments.all().delete()
            student_ids = request.POST.getlist('students')
            from .models import TestAssignment
            for sid in student_ids:
                TestAssignment.objects.get_or_create(test=test, student_id=sid)

        test.save()
        return redirect('classroom_detail', pk=classroom.pk)

    return render(request, 'tests/assign_test.html', {
        'test': test,
        'classroom': classroom,
        'memberships': memberships,
    })

@login_required
def all_tests(request):
    tests = Test.objects.filter(created_by=request.user)
    return render(request, 'tests/all_tests.html', {'tests': tests})

@login_required
def create_test_standalone(request):
    if request.method == 'POST':
        test = Test.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            time_limit=request.POST.get('time_limit') or None,
            created_by=request.user,
        )
        return redirect('edit_test', pk=test.pk)
    return render(request, 'tests/create_test_standalone.html')

@login_required
def add_test_to_class(request, pk):
    test = get_object_or_404(Test, pk=pk)
    classrooms = Classroom.objects.filter(teacher=request.user)
    if request.method == 'POST':
        classroom_id = request.POST.get('classroom_id')
        classroom = get_object_or_404(Classroom, pk=classroom_id, teacher=request.user)
        test.classroom = classroom
        test.save()
        return redirect('assign_test', pk=test.pk)
    return render(request, 'tests/add_to_class.html', {'test': test, 'classrooms': classrooms})