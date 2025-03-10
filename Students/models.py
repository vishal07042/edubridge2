from django.db import models
from django.contrib.auth.models import User
from Teacher.models import Course

# Create your models here.

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=0)  # Store progress as percentage
    last_accessed = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    completed_lectures = models.TextField(default='')  # Store completed lecture numbers as comma-separated string

    class Meta:
        unique_together = ['student', 'course']  # Prevent duplicate enrollments

    def __str__(self):
        return f"{self.student.user.username} - {self.course.name}"
