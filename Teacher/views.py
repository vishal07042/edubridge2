from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import TeacherSignup, Course, Shell, Student, CourseContent
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
import os
from django.http import JsonResponse
import json
from django.db import models
from django.db.models import Count
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'Teacher/index.html')

def teacher_index(request):
    return render(request, 'Teacher/teacher_index.html')

def student_index(request):
    return render(request, 'Teacher/student_index.html')

@login_required
def teacher_dashboard(request):
    try:
        teacher = request.user.teacher
        # Get courses with correct student count and lecture count
        courses = Course.objects.filter(teacher=teacher).prefetch_related('student_set', 'shells')
        
        # Manually calculate counts for each course
        for course in courses:
            course.student_count = course.student_set.count()
            course.lecture_count = course.shells.count()
        
        # Get total counts
        total_students = Student.objects.filter(course__teacher=teacher).count()
        total_courses = courses.count()
        
        # Count total videos (shells that have either video_file or video_link)
        total_videos = Shell.objects.filter(
            course__teacher=teacher
        ).filter(
            models.Q(video_file__isnull=False, video_file__gt='') |
            models.Q(video_link__isnull=False, video_link__gt='')
        ).count()
        
        # Count total PDFs (only count shells that have PDF files)
        total_pdfs = Shell.objects.filter(
            course__teacher=teacher,
            pdf_file__isnull=False
        ).exclude(pdf_file='').count()

        context = {
            'courses': courses,
            'total_courses': total_courses,
            'total_students': total_students,
            'total_videos': total_videos,
            'total_pdfs': total_pdfs,
        }
        return render(request, 'Teacher/teacher_dashboard.html', context)
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please complete your registration.')
        return redirect('teacher_signup')

@login_required
def course_detail(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        shells = Shell.objects.filter(course=course).order_by('shell_number')
        return render(request, 'Teacher/course_detail.html', {
            'course': course,
            'shells': shells
        })
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please log in again.')
        return redirect('teacher_login')

@login_required
def shell_detail(request, course_id, shell_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        shell = get_object_or_404(Shell, id=shell_id, course=course)
        return render(request, 'Teacher/shell_detail.html', {
            'course': course,
            'shell': shell
        })
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please log in again.')
        return redirect('teacher_login')

@login_required
@require_POST
def upload_video(request, course_id, shell_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        shell = get_object_or_404(Shell, id=shell_id, course=course)
        
        if 'video_file' in request.FILES:
            # Delete old video file if it exists
            if shell.video_file:
                if os.path.isfile(shell.video_file.path):
                    os.remove(shell.video_file.path)
            
            # Save new video file
            shell.video_file = request.FILES['video_file']
            shell.save()
            messages.success(request, 'Video uploaded successfully!')
        else:
            messages.error(request, 'No video file selected.')
    except Exception as e:
        messages.error(request, f'Error uploading video: {str(e)}')
    
    return redirect('shell_detail', course_id=course_id, shell_id=shell_id)

@login_required
@require_POST
def upload_pdf(request, course_id, shell_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        shell = get_object_or_404(Shell, id=shell_id, course=course)
        
        if 'pdf_file' in request.FILES:
            # Delete old PDF file if it exists
            if shell.pdf_file:
                if os.path.isfile(shell.pdf_file.path):
                    os.remove(shell.pdf_file.path)
            
            # Save new PDF file
            shell.pdf_file = request.FILES['pdf_file']
            shell.save()
            messages.success(request, 'PDF uploaded successfully!')
        else:
            messages.error(request, 'No PDF file selected.')
    except Exception as e:
        messages.error(request, f'Error uploading PDF: {str(e)}')
    
    return redirect('shell_detail', course_id=course_id, shell_id=shell_id)

@login_required
@require_POST
def create_shell(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        description = request.POST.get('description')
        video_link = request.POST.get('video_link')
        
        # Get the next shell number
        last_shell = Shell.objects.filter(course=course).order_by('-shell_number').first()
        next_shell_number = 1 if not last_shell else last_shell.shell_number + 1
        
        # Create the new shell
        Shell.objects.create(
            course=course,
            shell_number=next_shell_number,
            description=description,
            video_link=video_link
        )
        
        messages.success(request, f'Shell {next_shell_number} created successfully!')
    except Exception as e:
        messages.error(request, f'Error creating shell: {str(e)}')
    
    return redirect('course_detail', course_id=course_id)

@login_required
def edit_shell(request, course_id, shell_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        shell = get_object_or_404(Shell, id=shell_id, course=course)
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please log in again.')
        return redirect('teacher_login')

    if request.method == 'POST':
        try:
            shell.description = request.POST.get('description')
            shell.video_link = request.POST.get('video_link')
            shell.save()
            messages.success(request, f'Shell {shell.shell_number} updated successfully!')
            return redirect('course_detail', course_id=course_id)
        except Exception as e:
            messages.error(request, f'Error updating shell: {str(e)}')
    
    return render(request, 'Teacher/edit_shell.html', {'course': course, 'shell': shell})

@login_required
@require_POST
def delete_shell(request, course_id, shell_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        shell = get_object_or_404(Shell, id=shell_id, course=course)
        
        # Delete associated files
        if shell.video_file:
            if os.path.isfile(shell.video_file.path):
                os.remove(shell.video_file.path)
        if shell.pdf_file:
            if os.path.isfile(shell.pdf_file.path):
                os.remove(shell.pdf_file.path)
        
        shell.delete()
        messages.success(request, f'Shell {shell.shell_number} deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting shell: {str(e)}')
    
    return redirect('course_detail', course_id=course_id)

@login_required
def create_course(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')

        try:
            # Create course
            course = Course.objects.create(
                teacher=request.user.teacher,
                name=name,
                description=description,
                price=price
            )

            messages.success(request, 'Course created successfully!')
            return redirect('teacher_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating course: {str(e)}')
            return redirect('teacher_dashboard')

    return redirect('teacher_dashboard')

@login_required
def edit_course(request, course_id):
    try:
        course = get_object_or_404(Course, id=course_id, teacher=request.user.teacher)
        
        if request.method == 'POST':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            price = request.POST.get('price')

            # Validate required fields
            if not all([name, description, price]):
                messages.error(request, 'All fields are required.')
                return redirect('teacher_dashboard')

            try:
                # Validate price
                price = float(price)
                if price < 0:
                    messages.error(request, 'Price cannot be negative.')
                    return redirect('teacher_dashboard')

                # Update course
                course.name = name
                course.description = description
                course.price = price
                course.save()
                
                messages.success(request, f'Course "{name}" updated successfully!')
            except ValueError:
                messages.error(request, 'Invalid price value.')
            except Exception as e:
                messages.error(request, f'Error updating course: {str(e)}')
            
            return redirect('teacher_dashboard')

    except Course.DoesNotExist:
        messages.error(request, 'Course not found.')
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please log in again.')
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
    
    return redirect('teacher_dashboard')

@login_required
@require_POST
def delete_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id, teacher=request.user.teacher)
        course.delete()
        messages.success(request, 'Course deleted successfully!')
    except Course.DoesNotExist:
        messages.error(request, 'Course not found.')
    except Exception as e:
        messages.error(request, f'Error deleting course: {str(e)}')
    return redirect('teacher_dashboard')

def teacher_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user is a teacher
            try:
                teacher = user.teacher
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('teacher_dashboard')
            except TeacherSignup.DoesNotExist:
                messages.error(request, 'This account is not registered as a teacher.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'Teacher/teacher_login.html')

def teacher_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        qualification = request.POST.get('qualification')
        coaching_institute_name = request.POST.get('coaching_institute_name')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'Teacher/teacher_signup.html')

        try:
            with transaction.atomic():
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'This username is already taken. Please choose another one.')
                    return render(request, 'Teacher/teacher_signup.html')

                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'This email is already registered. Please use another email or login.')
                    return render(request, 'Teacher/teacher_signup.html')

                # Create User instance
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )

                # Create TeacherSignup instance
                teacher = TeacherSignup.objects.create(
                    user=user,
                    name=name,
                    email=email,
                    phone_number=phone_number,
                    qualification=qualification,
                    coaching_institute_name=coaching_institute_name
                )

                messages.success(request, 'Registration successful! Please login with your credentials.')
                return redirect('teacher_login')

        except IntegrityError as e:
            messages.error(request, 'This username or email is already taken. Please choose another one.')
            return render(request, 'Teacher/teacher_signup.html')
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
            return render(request, 'Teacher/teacher_signup.html')

    return render(request, 'Teacher/teacher_signup.html')

@login_required
def upload_video_page(request, course_id, shell_id):
    """Display the Cloudinary video upload page"""
    course = get_object_or_404(Course, id=course_id, teacher__user=request.user)
    shell = get_object_or_404(Shell, id=shell_id, course=course)
    return render(request, 'Teacher/upload_video.html', {
        'course': course,
        'shell': shell
    })

@login_required
@require_POST
def save_video_url(request, course_id, shell_id):
    """Save the Cloudinary video URL and lecture type to the shell"""
    try:
        course = get_object_or_404(Course, id=course_id, teacher__user=request.user)
        shell = get_object_or_404(Shell, id=shell_id, course=course)
        
        data = json.loads(request.body)
        video_url = data.get('video_url')
        public_id = data.get('public_id')
        lecture_type = data.get('lecture_type', 'paid')  # Default to paid if not specified
        
        if video_url:
            shell.video_link = video_url
            if public_id:
                shell.cloudinary_public_id = public_id
            shell.lecture_type = lecture_type
            shell.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'No video URL provided'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def features(request):
    """Display the features page"""
    return render(request, 'Teacher/features.html')

def about(request):
    """Display the about page"""
    return render(request, 'Teacher/about.html')

def contact(request):
    """Handle contact form submission and display contact page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Send confirmation email to the user
        confirmation_subject = "Thank you for contacting EduBridge"
        confirmation_message = f"""
Dear {name},

Thank you for reaching out to EduBridge! We have received your message and will get back to you as soon as possible.

Here's a copy of your message:
Subject: {subject}
Message:
{message}

Best regards,
The EduBridge Team
"""
        try:
            from django.conf import settings as django_settings
            # Send confirmation email to user
            send_mail(
                confirmation_subject,
                confirmation_message,
                django_settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            # Send notification email to admin
            admin_subject = f"New Contact Form Submission: {subject}"
            admin_message = f"""
New contact form submission from {name}

Email: {email}
Subject: {subject}
Message:
{message}
"""
            send_mail(
                admin_subject,
                admin_message,
                django_settings.DEFAULT_FROM_EMAIL,
                [django_settings.ADMIN_EMAIL],
                fail_silently=False,
            )

            messages.success(request, 'Thank you for your message! We have sent you a confirmation email.')
            return redirect('contact')
            
        except Exception as e:
            # Log the error for debugging
            logger.error(f"Email sending failed: {str(e)}")
            
            # Show detailed error in debug mode, generic message in production
            error_message = str(e) if django_settings.DEBUG else 'Sorry, there was an error sending your message. Please try again later.'
            messages.error(request, error_message)
            
            # Return to the form with the submitted data intact
            context = {
                'form_data': {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message
                }
            }
            return render(request, 'Teacher/contact.html', context)

    return render(request, 'Teacher/contact.html')

@login_required
def add_student(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        course_id = request.POST.get('course')

        try:
            teacher = request.user.teacher
            course = Course.objects.get(id=course_id, teacher=teacher)
            student = Student.objects.create(
                name=name,
                email=email,
                phone=phone,
                course=course,
                teacher=teacher
            )
            messages.success(request, 'Student added successfully!')
        except Course.DoesNotExist:
            messages.error(request, 'Course not found.')
        except Exception as e:
            messages.error(request, f'Error adding student: {str(e)}')

    return redirect('student_management')

@login_required
def remove_student(request, student_id):
    if request.method == 'POST':
        try:
            student = get_object_or_404(Student, id=student_id, teacher=request.user.teacher)
            student.delete()
            messages.success(request, 'Student removed successfully!')
        except Exception as e:
            messages.error(request, f'Error removing student: {str(e)}')
    return redirect('teacher_dashboard')

@login_required
def add_student_page(request):
    """Display the add student page"""
    try:
        courses = Course.objects.filter(teacher=request.user.teacher).order_by('-created_at')
        return render(request, 'Teacher/add_student.html', {
            'courses': courses
        })
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please log in again.')
        return redirect('teacher_login')

def course_listing(request):
    """Display all courses with search and filter functionality"""
    courses = Course.objects.all().order_by('-created_at')
    teachers = TeacherSignup.objects.all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            models.Q(name__icontains=search_query) |
            models.Q(teacher__name__icontains=search_query) |
            models.Q(teacher__coaching_institute_name__icontains=search_query)
        )

    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        courses = courses.filter(price__gte=min_price)
    if max_price:
        courses = courses.filter(price__lte=max_price)

    # Qualification filter
    qualification = request.GET.get('qualification')
    if qualification:
        courses = courses.filter(teacher__qualification=qualification)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'price_low':
        courses = courses.order_by('price')
    elif sort_by == 'price_high':
        courses = courses.order_by('-price')
    elif sort_by == 'newest':
        courses = courses.order_by('-created_at')

    context = {
        'courses': courses,
        'teachers': teachers,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'qualification': qualification,
        'sort_by': sort_by,
        'qualification_choices': TeacherSignup.QUALIFICATION_CHOICES,
    }
    
    return render(request, 'Teacher/course_listing.html', context)

@login_required
def student_management(request):
    try:
        teacher = request.user.teacher
        students = Student.objects.filter(course__teacher=teacher).order_by('-created_at')
        courses = Course.objects.filter(teacher=teacher)
        
        context = {
            'students': students,
            'courses': courses,
        }
        return render(request, 'Teacher/student_management.html', context)
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please complete your registration.')
        return redirect('teacher_signup')

@login_required
def settings(request):
    try:
        teacher = request.user.teacher
        context = {
            'teacher': teacher,
        }
        return render(request, 'Teacher/settings.html', context)
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please complete your registration.')
        return redirect('teacher_signup')

@login_required
def analytics(request):
    try:
        teacher = request.user.teacher
        context = {
            'teacher': teacher,
        }
        return render(request, 'Teacher/analytics.html', context)
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please complete your registration.')
        return redirect('teacher_signup')

@login_required
def doubt(request):
    try:
        teacher = request.user.teacher
        context = {
            'teacher': teacher,
        }
        return render(request, 'Teacher/doubt.html', context)
    except TeacherSignup.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please complete your registration.')
        return redirect('teacher_signup')

def all_courses(request):
    courses = Course.objects.all().prefetch_related('shells', 'student_set')
    return render(request, 'Teacher/all_courses.html', {'courses': courses})

def course_demo(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    demo_lectures = Shell.objects.filter(course=course, lecture_type='demo').order_by('shell_number')
    
    context = {
        'course': course,
        'demo_lectures': demo_lectures,
    }
    return render(request, 'Teacher/course_demo.html', context)

def teacher_logout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Logged out successfully!')
    return redirect('teacher_login')