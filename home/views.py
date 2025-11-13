from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.shortcuts import render
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from .models import (
    Students, Courses, StudentsExams, ReferenceForm, 
    StudentsSubjects, Assignments, StudentsAssignment
)
from .decorators import role_redirection

# Create your views here.
from .models import *

def index(request): 
    pages = Pages.objects.all()
    context = {"pages":pages}
    return render(request,"site_pages/index.html",context)

def about_us(request):
    return render(request,"site_pages/about_us.html")

def signin(request):
    users =  Users.objects.all()
    print(users)
    if request.method == "POST":
        username = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email = username, password = password)
        if user is not None:
            login(request,user)
            return redirect('admin_index')
        else:
            messages.info(request,"User name or password incorrect")
            return redirect("signin")
    return render(request,"site_pages/login.html")

def signout(request):
    logout(request)
    return redirect("index")

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.db import transaction
from .models import Students, Languages
import uuid
import os


def signup_student(request):
    """
    Handle student application form submission
    GET: Display the registration form
    POST: Process and save the application
    """
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Generate unique student ID
                student_id = f"STU{uuid.uuid4().hex[:8].upper()}"
                
                # Validate required fields
                required_fields = ['first_name', 'email', 'date_of_birth', 'gender', 
                                 'phone_number', 'timezone', 'language']
                missing_fields = []
                
                for field in required_fields:
                    if not request.POST.get(field):
                        missing_fields.append(field.replace('_', ' ').title())
                
                if missing_fields:
                    messages.error(request, f"Missing required fields: {', '.join(missing_fields)}")
                    return render(request, 'site_pages/student_register.html')
                
                # Handle file uploads
                photo_path = None
                certificate_paths = [None] * 5
                
                # Upload photo
                if request.FILES.get('photo'):
                    photo = request.FILES['photo']
                    # Validate file size (max 5MB)
                    if photo.size > 5 * 1024 * 1024:
                        messages.error(request, 'Photo file size must be less than 5MB.')
                        return render(request, 'site_pages/student_register.html')
                    
                    # Validate file extension
                    ext = os.path.splitext(photo.name)[1].lower()
                    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                        messages.error(request, 'Photo must be in JPG, PNG, or GIF format.')
                        return render(request, 'site_pages/student_register.html')
                    
                    fs = FileSystemStorage(location='media/student_photos/')
                    filename = fs.save(f"{student_id}_{photo.name}", photo)
                    photo_path = f"student_photos/{filename}"
                
                # Upload certificates
                for i in range(1, 6):
                    cert_key = f'certificate{i}'
                    if request.FILES.get(cert_key):
                        cert = request.FILES[cert_key]
                        
                        # Validate file size (max 10MB)
                        if cert.size > 10 * 1024 * 1024:
                            messages.error(request, f'Certificate {i} file size must be less than 10MB.')
                            return render(request, 'site_pages/student_register.html')
                        
                        # Validate file extension
                        ext = os.path.splitext(cert.name)[1].lower()
                        if ext not in ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']:
                            messages.error(request, f'Certificate {i} must be in PDF, JPG, PNG, DOC, or DOCX format.')
                            return render(request, 'site_pages/student_register.html')
                        
                        fs = FileSystemStorage(location='media/student_certificates/')
                        filename = fs.save(f"{student_id}_cert{i}_{cert.name}", cert)
                        certificate_paths[i-1] = f"student_certificates/{filename}"
                
                # Get language instance
                language_id = request.POST.get('language')
                try:
                    language = Languages.objects.get(id=language_id)
                except Languages.DoesNotExist:
                    messages.error(request, 'Invalid language selection.')
                    return render(request, 'site_pages/student_register.html')
                
                # Check if email already exists
                if Students.objects.filter(email=request.POST.get('email')).exists():
                    messages.error(request, 'An application with this email already exists.')
                    return render(request, 'site_pages/student_register.html')
                
                # Create student record
                student = Students.objects.create(
                    student_id=student_id,
                    
                    # Personal Information
                    first_name=request.POST.get('first_name'),
                    middle_name=request.POST.get('middle_name') or None,
                    last_name=request.POST.get('last_name') or None,
                    email=request.POST.get('email'),
                    gender=request.POST.get('gender'),
                    citizenship=int(request.POST.get('citizenship')) if request.POST.get('citizenship') else None,
                    date_of_birth=request.POST.get('date_of_birth') or None,
                    mrital_status=request.POST.get('mrital_status') or None,
                    spouse_name=request.POST.get('spouse_name') or None,
                    children=int(request.POST.get('children')) if request.POST.get('children') else None,
                    photo=photo_path,
                    
                    # Contact Information
                    phone_code=int(request.POST.get('phone_code')) if request.POST.get('phone_code') else None,
                    phone_number=request.POST.get('phone_number') or None,
                    mailing_address=request.POST.get('mailing_address') or None,
                    city=request.POST.get('city') or None,
                    state=request.POST.get('state') or None,
                    country=int(request.POST.get('country')) if request.POST.get('country') else None,
                    zip_code=request.POST.get('zip_code') or None,
                    timezone=request.POST.get('timezone'),
                    
                    # Educational & Ministry Background
                    highest_education=request.POST.get('highest_education') or None,
                    course_applied=int(request.POST.get('course_applied')) if request.POST.get('course_applied') else None,
                    associate_degree=int(request.POST.get('associate_degree')) if request.POST.get('associate_degree') else None,
                    starting_year=int(request.POST.get('starting_year')) if request.POST.get('starting_year') else None,
                    language=language,
                    ministerial_status=request.POST.get('ministerial_status') or None,
                    church_affiliation=request.POST.get('church_affiliation') or None,
                    
                    # Financial Information
                    scholarship_needed=request.POST.get('scholarship_needed') or None,
                    currently_employed=request.POST.get('currently_employed') or None,
                    income=request.POST.get('income') or None,
                    affordable_amount=request.POST.get('affordable_amount') or None,
                    
                    # References
                    reference_name1=request.POST.get('reference_name1') or None,
                    reference_email1=request.POST.get('reference_email1') or None,
                    reference_phone1=request.POST.get('reference_phone1') or None,
                    reference_name2=request.POST.get('reference_name2') or None,
                    reference_email2=request.POST.get('reference_email2') or None,
                    reference_phone2=request.POST.get('reference_phone2') or None,
                    reference_name3=request.POST.get('reference_name3') or None,
                    reference_email3=request.POST.get('reference_email3') or None,
                    reference_phone3=request.POST.get('reference_phone3') or None,
                    
                    # Certificates
                    certificate1=certificate_paths[0],
                    certificate2=certificate_paths[1],
                    certificate3=certificate_paths[2],
                    certificate4=certificate_paths[3],
                    certificate5=certificate_paths[4],
                    
                    # Additional Information
                    message=request.POST.get('message') or None,
                    
                    # System fields
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    status=False,  # Pending approval
                    active=False   # Not active until approved
                )
                
                # Send success message with student ID
                messages.success(
                    request, 
                    f'Application submitted successfully! Your Student ID is: {student_id}. '
                    'You will receive an email once your application is reviewed.'
                )
                
                # Optional: Send email notification to student
                # send_application_confirmation_email(student)
                
                # Optional: Send email notification to admin
                # send_admin_notification_email(student)
                
                return redirect('student_application_success')
                
        except Languages.DoesNotExist:
            messages.error(request, 'Invalid language selection.')
            return render(request, 'site_pages/student_register.html')
            
        except ValueError as e:
            messages.error(request, f'Invalid data format: {str(e)}')
            return render(request, 'site_pages/student_register.html')
            
        except Exception as e:
            messages.error(request, f'An error occurred while submitting your application. Please try again.')
            print(f"Error in student registration: {str(e)}")  # Log the error
            return render(request, 'site_pages/student_register.html')
    
    # GET request - display the form
    else:
        context = {
            'languages': Languages.objects.filter(status=True) if hasattr(Languages, 'status') else Languages.objects.all(),
            # Add other dropdown options as needed
            # 'countries': Country.objects.all(),
            # 'courses': Course.objects.all(),
        }
        return render(request, 'site_pages/student_register.html', context)


def student_application_success(request):
    """Success page after application submission"""
    return render(request, 'site_pages/application_success.html')


# Optional: Email notification functions
def send_application_confirmation_email(student):
    """
    Send confirmation email to student after application submission
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = 'Application Received - Student Registration'
    message = f"""
    Dear {student.first_name},
    
    Thank you for submitting your student application.
    
    Your Student ID: {student.student_id}
    
    We have received your application and our admissions team will review it within 3-5 business days.
    You will receive an email notification once your application status is updated.
    
    If you have any questions, please contact us at admissions@yourdomain.com
    
    Best regards,
    Admissions Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [student.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send confirmation email: {str(e)}")


def send_admin_notification_email(student):
    """
    Send notification email to admin when new application is submitted
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = f'New Student Application - {student.student_id}'
    message = f"""
    A new student application has been submitted.
    
    Student ID: {student.student_id}
    Name: {student.first_name} {student.last_name}
    Email: {student.email}
    Course Applied: {student.course_applied}
    Submitted: {student.created_at}
    
    Please review the application in the admin panel.
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send admin notification: {str(e)}")

def contact(request):
    return render(request,"site_pages/contact.html")

def register(request):
    return render(request,"site_pages/register.html" )

def admin_functions():
    print(AdminPages.objects.all())


@role_redirection
@login_required
def admin_index(request):
    # admin_functions()
    # Get total students
    total_students = Students.objects.filter(active=1).count()
    admin_pages = AdminPages.objects.all().order_by('menu_order')
    
    # Get new students (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_students = Students.objects.filter(
        created_at__gte=thirty_days_ago,
        active=1
    ).order_by('-created_at')[:10]
    
    # Gender statistics
    male_count = Students.objects.filter(gender='Male', active=1).count()
    female_count = Students.objects.filter(gender='Female', active=1).count()
    
    if total_students > 0:
        male_percentage = round((male_count / total_students) * 100)
        female_percentage = round((female_count / total_students) * 100)
        # Calculate SVG circle offsets (314 is circumference for r=50)
        male_offset = 314 - (314 * male_percentage / 100)
        female_offset = 314 - (314 * female_percentage / 100)
    else:
        male_percentage = female_percentage = 0
        male_offset = female_offset = 314
    
    # Get courses with student count using course_applied field
    courses_list = []
    for course in Courses.objects.filter(status=1)[:6]:
        # Count students who applied for this course
        student_count = Students.objects.filter(
            course_applied=course.id,
            active=1
        ).count()
        
        # Add student_count as an attribute to the course object
        course.student_count = student_count
        courses_list.append(course)
    
    # Get pending exam requests
   
    # Get recent references
    references = ReferenceForm.objects.order_by('-created_at')[:10]
    
    # Get pending subject requests
    
    # Calculate assignments in progress
    total_assignments = Assignments.objects.count()
    completed_assignments = StudentsAssignment.objects.filter(
        submitted_on__isnull=False
    ).count()
    
    if total_assignments > 0:
        tasks_in_progress = round(((total_assignments - completed_assignments) / total_assignments) * 100)
    else:
        tasks_in_progress = 0
    
    # Calculate total exams completed
    total_exams_completed = StudentsExams.objects.filter(
        is_exam_ended=1
    ).count()
    
    # Attendance calculation (example - customize based on your logic)
    # You can calculate this based on actual attendance records if you have them
    total_classes = 100  # Example
    attended_classes = 80  # Example
    attendance_percentage = round((attended_classes / total_classes) * 100) if total_classes > 0 else 0
    
    context = {
        'total_students': total_students,
        'new_students': new_students,
        'male_count': male_count,
        'female_count': female_count,
        'male_percentage': male_percentage,
        'female_percentage': female_percentage,
        'male_offset': male_offset,
        'female_offset': female_offset,
        'courses': courses_list,
        # 'exam_requests': exam_requests,
        'references': references,
        # 'subject_requests': subject_requests,
        'attendance_percentage': attendance_percentage,
        'tasks_in_progress': tasks_in_progress,
        'total_exams_completed': total_exams_completed,
        'students_start': 1,
        'students_end': min(10, len(new_students)),
        'subjects_start': 1,
        # 'subjects_end': min(10, len(subject_requests)),
        'admin_pages':admin_pages
    }
    
    return render(request,"admin/index.html",context)

@login_required
def student_index(request):
    try:
        student  = request.user.student
    except:
        student = None
    print(student,"--------------")
    return render(request, 'student/index.html')