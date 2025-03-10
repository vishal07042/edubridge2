from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .models import Student, Enrollment
from Teacher.models import Course, TeacherSignup, Shell
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def student_index(request):
    courses = Course.objects.all()
    teachers = TeacherSignup.objects.all()  # Changed from Teacher to TeacherSignup
    
    # Handle contact form submission
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Compose email message
        email_message = f"""
        New contact form submission from {name}
        
        Email: {email}
        Subject: {subject}
        Message:
        {message}
        """

        try:
            # Send email
            send_mail(
                f'Contact Form: {subject}',
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
        
        return redirect('students:student_index')

    # Get filter parameters
    sort_by = request.GET.get('sort_by', '')
    teacher_filter = request.GET.get('teacher', '')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    search_query = request.GET.get('search', '')

    # Apply filters
    if search_query:
        courses = courses.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(teacher__name__icontains=search_query)  # This will still work as the field name is correct
        )

    if teacher_filter:
        courses = courses.filter(teacher_id=teacher_filter)

    if price_min:
        courses = courses.filter(price__gte=float(price_min))
    if price_max:
        courses = courses.filter(price__lte=float(price_max))

    # Apply sorting
    if sort_by == 'price_low_high':
        courses = courses.order_by('price')
    elif sort_by == 'price_high_low':
        courses = courses.order_by('-price')
    elif sort_by == 'name_az':
        courses = courses.order_by('name')
    elif sort_by == 'name_za':
        courses = courses.order_by('-name')
    elif sort_by == 'newest':
        courses = courses.order_by('-created_at')
    elif sort_by == 'oldest':
        courses = courses.order_by('created_at')

    context = {
        'courses': courses,
        'teachers': teachers,
        'current_sort': sort_by,
        'current_teacher': teacher_filter,
        'current_price_min': price_min,
        'current_price_max': price_max,
        'search_query': search_query,
    }
    
    return render(request, 'Students/student_index.html', context)

def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if the user has a student profile, if not create one
            try:
                student = Student.objects.get(user=user)
            except Student.DoesNotExist:
                # Create a new student profile
                student = Student.objects.create(
                    user=user,
                    phone=''  # Default empty phone
                )
            
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('students:student_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'Students/student_login.html')

def student_signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('students:student_signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
            return redirect('students:student_signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return redirect('students:student_signup')

        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create the student profile
            student = Student.objects.create(
                user=user,
                phone=phone
            )
            
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('students:student_login')
            
        except Exception as e:
            messages.error(request, 'An error occurred during registration.')
            return redirect('students:student_signup')

    return render(request, 'Students/student_signup.html')

@login_required
def student_dashboard(request):
    # Get or create student profile
    student, created = Student.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}  # Default empty phone
    )
    
    enrolled_courses = Enrollment.objects.filter(student=student).select_related('course', 'course__teacher')
    
    # Calculate statistics
    completed_courses = enrolled_courses.filter(progress=100).count()
    in_progress_courses = enrolled_courses.filter(progress__gt=0, progress__lt=100).count()
    certificates_earned = completed_courses  # For now, one certificate per completed course
    
    context = {
        'enrolled_courses': enrolled_courses,
        'completed_courses': completed_courses,
        'in_progress_courses': in_progress_courses,
        'certificates_earned': certificates_earned,
    }
    
    return render(request, 'Students/student_dashboard.html', context)

def student_logout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('students:student_login')

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    demo_lectures = Shell.objects.filter(course=course, lecture_type='demo').order_by('shell_number')
    context = {
        'course': course,
        'demo_lectures': demo_lectures,
    }
    return render(request, 'Students/course_detail.html', context)

@login_required
def payment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    context = {
        'course': course,
    }
    return render(request, 'Students/payment.html', context)

@login_required
def process_payment(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        
        # Get or create student profile
        student, created = Student.objects.get_or_create(
            user=request.user,
            defaults={'phone': ''}  # Default empty phone
        )
        
        try:
            # Create enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={'progress': 0}
            )
            
            if created:
                messages.success(request, f'Successfully enrolled in {course.name}!')
            else:
                messages.info(request, 'You are already enrolled in this course.')
            
            return redirect('students:student_dashboard')
        except Exception as e:
            messages.error(request, 'Enrollment failed. Please try again.')
            return redirect('students:payment', course_id=course_id)
    
    return redirect('students:course_detail', course_id=course_id)

@login_required
def course_learning(request, course_id, shell_number=1):
    course = get_object_or_404(Course, id=course_id)
    
    # Get or create student profile
    student, created = Student.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}  # Default empty phone
    )
    
    enrollment = get_object_or_404(Enrollment, course=course, student=student)
    
    # Get all shells for this course
    all_shells = Shell.objects.filter(course=course).order_by('shell_number')
    total_shells = all_shells.count()
    
    # Get current shell
    current_shell = get_object_or_404(Shell, course=course, shell_number=shell_number)
    
    # Get previous and next shells
    prev_shell = Shell.objects.filter(
        course=course, 
        shell_number__lt=shell_number
    ).order_by('-shell_number').first()
    
    next_shell = Shell.objects.filter(
        course=course, 
        shell_number__gt=shell_number
    ).order_by('shell_number').first()
    
    # Update progress
    completed_lectures = set(enrollment.completed_lectures.split(',')) if enrollment.completed_lectures else set()
    completed_lectures.add(str(shell_number))
    enrollment.completed_lectures = ','.join(completed_lectures)
    
    # Calculate progress percentage
    progress = (len(completed_lectures) / total_shells) * 100
    enrollment.progress = round(progress)
    
    # Check if course is completed
    if progress == 100:
        enrollment.completed = True
    
    enrollment.save()
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'current_shell': current_shell,
        'prev_shell': prev_shell,
        'next_shell': next_shell,
        'all_shells': all_shells,
        'total_shells': total_shells,
    }
    
    return render(request, 'Students/course_learning.html', context)

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
            return redirect('students:contact')
            
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
            return render(request, 'Students/contact.html', context)

    return render(request, 'Students/contact.html')

