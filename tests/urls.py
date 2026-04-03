from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:classroom_pk>/', views.create_test, name='create_test'),
    path('<int:pk>/', views.test_detail, name='test_detail'),
    path('<int:pk>/edit/', views.edit_test, name='edit_test'),
    path('<int:pk>/take/', views.take_test, name='take_test'),
    path('<int:pk>/submit/', views.submit_test, name='submit_test'),
    path('<int:pk>/results/', views.test_results, name='test_results'),
    path('<int:pk>/stats/', views.test_stats, name='test_stats'),
    path('<int:test_pk>/question/add/', views.add_question, name='add_question'),
    path('question/<int:pk>/delete/', views.delete_question, name='delete_question'),
    path('question/<int:pk>/edit/', views.edit_question, name='edit_question'),
    path('<int:pk>/save/', views.save_progress, name='save_progress'),
    path('<int:pk>/assign/', views.assign_test, name='assign_test'),
]