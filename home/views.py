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
    SliderPhotos
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

                # If Google says "failed"
                if not result.get('success'):
                    messages.error(request, "Invalid reCAPTCHA. Please try again.")
                    return render(request, 'site_pages/reference_form.html')
            except requests.exceptions.RequestException:
                # Network or API failure
                messages.error(request, "reCAPTCHA verification failed due to a network issue. Please try again.")
                return render(request, 'site_pages/reference_form.html')

            except ValueError:
                # JSON decoding failed
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

                # If Google says "failed"
                if not result.get('success'):
                    messages.error(request, "Invalid reCAPTCHA. Please try again.")
                    return render(request, 'site_pages/payment_options.html')
            except requests.exceptions.RequestException:
                # Network or API failure
                messages.error(request, "reCAPTCHA verification failed due to a network issue. Please try again.")
                return render(request, 'site_pages/payment_options.html')

            except ValueError:
                # JSON decoding failed
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

        user = authenticate(request, email = username, password = password)
        if user is not None:
            login(request,user)
            role = user.user_roles.first().role.name if user.user_roles.exists() else "No Role"
            # if role == "Student":
            #     return redirect('student_home')
            # elif role=="Church User":  
            #     return redirect('church_user_home')
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
                # Generate unique student ID
                student_id = f"STU{uuid.uuid4().hex[:8].upper()}"
                print("stud",student_id)
                
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
            messages.error(request, "reCAPTCHA verification failed. Please try again.")
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
                    
                    if not result.get('success'):
                        messages.error(request, "Invalid reCAPTCHA. Please try again.")
                        context = get_guest_context()
                        return render(request, 'site_pages/guest_register.html', context)
                        
                except requests.exceptions.RequestException:
                    messages.error(request, "reCAPTCHA verification failed due to a network issue. Please try again.")
                    context = get_guest_context()
                    return render(request, 'site_pages/guest_register.html', context)
                    
                except ValueError:
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
                # Generate unique church admin ID
                admin_id = f"CHA{uuid.uuid4().hex[:8].upper()}"
                
                # Validate required fields
                required_fields = ['register_as', 'church_code', 'associate_degree', 'first_name', 
                                 'last_name', 'email', 'phone_code', 'phone_number', 'date_of_birth', 
                                 'gender', 'mailing_address', 'city', 'state', 'country', 'zipcode', 
                                 'timezone', 'language', 'church_affiliation']
                missing_fields = []
                
                for field in required_fields:
                    if not request.POST.get(field):
                        missing_fields.append(field.replace('_', ' ').title())
                
                if missing_fields:
                    messages.error(request, f"Missing required fields: {', '.join(missing_fields)}")
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                
                # Validate church code
                church_code = request.POST.get('church_code')
                # try:
                #     church_code_obj = ChurchCodes.objects.get(code=church_code, status=True)
                # except ChurchCodes.DoesNotExist:
                #     messages.error(request, 'Invalid or inactive church code. Please contact support.')
                #     context = get_church_admin_context()
                #     return render(request, 'site_pages/church_admin_register.html', context)
                
                # Get language instance
                language_id = request.POST.get('language')
                try:
                    language = Languages.objects.get(id=language_id)
                except Languages.DoesNotExist:
                    messages.error(request, 'Invalid language selection.')
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                
                # # Check if email already exists
                # if ChurchAdmins.objects.filter(email=request.POST.get('email')).exists():
                #     messages.error(request, 'A church admin account with this email already exists.')
                #     context = get_church_admin_context()
                #     return render(request, 'site_pages/church_admin_register.html', context)
                
                # Check if email already exists in Users table
                if Users.objects.filter(email=request.POST.get('email')).exists():
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
                    
                    r = requests.post('https://www.google.com/recaptcha/api/siteverify', 
                                    data=data, timeout=5)
                    result = r.json()
                    
                    if not result.get('success'):
                        messages.error(request, "Invalid reCAPTCHA. Please try again.")
                        context = get_church_admin_context()
                        return render(request, 'site_pages/church_admin_register.html', context)
                        
                except requests.exceptions.RequestException:
                    messages.error(request, "reCAPTCHA verification failed due to a network issue. Please try again.")
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                    
                except ValueError:
                    messages.error(request, "Unexpected reCAPTCHA response. Please try again.")
                    context = get_church_admin_context()
                    return render(request, 'site_pages/church_admin_register.html', context)
                
                # Create church admin record
              
                church_admin = ChurchAdmins.objects.create(
                    student=None,  # or link to Students model if required
                    name_of_church=request.POST.get('name_of_church')or None,
                    name_of_paster=request.POST.get('name_of_paster')or None,
                    church_address=request.POST.get('church_address')or None,

                    church_code_id=request.POST.get('church_code')or None,
                    code=request.POST.get('church_code')or None,

                    amount=0.0,  
                    max_user_no=0,
                    current_user_no=0,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )                   
                
                # Generate random password
                password = get_random_string(10)              
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                # Create user record
                user = Users.objects.create(
                    name=f"{first_name} {last_name or ''}".strip(),
                    email=email,
                    username=admin_id,
                    church_admin=church_admin,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    is_active=False,                    
                )
                
                # Set hashed password
                user.set_password(password)
                user.save()
                
                # Send email
                try:
                    subject = "Your Church Admin Account Login Details"
                    message = f"""
                    Hello {first_name},

                    Your church admin account has been created successfully.

                    Login Details:
                    Email: {email}
                    Username: {admin_id}
                    Temporary Password: {password}
                    Church Code: {church_code}

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
                        messages.success(request, f'Church admin account created successfully! Login details sent to {church_admin.email}')
                        logger.info(f'Email sent successfully to {email}')
                    else:
                        messages.warning(request, 'Church admin account created but email could not be sent.')
                        logger.warning(f'Email failed to send to {email}')
                        
                except Exception as e:
                    messages.warning(request, f'Church admin account created but error sending email: {str(e)}')
                    logger.error(f'Email error: {str(e)}')
                
                return redirect('church_admin_registration_success', admin_id=admin_id)             
        
            
        except Languages.DoesNotExist:
            messages.error(request, 'Invalid language selection.')
            context = get_church_admin_context()
            return render(request, 'site_pages/church_admin_register.html', context)
            
        except ValueError as e:
            messages.error(request, f'Invalid data format: {str(e)}')
            context = get_church_admin_context()
            return render(request, 'site_pages/church_admin_register.html', context)
            
        except Exception as e:
            messages.error(request, f'An error occurred while submitting your registration. Please try again.')
            print(f"Error in church admin registration: {str(e)}")
            logger.error(f"Church admin registration error: {str(e)}")
            context = get_church_admin_context()
            return render(request, 'site_pages/church_admin_register.html', context)
    
    # GET request - display the form
    else:
        context = get_church_admin_context()
        return render(request, 'site_pages/church_admin_register.html', context)


def get_church_admin_context():
    """Helper function to get context for church admin registration form"""
    return {
        'languages': Languages.objects.filter(status=True) if hasattr(Languages, 'status') else Languages.objects.all(),
        'countries': Countries.objects.all(),
        'courses': Courses.objects.all(),
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY
    }


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