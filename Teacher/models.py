from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class TeacherSignup(models.Model):
    QUALIFICATION_CHOICES = [
        ('phd', 'PhD'),
        ('masters', 'Masters Degree'),
        ('bachelors', 'Bachelors Degree'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    qualification = models.CharField(max_length=50, choices=QUALIFICATION_CHOICES)
    coaching_institute_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    teacher = models.ForeignKey(TeacherSignup, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Shell(models.Model):
    LECTURE_TYPE_CHOICES = [
        ('demo', 'Demo Lecture'),
        ('paid', 'Paid Lecture'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='shells')
    shell_number = models.IntegerField()
    description = models.TextField()
    video_link = models.URLField(max_length=500, blank=True, null=True)
    video_file = models.FileField(upload_to='shell_videos/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='shell_pdfs/', blank=True, null=True)
    cloudinary_public_id = models.CharField(max_length=100, blank=True, null=True)
    lecture_type = models.CharField(max_length=10, choices=LECTURE_TYPE_CHOICES, default='paid')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shell {self.shell_number} - {self.course.name}"

class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(TeacherSignup, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CourseContent(models.Model):
    CONTENT_TYPES = (
        ('video', 'Video'),
        ('pdf', 'PDF'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contents')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='course_content/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.name} - {self.content_type} - {self.title}"
