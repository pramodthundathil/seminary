# -------------------------------
# Python Standard Library Imports
# -------------------------------
import os
import uuid
from datetime import datetime, timedelta
import logging
import requests
import random
import string

# -------------------------------
# Django Core Imports
# -------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.db.models import Q, Count
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

# -------------------------------
# Local App Imports
# -------------------------------
from .models import (
    Students,
    Courses,
    Countries,
    StudentsExams,
    ReferenceForm,
    StudentsSubjects,
    ChurchAdmins,
    StudentsAssignment,
    Pages,
    Languages,
    Users,
    AdminPages,
    Support,Notifications,
    Subjects,StudentsInstructor,
    Exams,
    Payments,
    Contacts,
    Sliders,
    SliderPhotos,
    Branches,
    ChurchLoginCodeSettings
)

# Set up logger
logger = logging.getLogger(__name__)
from django.db import DatabaseError







from django.http import JsonResponse
import json



# @login_required(login_url='signin')


# @login_required(login_url='signin')



# @login_required(login_url='signin')
# def index(request): 
#     pages = Pages.objects.all()
#     # student=Students.objects.get(id=10600)
#     student=Students.objects.get(user=request.user)
#     context = {"pages":pages,"student":student}
#     return render(request,"site_pages/index.html",context)

##################only test###################
from django.shortcuts import render
from django.http import JsonResponse
from .context_processors import menu_context


def test_menu_debug(request):
    """
    Debug view to see the processed menu structure
    Access this at /test-menu-debug/
    """
    context_data = menu_context(request)
    
    # Pretty print the menu structure
    import json
    
    result = {
        'header_menu_items': context_data['header_menu_items'],
        'footer_menu_items': context_data['footer_menu_items'],
    }
    
    return JsonResponse(result, safe=False, json_dumps_params={'indent': 2})

############################only test#######################################
def index(request):
    """
    Home page view - menu context is automatically available
    via context processor
    """
    codes_needed = ["about-us","Admission-Process"]
    pages_data = Pages.objects.filter(
        code__in=codes_needed,
        status=True,
        deleted_at__isnull=True
    ).exclude(
        Q(code__isnull=True) |
        Q(code__exact="") |
        Q(code__regex=r'^\s*$')
    )  
    logger.info(f"Page data count: {pages_data.count()}")

    slider_photos = []
    try:
        # Fetch the slider with code 'home' or 'home-slider'
        slider = Sliders.objects.filter(code='home').first()
        if not slider:
            slider = Sliders.objects.filter(code='home-slider').first()
            
        if slider:
            slider_photos = slider.photos.all().select_related('media').order_by('id') # Or order by another field if available
    except Exception as e:
        logger.error(f"Error fetching slider: {e}")

    context = {
        "pages_data": pages_data,
        "slider_photos": slider_photos,
    }
    return render(request, "site_pages/index.html", context)


def page_detail(request, slug):
    """
    Dynamic page view for handling page URLs
    """
    page = get_object_or_404(Pages, code=slug, deleted_at__isnull=True, status=True)
    context = {
        "page": page
    }
    return render(request, "site_pages/page_detail.html", context)

def course_detail(request, slug):
    """
    Display individual course details
    slug parameter uses course_code field
    """
    # Get course by course_code (used as slug)
    course = get_object_or_404(
        Courses,
        course_code=slug,
        status=1  # Only show active courses
    )
    
    # You can add related courses or other data here
    related_courses = Courses.objects.filter(
        highest_qualification=course.highest_qualification,
        status=1
    ).exclude(id=course.id)[:3]
    
    context = {
        'course': course,
        'related_courses': related_courses,
    }
    
    return render(request, 'site_pages/course_detail.html', context)





def reference_form(request):
    # -------------------------------
    # Reference Details of the student
    # -------------------------------
    try: 
        countries = Countries.objects.all()       
        logger.info("Countries fetched successfully for dropdown")
    except Exception as e:
        logger.error(f"Error fetching countries: {e}", exc_info=True)
        messages.error(request, "Could not load country list. Please try again later.")
        countries = []

    # -------------------------------
    # Handle POST request
    # -------------------------------
    if request.method == "POST":
        try:
            # -------------------------------
            # Get form data
            # -------------------------------
            first_name = request.POST.get("first_name")
            middle_name = request.POST.get("middle_name")
            last_name = request.POST.get("last_name")
            email = request.POST.get("email")
            contact = request.POST.get("contact")
            nationality = request.POST.get("nationality")

            applicant_name = request.POST.get("applicant_name")
            relationship = request.POST.get("relationship")
            known_since = request.POST.get("known_since")

            spiritual_commitment = request.POST.get("spiritual_commitment")
            learning_capacity = request.POST.get("learning_capacity")
            dedication = request.POST.get("dedication")
            leadership = request.POST.get("leadership")
            church_involvement = request.POST.get("church_involvement")
            biblical_knowledge = request.POST.get("biblical_knowledge")
            moral_standard = request.POST.get("moral_standard")
            recommendation = request.POST.get("recommendation")
            financial_condition = request.POST.get("financial_condition")

            comments = request.POST.get("comments")
            # Get reCAPTCHA response           
            recaptcha_response = request.POST.get('g-recaptcha-response')

            try:
                data = {
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
                }

                r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=5)
                result = r.json()
                
                print("--- reCAPTCHA reference_form DEBUG ---")
                print("Secret Key:", settings.RECAPTCHA_SECRET_KEY)
                print("Response token in POST:", recaptcha_response)
                print("Google API verification result:", result)
                print("---------------------------------------")

                # If Google says "failed"
                if not result.get('success'):
                    error_msgs = result.get('error-codes', [])
                    err_str = f" ({', '.join(error_msgs)})" if error_msgs else ""
                    messages.error(request, f"Invalid reCAPTCHA{err_str}. Please try again.")
                    return render(request, 'site_pages/reference_form.html')
            except requests.exceptions.RequestException as e:
                print("--- reCAPTCHA reference_form EXCEPTION ---")
                print("Request exception:", e)
                print("-------------------------------------------")
                messages.error(request, f"reCAPTCHA verification failed due to a network issue: {str(e)}. Please try again.")
                return render(request, 'site_pages/reference_form.html')

            except ValueError as e:
                print("--- reCAPTCHA reference_form EXCEPTION ---")
                print("Value/JSON exception:", e)
                print("-------------------------------------------")
                messages.error(request, "Unexpected reCAPTCHA response. Please try again.")
                return render(request, 'site_pages/reference_form.html')

            logger.info(f"Received Reference Form submission from {first_name} {last_name}")

            # -------------------------------
            # Save to database
            # -------------------------------
            try:
                ReferenceForm.objects.create(
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    email=email,
                    contact_number=contact,
                    nationality=nationality,

                    applicant_name=applicant_name,
                    relation_with_applicant=relationship,
                    since_know_applicant=known_since,

                    spiritual_commitment=spiritual_commitment,
                    learning_capacity=learning_capacity,
                    dedication_for_loard=dedication,
                    leadership_skills=leadership,
                    church_involvement=church_involvement,
                    biblical_knowledge=biblical_knowledge,
                    moral_standard=moral_standard,
                    how_do_you_recommend=recommendation,
                    financial_condition=financial_condition,

                    personal_comment=comments
                )
                logger.info(f"Reference Form saved successfully for {first_name} {last_name}")
                messages.success(request, "Reference Form submitted successfully!")
                return redirect("reference_form")
            except Exception as e:
                logger.error(f"Error saving Reference Form: {e}", exc_info=True)
                messages.error(request, f"Could not save form: {e}")
        
        except Exception as e:
            logger.error(f"Error processing Reference Form submission: {e}", exc_info=True)
            messages.error(request, f"Error processing form: {e}")

    # -------------------------------
    # Default GET request
    # -------------------------------
    try:
       
        context = {               
            'countries': countries,           
            "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY
        }   

        return render(request, "site_pages/reference_form.html", context)
    except Exception as e:
        logger.error(f"Error rendering reference form page: {e}", exc_info=True)
        messages.error(request, "Could not load the reference form page.")
        return render(request, "site_pages/reference_form.html")

def payment_options(request):
    # -------------------------------
    # Payment Details of the student
    # -------------------------------
    try: 
        countries = Countries.objects.all()       
        logger.info("Countries fetched successfully for dropdown")
    except Exception as e:
        logger.error(f"Error fetching countries: {e}", exc_info=True)
        messages.error(request, "Could not load country list. Please try again later.")
        countries = []

    # -------------------------------
    # Handle POST request
    # -------------------------------
    if request.method == "POST":
        try:
            name = request.POST.get("full_name")
            email = request.POST.get("email")
            phone_code = request.POST.get("phone_code")
            phone_number = request.POST.get("phone")
            person_group = request.POST.get("person_group")
            amount = request.POST.get("amount")
            message_text = request.POST.get("message")

            phone = f"{phone_code}{phone_number}" if phone_code and phone_number else None
           
            # Get reCAPTCHA response           
            recaptcha_response = request.POST.get('g-recaptcha-response')

            try:
                data = {
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
                }

                r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=5)
                result = r.json()
                
                print("--- reCAPTCHA payment_options DEBUG ---")
                print("Secret Key:", settings.RECAPTCHA_SECRET_KEY)
                print("Response token in POST:", recaptcha_response)
                print("Google API verification result:", result)
                print("---------------------------------------")

                # If Google says "failed"
                if not result.get('success'):
                    error_msgs = result.get('error-codes', [])
                    err_str = f" ({', '.join(error_msgs)})" if error_msgs else ""
                    messages.error(request, f"Invalid reCAPTCHA{err_str}. Please try again.")
                    return render(request, 'site_pages/payment_options.html')
            except requests.exceptions.RequestException as e:
                print("--- reCAPTCHA payment_options EXCEPTION ---")
                print("Request exception:", e)
                print("-------------------------------------------")
                messages.error(request, f"reCAPTCHA verification failed due to a network issue: {str(e)}. Please try again.")
                return render(request, 'site_pages/payment_options.html')

            except ValueError as e:
                print("--- reCAPTCHA payment_options EXCEPTION ---")
                print("Value/JSON exception:", e)
                print("-------------------------------------------")
                messages.error(request, "Unexpected reCAPTCHA response. Please try again.")
                return render(request, 'site_pages/payment_options.html')

            logger.info(f"Received payment Form submission from {name}")
            # 1. Fetch Student (email is unique in your system)
            student = Students.objects.select_related("course_applied").filter(email=email).first()

            # 2. Fetch Related ChurchAdmin for this student
            church_admin = student.church_admins.first() if student else None

            # 3. Fetch Subject based on student's course
            student_subject_record = StudentsSubjects.objects.filter(
                student=student,
                is_approved=True
            ).first()
                        # -------------------------------
            # Save to database
            # -------------------------------
            try:
                payment_obj = Payments.objects.create(
                name=name,
                email=email,
                phone=phone,
                person_group=person_group,
                amount=amount,
                message=message_text,
                is_paid=False,
                student=student,
                church_admin=church_admin,
                subjects_id=student_subject_record 
                )
                logger.info(f"payment Form saved successfully for {name}")

                # Store data in session for the confirmation page
                request.session['payment_temp'] = {
                    'id': payment_obj.id,
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'group': person_group,
                    'amount': amount,
                    'message': message_text
                }
                
                return redirect("student_confirm_payment")
            except Exception as e:
                logger.error(f"Error saving payment Form: {e}", exc_info=True)
                messages.error(request, f"Could not save form: {e}")
        
        except Exception as e:
            logger.error(f"Error processing payment Form submission: {e}", exc_info=True)
            messages.error(request, f"Error processing form: {e}")

    # -------------------------------
    # Default GET request
    # -------------------------------
    try:
       
        context = {               
            'countries': countries,           
            "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY
        }   

        return render(request, "site_pages/payment_options.html", context)
    except Exception as e:
        logger.error(f"Error rendering payment form page: {e}", exc_info=True)
        messages.error(request, "Could not load the payment form page.")
        return render(request, "site_pages/payment_options.html")    
    

def signin(request):
    users =  Users.objects.all()
    if request.method == "POST":
        username = request.POST['email']
        password = request.POST['password']
        login_role = request.POST.get('login_role', 'student')

        user = authenticate(request, email = username, password = password)
        if user is not None:
            # Check role-specific access before logging them in entirely (or log them in and redirect fallback)
            
            if login_role == 'church_admin':
                # Determine if user is actually a ChurchAdmin (meaning they own it)
                church_admin_obj = ChurchAdmins.objects.filter(student__user=user, deleted_at__isnull=True).first()
                if not church_admin_obj:
                    messages.error(request, "You do not have a Church Admin account.")
                    return redirect("signin")
                
                if not church_admin_obj.is_paid and church_admin_obj.student and not church_admin_obj.student.status and not church_admin_obj.student.active:
                    payment = Payments.objects.filter(church_admin=church_admin_obj, is_paid=False).first()
                    if not payment:
                        payment = Payments.objects.create(
                            name=f"{user.first_name} {user.last_name or ''}".strip(),
                            email=user.email,
                            person_group="church_admin",
                            amount=church_admin_obj.amount,
                            is_paid=False,
                            church_admin=church_admin_obj
                        )
                    login(request, user)
                    request.session['registration_payment_id'] = payment.id
                    messages.warning(request, "Please complete your registration payment to activate your Church Admin account.")
                    return redirect('registration_payment')
                
                login(request, user)
                return redirect('church_admin_dashboard')
                
            elif login_role == 'church_user':
                # They must have a linked church admin, but they must NOT be the admin itself for strict separation.
                # If you allow admins to log in as users, just checking user.church_admin is enough.
                if not user.church_admin:
                    messages.error(request, "You are not affiliated with any Church User account.")
                    return redirect("signin")
                
                login(request, user)
                return redirect('church_user_home')
                
            # 'student' generic fallback role
            role = user.user_roles.first().role.name if user.user_roles.exists() else "No Role"
            
            if role == "Student":
                student = Students.objects.filter(user=user).first()
                if student:
                    if not student.is_paid:
                        # Look for existing unpaid registration payment
                        payment = Payments.objects.filter(student=student, is_paid=False, subjects_id__isnull=True, deleted_at__isnull=True).first()
                        
                        if payment:
                            balance_due = float(payment.amount or 0)
                            balance_due = student.get_balance_due()
                            
                            if balance_due > 0:
                                payment = Payments.objects.create(
                                    name=f"{student.first_name} {student.last_name or ''}".strip(),
                                    email=student.email,
                                    phone=student.phone_number,
                                    person_group="student",
                                    amount=balance_due,
                                    is_paid=False,
                                    student=student
                                )
                        
                        if payment and balance_due > 0:
                            login(request, user)
                            request.session['registration_payment_id'] = payment.id
                            messages.warning(request, f"Please complete your registration payment of ${balance_due:.2f} to proceed.")
                            return redirect('registration_payment')
                        else:
                            student.is_paid = True
                            student.save()
                    
                    if not student.active:
                        login(request, user)
                        return redirect('student_inactive')
            
            login(request, user)
            return redirect('admin_index')
        else:
            messages.info(request,"User name or password incorrect")
            return redirect("signin")
    return render(request,"site_pages/login.html")

def signout(request):
    logout(request)
    return redirect("index")

def signup_student(request):
    """
    Handle student application form submission
    GET: Display the registration form
    POST: Process and save the application
    """
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Generate unique student ID based on course
                course_id = request.POST.get('course_applied')
                course_code = 'GEN'
                if course_id:
                    try:
                        course = Courses.objects.get(id=course_id)
                        course_code = course.course_code
                    except Courses.DoesNotExist:
                        pass
                
                # Find maximum existing count for this course code prefix
                last_student = Students.objects.filter(student_id__startswith=f"TTS{course_code}").order_by('-student_id').first()
                if last_student and last_student.student_id:
                    try:
                        last_num = int(last_student.student_id.replace(f"TTS{course_code}", ""))
                        new_num = last_num + 1
                    except ValueError:
                        new_num = 1
                else:
                    new_num = 1
                
                student_id = f"TTS{course_code}{new_num:04d}"
                print("Generated student_id:", student_id)
                
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
                print("lang",language_id)
                try:
                    language = Languages.objects.get(id=language_id)
                    print("lang",language_id)
                except Languages.DoesNotExist:
                    messages.error(request, 'Invalid language selection.')
                    return render(request, 'site_pages/student_register.html')
                
                # Check if email already exists
                if Students.objects.filter(email=request.POST.get('email')).exists():
                    messages.error(request, 'An application with this email already exists.')
                    return render(request, 'site_pages/student_register.html')
                
                # Get reCAPTCHA response           
                recaptcha_response = request.POST.get('g-recaptcha-response')

                try:
                    data = {
                        'secret': settings.RECAPTCHA_SECRET_KEY,
                        'response': recaptcha_response
                    }

                    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=5)
                    result = r.json()

                    # If Google says "failed"
                    if not result.get('success'):
                        messages.error(request, "Invalid reCAPTCHA. Please try again.")
                        return render(request, 'site_pages/student_register.html')
                except requests.exceptions.RequestException:
                    # Network or API failure
                    messages.error(request, "reCAPTCHA verification failed due to a network issue. Please try again.")
                    return render(request, 'site_pages/student_register.html')

                except ValueError:
                    # JSON decoding failed
                    messages.error(request, "Unexpected reCAPTCHA response. Please try again.")
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

                    citizenship_id=request.POST.get('citizenship') or None,
                    country_id=request.POST.get('country') or None,
                    course_applied_id=request.POST.get('course_applied') or None,                    
                    
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
                   
                    zip_code=request.POST.get('zip_code') or None,
                    timezone=request.POST.get('timezone'),
                    
                    # Educational & Ministry Background
                    highest_education=request.POST.get('highest_education') or None,
                
                    starting_year=int(request.POST.get('starting_year')) if request.POST.get('starting_year') else None,
                    language_id=language.id,
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
                # Generate random password
                password = get_random_string(10)   # Example: "A8sd92LkPq"

                print("pass",password)

                # Create user record
                user = Users.objects.create(
                    name=f"{student.first_name} {student.last_name or ''}".strip(),
                    email=student.email,
                    username=student.student_id,   # Student ID becomes username
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    is_active=False,
                    image=photo_path,
                )

                # Set hashed password
                user.set_password(password)
                user.save()
                # Send email
                subject = "Your Student Login Details"
                message = f"""
                Hello {student.first_name},

                Your student account has been created successfully.

                Login Details:
                Email: {student.email}
                Temporary Password: {password}

                Please log in and change your password immediately for security reasons.

                Login here: {request.build_absolute_uri('/signin/')}

                Best regards,
                Trinity Theological Seminary
                        """
                        
                email_sent = send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.email],
                    fail_silently=False,
                )
                print("email sent",email_sent)
                if email_sent:
                    messages.success(request, f'Student created and login details sent to {student.email}')
                    logger.info(f'Email sent successfully to {student.email}')
                else:
                    messages.warning(request, 'Student created but email could not be sent.')
                    logger.warning(f'Email failed to send to {student.email}')
                        
            # except BadHeaderError:
            #     messages.error(request, 'Invalid header found in email.')
            #     logger.error('Bad header in email')
                
            # except Exception as e:
            #     messages.error(request, f'Error sending email: {str(e)}')
            #     logger.error(f'Email error: {str(e)}')
                
            return redirect('student_application_success', student_id=student_id)
            
            # Optional: Send email notification to student
            # send_application_confirmation_email(student)
            
            # Optional: Send email notification to admin
            # send_admin_notification_email(student)
            
           
                
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
            'countries': Countries.objects.all(),
            'courses': Courses.objects.all(),
            "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY
        }
        return render(request, 'site_pages/student_register.html', context)


def student_application_success(request,  student_id):
    """Success page after application submission"""
    student = Students.objects.get(student_id=student_id)
    return render(request, "site_pages/application_success.html", {"student": student.student_id})

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
    if request.method == 'POST':
        # reCAPTCHA validation
        recaptcha_response = request.POST.get('g-recaptcha-response')

        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }

        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        
        print("--- reCAPTCHA contact DEBUG ---")
        print("Secret Key:", settings.RECAPTCHA_SECRET_KEY)
        print("Response token in POST:", recaptcha_response)
        print("Google API verification result:", result)
        print("---------------------------------")

        if result.get('success'):
            # Save contact form
            Contacts.objects.create(
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                subject=request.POST.get('subject'),
                message=request.POST.get('message'),
                created_at=datetime.now()
            )

            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact-us')  # reload same page to show success message
        else:
            error_msgs = result.get('error-codes', [])
            err_str = f" ({', '.join(error_msgs)})" if error_msgs else ""
            messages.error(request, f"reCAPTCHA verification failed{err_str}. Please try again.")
            return redirect('contact-us')

    return render(request, "site_pages/contact.html", {
        "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY
    })


    
def admin_functions():
    print(AdminPages.objects.all())

@login_required
def student_index(request):
    try:
        # student  = request.user.student
        student= Students.objects.get(user=request.user)
    except:
        student = None
    print("--------------",student)
    print("LOGGED USER =", request.user.id)
    print("USER EMAIL =", request.user.email)
    print("USER NAME =", request.user.username)

    context = {
        'student': student,
    }
    return render(request, 'student/index.html')

def courses(request):
    courses = Courses.objects.filter(status=1).order_by('id')
    return render(request, 'site_pages/course_list.html', {'courses': courses})

def register(request):
    return render(request, 'site_pages/register.html')

def generate_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            # Find the student
            student = Users.objects.get(email=email)
        except Users.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect("forgot_password")

        # Generate new password
        new_password = get_random_string(length=10)
        try:
            # Save new password
            student.set_password(new_password)
            student.save()
        except Exception as e:
            print("Password update error:", e)

        student_data = Students.objects.get(email=email)
        # Email content (same format as your register email)
        subject = "Your Password Reset Request"
        message = f"""
        Hello {student_data.first_name},
               
        We received a request to reset your password.

        Your new temporary login details are:

        Email: {student.email}
        Temporary Password: {new_password}

        Please log in and change your password immediately for security purposes.

        Login here: {request.build_absolute_uri('/signin/')}

        Best regards,
        Trinity Theological Seminary
        """

        # Send email
        email_sent = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.email],
            fail_silently=False,
        )

        if email_sent:
            messages.success(request, f"New password has been sent to {student.email}")
        else:
            messages.error(request, "Password reset failed. Unable to send email.")

        return redirect("forgot_password")

    return render(request, "site_pages/forgot_password.html")

def signup_guest(request):
    """
    Handle guest registration form submission
    GET: Display the registration form
    POST: Process and save the registration
    """
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Generate unique guest ID
                guest_id = f"GST{uuid.uuid4().hex[:8].upper()}"
                print("guest_id:", guest_id)
                
                # Validate required fields
                required_fields = ['first_name', 'last_name', 'email', 'phone_number', 
                                 'date_of_birth', 'gender', 'mailing_address', 'city', 
                                 'state', 'country', 'zipcode', 'timezone', 'language', 
                                 'church_affiliation', 'associate_degree', 'phone_code']
                missing_fields = []
                
                for field in required_fields:
                    if not request.POST.get(field):
                        missing_fields.append(field.replace('_', ' ').title())
                
                if missing_fields:
                    messages.error(request, f"Missing required fields: {', '.join(missing_fields)}")
                    context = get_guest_context()
                    return render(request, 'site_pages/guest_register.html', context)
                
                # Get language instance
                language_id = request.POST.get('language')
                try:
                    language = Languages.objects.get(id=language_id)
                except Languages.DoesNotExist:
                    messages.error(request, 'Invalid language selection.')
                    context = get_guest_context()
                    return render(request, 'site_pages/guest_register.html', context)
                
                # Check if email already exists
                if Users.objects.filter(email=request.POST.get('email')).exists():
                    messages.error(request, 'A guest account with this email already exists.')
                    context = get_guest_context()
                    return render(request, 'site_pages/guest_register.html', context)
                
                # Check if email already exists in Users table
                if Users.objects.filter(email=request.POST.get('email')).exists():
                    messages.error(request, 'An account with this email already exists.')
                    context = get_guest_context()
                    return render(request, 'site_pages/guest_register.html', context)
                
                # Get reCAPTCHA response
                recaptcha_response = request.POST.get('g-recaptcha-response')
                
                try:
                    data = {
                        'secret': settings.RECAPTCHA_SECRET_KEY,
                        'response': recaptcha_response
                    }
                    
                    r = requests.post('https://www.google.com/recaptcha/api/siteverify', 
                                    data=data, timeout=5)
                    result = r.json()
                    
                    print("--- reCAPTCHA signup_guest DEBUG ---")
                    print("Secret Key:", settings.RECAPTCHA_SECRET_KEY)
                    print("Response token in POST:", recaptcha_response)
                    print("Google API verification result:", result)
                    print("------------------------------------")
                    
                    if not result.get('success'):
                        error_msgs = result.get('error-codes', [])
                        err_str = f" ({', '.join(error_msgs)})" if error_msgs else ""
                        messages.error(request, f"Invalid reCAPTCHA{err_str}. Please try again.")
                        context = get_guest_context()
                        return render(request, 'site_pages/guest_register.html', context)
                        
                except requests.exceptions.RequestException as e:
                    print("--- reCAPTCHA signup_guest EXCEPTION ---")
                    print("Request exception:", e)
                    print("----------------------------------------")
                    messages.error(request, f"reCAPTCHA verification failed due to a network issue: {str(e)}. Please try again.")
                    context = get_guest_context()
                    return render(request, 'site_pages/guest_register.html', context)
                    
                except ValueError as e:
                    print("--- reCAPTCHA signup_guest EXCEPTION ---")
                    print("Value/JSON exception:", e)
                    print("----------------------------------------")
                    messages.error(request, "Unexpected reCAPTCHA response. Please try again.")
                    context = get_guest_context()
                    return render(request, 'site_pages/guest_register.html', context)
                
                # # Create guest record
                # guest = Users.objects.create(
                #     guest_id=guest_id,
                #     associate_degree_id=request.POST.get('associate_degree') or None,
                #     first_name=request.POST.get('first_name'),
                #     middle_name=request.POST.get('middle_name') or None,
                #     last_name=request.POST.get('last_name'),
                #     email=request.POST.get('email'),
                #     phone_code=int(request.POST.get('phone_code')) if request.POST.get('phone_code') else None,
                #     phone_number=request.POST.get('phone_number'),
                #     date_of_birth=request.POST.get('date_of_birth'),
                #     gender=request.POST.get('gender'),
                #     mailing_address=request.POST.get('mailing_address'),
                #     city=request.POST.get('city'),
                #     state=request.POST.get('state'),
                #     country_id=request.POST.get('country'),
                #     zipcode=request.POST.get('zipcode'),
                #     timezone=request.POST.get('timezone'),
                #     language_id=language.id,
                #     church_affiliation=request.POST.get('church_affiliation'),
                #     created_at=timezone.now(),
                #     updated_at=timezone.now(),
                #     status=False,
                #     active=False
                # )
                
                # Generate random password
                password = get_random_string(10)               
                
                first_name=request.POST.get('first_name'),
                middle_name=request.POST.get('middle_name') or None,
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                user = Users.objects.create(
                    name=f"{first_name} {last_name or ''}".strip(),
                    email=email,
                    username=guest_id,   # Student ID becomes username
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    is_active=False,                   
                )      
                
                # Set hashed password
                user.set_password(password)
                user.save()
                
                # Send email
                try:
                    subject = "Your Guest Account Login Details"
                    message = f"""
                    Hello {first_name},

                    Your guest account has been created successfully.

                    Login Details:
                    Email: {email}
                    Username: {guest_id}
                    Temporary Password: {password}

                    Please log in and change your password immediately for security reasons.

                    Login here: {request.build_absolute_uri('/signin/')}

                    Best regards,
                    Trinity Theological Seminary
                                        """
                    
                    email_sent = send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    
                    if email_sent:
                        messages.success(request, f'Guest account created successfully! Login details sent to {email}')
                        logger.info(f'Email sent successfully to {email}')
                    else:
                        messages.warning(request, 'Guest account created but email could not be sent.')
                        logger.warning(f'Email failed to send to {email}')
                        
                except Exception as e:
                    messages.warning(request, f'Guest account created but error sending email: {str(e)}')
                    logger.error(f'Email error: {str(e)}')
                
                return redirect('guest_registration_success', guest_id=guest_id)
                
        except Languages.DoesNotExist:
            messages.error(request, 'Invalid language selection.')
            context = get_guest_context()
            return render(request, 'site_pages/guest_register.html', context)
            
        except ValueError as e:
            messages.error(request, f'Invalid data format: {str(e)}')
            context = get_guest_context()
            return render(request, 'site_pages/guest_register.html', context)
            
        except Exception as e:
            messages.error(request, f'An error occurred while submitting your registration. Please try again.')
            print(f"Error in guest registration: {str(e)}")
            logger.error(f"Guest registration error: {str(e)}")
            context = get_guest_context()
            return render(request, 'site_pages/guest_register.html', context)
    
    # GET request - display the form
    else:
        context = get_guest_context()
        return render(request, 'site_pages/guest_register.html', context)

def get_guest_context():
    """Helper function to get context for guest registration form"""
    return {
        'languages': Languages.objects.filter(status=True) if hasattr(Languages, 'status') else Languages.objects.all(),
        'countries': Countries.objects.all(),        
        'courses': Courses.objects.all(), 
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY
    }

def signup_church_admin(request):
    """
    Handle church admin registration form submission
    GET: Display the registration form
    POST: Process and save the registration
    """
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Generate unique ID based on role
                register_as = request.POST.get('register_as')
                is_user = (register_as == 'user')
                
                required_fields = ['register_as', 'first_name', 
                                 'last_name', 'email', 'phone_code', 'phone_number', 'date_of_birth', 
                                 'gender', 'mailing_address', 'city', 'state', 'country', 'zipcode', 
                                 'timezone', 'language']
                
                if is_user:
                    required_fields.extend(['church_code', 'church_affiliation'])
                else:
                    required_fields.extend(['associate_degree', 'package', 'name_of_church'])
                
                missing_fields = []
                for field in required_fields:
                    if not request.POST.get(field):
                        missing_fields.append(field.replace('_', ' ').title())
                
                if missing_fields:
                    messages.error(request, f"Missing required fields: {', '.join(missing_fields)}")
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                
                email = request.POST.get('email')
                
                # For Users, verify church code exists
                church_admin_obj = None
                church_code_obj = None
                church_code = request.POST.get('church_code')
                if is_user:
                    # User needs to join an existing church
                    church_admin_obj = ChurchAdmins.objects.filter(code=church_code).first()
                    if not church_admin_obj:
                        messages.error(request, 'Invalid church code. Please ask your Church Admin for a valid code.')
                        context = get_church_admin_context()
                        return render(request, 'site_pages/church_admin_register.html', context)
                    
                    if not church_admin_obj.is_paid:
                        messages.error(request, 'Church registration fee has not been paid. Please contact your Church Admin.')
                        context = get_church_admin_context()
                        return render(request, 'site_pages/church_admin_register.html', context)
                else:
                    # Admin/Pastor/Elder is creating a new church code
                    church_code = get_random_string(6).upper()
                    package_id = request.POST.get('package')
                    # Find the package (ChurchLoginCodeSettings) for this selection
                    church_code_obj = ChurchLoginCodeSettings.objects.filter(id=package_id).first()
                    if not church_code_obj:
                        messages.error(request, 'Could not find a valid package. Please select a valid package.')
                        context = get_church_admin_context()
                        return render(request, 'site_pages/church_admin_register.html', context)
                
                # Get language instance
                language_id = request.POST.get('language')
                try:
                    language = Languages.objects.get(id=language_id)
                except Languages.DoesNotExist:
                    messages.error(request, 'Invalid language selection.')
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                
                # Check if email already exists in Users table
                if Users.objects.filter(email=email).exists():
                    messages.error(request, 'An account with this email already exists.')
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                
                # Get reCAPTCHA response
                recaptcha_response = request.POST.get('g-recaptcha-response')
                
                try:
                    data = {
                        'secret': settings.RECAPTCHA_SECRET_KEY,
                        'response': recaptcha_response
                    }
                    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=5)
                    result = r.json()
                    
                    print("--- reCAPTCHA signup_church_admin DEBUG ---")
                    print("Secret Key:", settings.RECAPTCHA_SECRET_KEY)
                    print("Response token in POST:", recaptcha_response)
                    print("Google API verification result:", result)
                    print("-------------------------------------------")
                    
                    if not result.get('success'):
                        error_msgs = result.get('error-codes', [])
                        err_str = f" ({', '.join(error_msgs)})" if error_msgs else ""
                        messages.error(request, f"Invalid reCAPTCHA{err_str}. Please try again.")
                        context = get_church_admin_context()
                        return render(request, 'site_pages/church_admin_register.html', context)
                except Exception as e:
                    print("--- reCAPTCHA signup_church_admin EXCEPTION ---")
                    print("Exception:", e)
                    print("-----------------------------------------------")
                    messages.error(request, f"reCAPTCHA verification failed: {str(e)}. Please try again.")
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                
                # Common data
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                unique_prefix = "CHU" if is_user else "CHA"
                new_id = f"{unique_prefix}{uuid.uuid4().hex[:8].upper()}"
                
                # 1. ALWAYS Create Students record
                student = Students.objects.create(
                    student_id=new_id,
                    first_name=first_name,
                    middle_name=request.POST.get('middle_name') or None,
                    last_name=last_name,
                    email=email,
                    gender=request.POST.get('gender'),
                    phone_code=int(request.POST.get('phone_code')) if request.POST.get('phone_code') else None,
                    phone_number=request.POST.get('phone_number'),
                    date_of_birth=request.POST.get('date_of_birth'),
                    mailing_address=request.POST.get('mailing_address'),
                    city=request.POST.get('city'),
                    state=request.POST.get('state'),
                    country_id=request.POST.get('country'),
                    zip_code=request.POST.get('zipcode'),
                    timezone=request.POST.get('timezone'),
                    language_id=language.id,
                    church_affiliation=request.POST.get('church_affiliation'),
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    status=False,
                    active=False
                )

                if not is_user:
                    # 2. Create ChurchAdmins record if they are Admin
                    church_admin_obj = ChurchAdmins.objects.create(
                        student=student,
                        name_of_church=request.POST.get('name_of_church'),
                        name_of_paster=request.POST.get('name_of_paster') or None,
                        church_address=request.POST.get('church_address') or None,
                        church_code_id=church_code_obj.id,
                        code=church_code,
                        amount=church_code_obj.amount if church_code_obj else 0.0,
                        max_user_no=church_code_obj.max_user_no if church_code_obj else 0,
                        current_user_no=1, # Including themselves
                        is_paid=False,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                else:
                    # For User, increment the church admin user count
                    if church_admin_obj:
                        church_admin_obj.current_user_no = (church_admin_obj.current_user_no or 0) + 1
                        church_admin_obj.save()

                # Generate random password
                password = get_random_string(10)
                
                # 3. Create User record
                user = Users.objects.create(
                    name=f"{first_name} {last_name}".strip(),
                    email=email,
                    username=new_id,
                    church_admin=church_admin_obj, # This links the user to the ChurchAdmin
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    is_active=False,
                )
                
                # Link user back to student
                student.user = user
                student.save()

                # Set hashed password
                user.set_password(password)
                user.save()
                
                if not is_user:
                    # Redirect to payment for Church Admin
                    from home.models import Payments
                    payment = Payments.objects.create(
                        name=f"{first_name} {last_name}".strip(),
                        email=email,
                        phone=request.POST.get('phone_number'),
                        person_group="church_admin",
                        amount=church_admin_obj.amount,
                        is_paid=False,
                        student=student,
                        church_admin=church_admin_obj
                    )
                    request.session['registration_payment_id'] = payment.id
                    return redirect('registration_payment')
                else:
                    # Send email and redirect to success for Church User
                    role_display = "Church User"
                    try:
                        subject = f"Your {role_display} Account Login Details"
                        message = f"""
                        Hello {first_name},

                        Your {role_display.lower()} account has been created successfully.

                        Please wait for approval of Trinity Theological Seminary.


                        Best regards,
                        Trinity Theological Seminary
                        """
                        
                        email_sent = send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        
                        if email_sent:
                            messages.success(request, f'{role_display} account created successfully! Login details sent to {email}')
                            logger.info(f'Email sent successfully to {email}')
                        else:
                            messages.warning(request, f'{role_display} account created but email could not be sent.')
                            logger.warning(f'Email failed to send to {email}')

                        # Send approval request email to Super Admin
                        try:
                            admin_email = 'contact@byteboot.in'
                            admin_subject = "New Church User Registration - Approval Required"
                            admin_message = f"""Hello Admin,

A new church user has registered and requires approval.

Details:
Name: {first_name} {last_name}
Email: {email}
Church: {church_admin_obj.name_of_church if church_admin_obj else 'N/A'}
Church Admin: {church_admin_obj.student.first_name if (church_admin_obj and church_admin_obj.student) else 'N/A'}

Please log in to the admin panel to review and approve this user.

Best regards,
Trinity Theological Seminary"""
                            send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
                        except Exception as admin_err:
                            logger.error(f"Failed to send admin signup notification: {admin_err}")

                        # Send approval request email to corresponding Church Admin
                        if church_admin_obj and church_admin_obj.student and church_admin_obj.student.email:
                            try:
                                church_admin_email = church_admin_obj.student.email
                                ca_subject = "New Church User Registration - Approval Required"
                                ca_message = f"""Hello {church_admin_obj.student.first_name},

A new user has registered under your church code and requires your approval.

Details:
Name: {first_name} {last_name}
Email: {email}

Please log in to your Church Admin Dashboard to review and approve this user.

Best regards,
Trinity Theological Seminary"""
                                send_mail(ca_subject, ca_message, settings.DEFAULT_FROM_EMAIL, [church_admin_email], fail_silently=True)
                            except Exception as ca_err:
                                logger.error(f"Failed to send church admin signup notification: {ca_err}")
                            
                    except Exception as e:
                        messages.warning(request, f'{role_display} account created but error sending email: {str(e)}')
                        logger.error(f'Email error: {str(e)}')
                    
                    return redirect('church_admin_registration_success', admin_id=new_id)             
        
        except Languages.DoesNotExist:
            logger.error("Languages.DoesNotExist during registrations")
            messages.error(request, 'Invalid language selection.')
            context = get_church_admin_context()
            return render(request, 'site_pages/church_admin_register.html', context)
        
        except IntegrityError as e:
            logger.error(f"IntegrityError in registration: {str(e)}")
            error_msg = str(e)
            if 'unique' in error_msg.lower() and 'email' in error_msg.lower():
                messages.error(request, 'This email is already registered. Please use a different email or log in.')
            else:
                messages.error(request, 'A database error occurred. Please ensure all details are correct.')
            context = get_church_admin_context()
            return render(request, 'site_pages/church_admin_register.html', context)
            
        except ValueError as e:
            logger.error(f"ValueError in registration: {str(e)}")
            messages.error(request, f'Invalid data format: {str(e)}')
            context = get_church_admin_context()
            return render(request, 'site_pages/church_admin_register.html', context)
            
        except Exception as e:
            logger.exception("Unexpected error in church admin registration")
            messages.error(request, f'An error occurred while submitting your registration. Please try again later.')
            context = get_church_admin_context()
            return render(request, 'site_pages/church_admin_register.html', context)
    
    # GET request - display the form
    else:
        context = get_church_admin_context()
        return render(request, 'site_pages/church_admin_register.html', context)


def get_church_admin_context():
    """Helper function to get context for church admin registration form"""
    import json
    packages_query = ChurchLoginCodeSettings.objects.filter(status=1)
    packages_by_branch = {}
    for pkg in packages_query:
        if pkg.branches_id not in packages_by_branch:
            packages_by_branch[pkg.branches_id] = []
        packages_by_branch[pkg.branches_id].append({
            'id': pkg.id,
            'name': pkg.name,
            'amount': pkg.amount,
            'max_user': pkg.max_user_no
        })
        
    return {
        'languages': Languages.objects.filter(status=True) if hasattr(Languages, 'status') else Languages.objects.all(),
        'countries': Countries.objects.all(),
        'branches': Branches.objects.filter(is_associate_degree=True, status=True),
        'packages_json': json.dumps(packages_by_branch),
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY,
        'selected_branch': None, # Default if needed
    }

def check_email_exists(request):
    """AJAX view to check if an email already exists in Users"""
    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'exists': False, 'message': 'Email is required'}, status=400)
    
    exists = Users.objects.filter(email=email).exists()
    return JsonResponse({
        'exists': exists,
        'message': 'This email is already registered.' if exists else 'Email is available.'
    })

def check_church_code(request):
    """AJAX view to check if a church code exists in ChurchAdmins"""
    code = request.GET.get('code', '').strip()
    if not code:
        return JsonResponse({'exists': False, 'message': 'Code is required'}, status=400)
    
    exists = ChurchAdmins.objects.filter(code=code).exists()
    return JsonResponse({
        'exists': exists,
        'message': 'Valid church code found.' if exists else 'Invalid church code. Please check with your Church Admin.'
    })

# Success page views
def guest_registration_success(request, guest_id):
    """Display success page after guest registration"""
    try:
        guest = Users.objects.get(username=guest_id)
        context = {
            'guest': guest,
            'title': 'Registration Successful'
        }
        return render(request, 'site_pages/guest_success.html', context)
    except Users.DoesNotExist:
        messages.error(request, 'Guest account not found.')
        return redirect('guest_register')


def church_admin_registration_success(request, admin_id):
    """Display success page after church admin registration"""
    try:
        admin = Users.objects.get(username=admin_id)
        context = {
            'admin': admin,
            'title': 'Registration Successful'
        }
        return render(request, 'site_pages/church_admin_success.html', context)
    except ChurchAdmins.DoesNotExist:
        messages.error(request, 'Church admin account not found.')
        return redirect('church_admin_register')


from django.views.decorators.csrf import csrf_exempt
from home.models import Payments

def registration_payment(request):
    payment_id = request.session.get("registration_payment_id")
    
    if not payment_id and request.user.is_authenticated:
        # Self-healing check for logged-in student who direct-navigates
        student = Students.objects.filter(user=request.user).first()
        if student and not student.is_paid:
            payment = Payments.objects.filter(student=student, is_paid=False, subjects_id__isnull=True, deleted_at__isnull=True).first()
            if payment:
                balance_due = float(payment.amount or 0)
            else:
                balance_due = student.get_balance_due()
                
                if balance_due > 0:
                    payment = Payments.objects.create(
                        name=f"{student.first_name} {student.last_name or ''}".strip(),
                        email=student.email,
                        phone=student.phone_number,
                        person_group="student",
                        amount=balance_due,
                        is_paid=False,
                        student=student
                    )
            
            if payment and balance_due > 0:
                payment_id = payment.id
                request.session["registration_payment_id"] = payment.id
            else:
                student.is_paid = True
                student.save()
                messages.success(request, "Your registration fee has already been paid.")
                return redirect("student_home")

    if not payment_id:
        messages.error(request, "No pending registration payment found.")
        return redirect("register")
    
    payment = get_object_or_404(Payments, id=payment_id)
    if payment.is_paid:
        messages.success(request, "This registration fee has already been paid.")
        if request.user.is_authenticated:
            return redirect("student_home")
        return redirect("index")
        
    context = {
        "payment": payment,
        "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID,
    }
    return render(request, "site_pages/registration_payment.html", context)

@csrf_exempt
def capture_registration_payment(request):
    import json
    try:
        data = json.loads(request.body)
        order_id = data.get("orderID")
        if not order_id:
            return JsonResponse({"status": "failed", "message": "Order ID missing"}, status=400)

        payment_id = request.session.get("registration_payment_id")
        if not payment_id:
            return JsonResponse({"status": "failed", "message": "No pending payment session"}, status=400)

        payment_obj = get_object_or_404(Payments, id=payment_id)

        # 1) PayPal API Credentials
        CLIENT_ID = settings.PAYPAL_CLIENT_ID
        CLIENT_SECRET = settings.PAYPAL_CLIENT_SECRET

        # Get Access Token from PayPal Sandbox
        token_url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        token_headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        token_data = {"grant_type": "client_credentials"}
        token_response = requests.post(
            token_url,
            headers=token_headers,
            data=token_data,
            auth=(CLIENT_ID, CLIENT_SECRET),
            timeout=10
        )
        access_token = token_response.json()["access_token"]

        # Capture Order
        capture_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
        capture_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        capture_response = requests.post(capture_url, headers=capture_headers, timeout=10)
        capture_json = capture_response.json()
        status = capture_json.get("status")

        if status == "COMPLETED":
            with transaction.atomic():
                payment_obj.is_paid = True
                payment_obj.save()

                redirect_url = "/"

                if payment_obj.student:
                    student = payment_obj.student
                    student.is_paid = True
                    student.save()

                    # Send Email to Student
                    try:
                        subject = 'Application Received - Trinity Seminary'
                        message = f'''Dear {student.first_name},

Thank you for applying to Trinity Seminary. Your application has been received and is currently under review.
You will receive another email once your application status changes.

Best regards,
Administration'''
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [student.email], fail_silently=True)
                    except Exception as e:
                        logger.error(f"Failed to send student confirmation email: {e}")

                    # Send Email to Admin
                    try:
                        admin_subject = 'New Student Application Received'
                        admin_message = f'''A new student application has been submitted.
Name: {student.first_name} {student.last_name}
Course: {student.course_applied.course_name if student.course_applied else 'N/A'}

Please login to the admin panel to review.'''
                        send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, ['contact@byteboot.in'], fail_silently=True)
                    except Exception as e:
                        logger.error(f"Failed to send admin notification email: {e}")

                    if request.user.is_authenticated:
                        redirect_url = "/student/"
                    else:
                        redirect_url = f"/student/application/success/{student.student_id}/"

                elif payment_obj.church_admin:
                    church_admin = payment_obj.church_admin
                    church_admin.is_paid = True
                    church_admin.save()

                    # Send welcome email for Church Admin
                    try:
                        subject = "Your Church Admin Account Login Details"
                        message = f"""
                        Hello {church_admin.student.first_name},

                        Your church admin account has been created successfully.

                        Please wait for approval of Trinity Theological Seminary.


                        Best regards,
                        Trinity Theological Seminary
                        """
                        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [church_admin.student.email], fail_silently=True)
                    except Exception as e:
                        logger.error(f"Failed to send church admin confirmation email: {e}")

                    if request.user.is_authenticated:
                        redirect_url = "/church-admin/dashboard/"
                    else:
                        redirect_url = f"/church-admin/success/{church_admin.student.student_id}/"

                # Clear session payment ID
                request.session.pop("registration_payment_id", None)
                
                return JsonResponse({"status": "success", "redirect_url": redirect_url})
        else:
            return JsonResponse({"status": "failed", "message": "PayPal capture did not complete"}, status=400)

    except Exception as e:
        logger.error(f"Error capturing registration payment: {e}")
        return JsonResponse({"status": "failed", "message": str(e)}, status=500)