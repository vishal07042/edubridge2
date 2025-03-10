from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('n', views.index, name='index'),
    path('', views.teacher_index, name='teacher_index'),
    path('student/', views.student_index, name='student_index'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/signup/', views.teacher_signup, name='teacher_signup'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/create-course/', views.create_course, name='create_course'),
    path('teacher/edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('teacher/delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('teacher/course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('teacher/course/<int:course_id>/create-shell/', views.create_shell, name='create_shell'),
    path('teacher/course/<int:course_id>/edit-shell/<int:shell_id>/', views.edit_shell, name='edit_shell'),
    path('teacher/course/<int:course_id>/delete-shell/<int:shell_id>/', views.delete_shell, name='delete_shell'),
    path('teacher/course/<int:course_id>/shell/<int:shell_id>/', views.shell_detail, name='shell_detail'),
    path('teacher/course/<int:course_id>/shell/<int:shell_id>/upload-video/', views.upload_video, name='upload_video'),
    path('teacher/course/<int:course_id>/shell/<int:shell_id>/upload-pdf/', views.upload_pdf, name='upload_pdf'),
    path('teacher/course/<int:course_id>/shell/<int:shell_id>/upload-video-page/', views.upload_video_page, name='upload_video_page'),
    path('teacher/course/<int:course_id>/shell/<int:shell_id>/save-video-url/', views.save_video_url, name='save_video_url'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
    path('features/', views.features, name='features'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('teacher/add-student/', views.add_student, name='add_student'),
    path('teacher/add-student/page/', views.add_student_page, name='add_student_page'),
    path('teacher/remove-student/<int:student_id>/', views.remove_student, name='remove_student'),
    path('courses/', views.course_listing, name='course_listing'),
    path('teacher/students/', views.student_management, name='student_management'),
    path('teacher/settings/', views.settings, name='settings'),
    path('teacher/analytics/', views.analytics, name='analytics'),
    path('teacher/doubt/', views.doubt, name='doubt'),
    path('teacher/all-courses/', views.all_courses, name='all_courses'),
    path('course/<int:course_id>/', views.course_demo, name='course_demo'),
]
  