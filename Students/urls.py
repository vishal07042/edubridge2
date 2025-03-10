from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_index, name='student_index'),
    path('login/', views.student_login, name='student_login'),
    path('signup/', views.student_signup, name='student_signup'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.student_logout, name='student_logout'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/payment/', views.payment, name='payment'),
    path('course/<int:course_id>/process-payment/', views.process_payment, name='process_payment'),
    path('course/<int:course_id>/learn/', views.course_learning, name='course_learning'),
    path('course/<int:course_id>/learn/<int:shell_number>/', views.course_learning, name='course_learning'),
    path('contact/', views.contact, name='contact'),
]