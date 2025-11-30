# -------------------------------
# Python Standard Library Imports
# -------------------------------
import os
import uuid
from datetime import datetime, timedelta
import logging
import requests

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
    Assignments,
    StudentsAssignment,
    Pages,
    Languages,
    Users,
    AdminPages
)



# Set up logger
logger = logging.getLogger(__name__)


def student_home(request):
    return render(request, "student/home.html")

def student_subjects(request):
    return render(request, "student/subjects.html")

def student_view_post(request):
    return render(request, "student/view_posts.html")

def student_exam_hall(request):
    return render(request, "student/exam_hall.html")

def student_score_card(request):
    return render(request, "student/score_card.html")

def student_class_recordings(request):
    return render(request, "student/class_recordings.html")

def student_submitted_assignment(request):
    return render(request, "student/submitted_assignment.html")


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
    context = {
        "pages_data": pages_data,
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


def new_admission_form(request):
    """
    New admission form for students with full error handling
    """
    
    # Debug logging
    logger.info(f"Request method: {request.method}")  
    # Determine the user (if logged in)
    user_obj = request.user if request.user.is_authenticated else None
    
    if request.method == "POST":
        logger.info(f"POST data received: {list(request.POST.keys())}")
        logger.info(f"FILES received: {list(request.FILES.keys())}")

        # -------------------------------
        # READ FORM DATA SAFELY
        # -------------------------------
        try:
            first_name = request.POST.get("first_name")
            middle_name = request.POST.get("middle_name")
            last_name = request.POST.get("last_name")            
            email = request.POST.get("email")
            gender = request.POST.get("gender")
            citizenship_str = request.POST.get("citizenship")
            phone_code = request.POST.get("country_code")
            phone = request.POST.get("phone")
            dob = request.POST.get("dob")
            marital_status = request.POST.get("marital_status")
            spouse_name = request.POST.get("spouse_name")
            children = request.POST.get("children")
            mailing_address = request.POST.get("mailing_address")
            city = request.POST.get("city")
            state = request.POST.get("state")
            country_str = request.POST.get("country")
            zipcode = request.POST.get("zipcode")
            timezone_str = request.POST.get("timezone")
            education = request.POST.get("education")
            course_str = request.POST.get("course")
            language = request.POST.get("language")
            starting_year = request.POST.get("start_year")
            ministerial_status = request.POST.get("ministerial_status")
            church = request.POST.get("church")
            scholarship = request.POST.get("scholarship")
            employed = request.POST.get("employed")
            income = request.POST.get("income")
            afford = request.POST.get("afford")
            message = request.POST.get("message")

            # References
            ref1_name = request.POST.get("ref1_name")
            ref1_email = request.POST.get("ref1_email")
            ref1_phone = request.POST.get("ref1_phone")
            ref2_name = request.POST.get("ref2_name")
            ref2_email = request.POST.get("ref2_email")
            ref2_phone = request.POST.get("ref2_phone")
            ref3_name = request.POST.get("ref3_name")
            ref3_email = request.POST.get("ref3_email")
            ref3_phone = request.POST.get("ref3_phone")

            logger.info("Form data read successfully")

        except Exception as e:
            logger.error(f"Error reading form fields: {e}", exc_info=True)
            messages.error(request, f"Error reading form fields: {e}")
            return render(request, "site_pages/new_admission_form.html")

        # -------------------------------
        # CONVERT STRING VALUES TO OBJECTS
        # -------------------------------
        try:         
            if children == '':
                children = None
            # Convert citizenship string to Country OBJECT
            citizenship_obj = None
            if citizenship_str:
                citizenship_name = citizenship_str.replace('_', ' ').title()
                citizenship_obj = Countries.objects.filter(name__iexact=citizenship_name).first()
                if citizenship_obj:
                    logger.info(f" Citizenship converted: {citizenship_str} -> {citizenship_obj.name} (ID: {citizenship_obj.id})")
                else:
                    logger.warning(f" Citizenship not found: {citizenship_str}")
            
            # Convert country string to Country OBJECT
            country_obj = None
            if country_str:
                country_name = country_str.replace('_', ' ').title()
                country_obj = Countries.objects.filter(name__iexact=country_name).first()
                if country_obj:
                    logger.info(f"Country converted: {country_str} -> {country_obj.name} (ID: {country_obj.id})")
                else:
                    logger.warning(f"Country not found: {country_str}")
            
            # Convert course string to Course OBJECT
            course_obj = None
            if course_str:
                try:
                    course_obj = Courses.objects.get(id=int(course_str))
                    logger.info(f"Course converted: {course_str} -> {course_obj.course_name} (ID: {course_obj.id})")
                except Courses.DoesNotExist:
                    logger.warning(f"Course not found: {course_str}")
                    messages.warning(request, f"Course '{course_str}' not found in database. Please contact admin.")

        except Exception as e:
            logger.error(f" Error converting values to objects: {e}", exc_info=True)
            messages.error(request, f"Error processing form data: {e}")
            return render(request, "site_pages/new_admission_form.html")

        # -------------------------------
        # FILE UPLOAD HANDLING
        # -------------------------------
        try:
            profile_pic = request.FILES.get("profile_pic")
            cert1 = request.FILES.get("cert1")
            cert2 = request.FILES.get("cert2")
            cert3 = request.FILES.get("cert3")
            cert4 = request.FILES.get("cert4")
            cert5 = request.FILES.get("cert5")
            
            logger.info(f"Files received - Profile: {bool(profile_pic)}, Certs: {bool(cert1)}, {bool(cert2)}, {bool(cert3)}, {bool(cert4)}, {bool(cert5)}")

        except Exception as e:
            logger.error(f" File upload error: {e}", exc_info=True)
            messages.error(request, f"File upload error: {e}")
            return render(request, "site_pages/new_admission_form.html")

        # Function to save file
        def save_file(f):
            try:
                if not f:
                    return None

                # Generate unique file name
                file_path = f"uploads/students/{get_random_string(8)}_{f.name}"
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Save file manually
                with open(full_path, "wb+") as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
                
                logger.info(f"File saved: {file_path}")
                return file_path

            except Exception as e:
                logger.error(f" Error saving file '{f.name}': {e}", exc_info=True)
                messages.error(request, f"Error saving file '{f.name}': {e}")
                return None

        # Try saving all files
        try:
            photo_path = save_file(profile_pic)
            c1 = save_file(cert1)
            c2 = save_file(cert2)
            c3 = save_file(cert3)
            c4 = save_file(cert4)
            c5 = save_file(cert5)
            
            logger.info("All files processed")

        except Exception as e:
            logger.error(f" Error processing uploaded files: {e}", exc_info=True)
            messages.error(request, f"Error processing uploaded files: {e}")
            return render(request, "site_pages/new_admission_form.html")

        # -------------------------------
        # LANGUAGE FOREIGN KEY
        # -------------------------------
        try:
            lang_obj = None
            if language:
                lang_obj = Languages.objects.filter(language_name__icontains=language).first()
                if lang_obj:
                    logger.info(f" Language lookup: {lang_obj.language_name} (ID: {lang_obj.id})")
                else:
                    logger.warning(f" Language not found: {language}")

        except Exception as e:
            logger.error(f" Language lookup error: {e}", exc_info=True)
            messages.error(request, f"Language lookup error: {e}")
            lang_obj = None

        # -------------------------------
        # GENERATE STUDENT ID
        # -------------------------------
        try:
            student_id = "STD-" + get_random_string(6).upper()
            logger.info(f"Generated student ID: {student_id}")
            
        except Exception as e:
            logger.error(f" Error generating student ID: {e}", exc_info=True)
            messages.error(request, f"Error generating student ID: {e}")
            student_id = "STD-000000"

        # -------------------------------
        # SAVE INTO DATABASE
        # -------------------------------
        try:
            student = Students.objects.create(
                student_id=student_id,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                user_id = user_obj,
                email=email,
                gender=gender,
                citizenship=citizenship_obj,  # Pass OBJECT not string/ID
                phone_code=phone_code.replace("+", "") if phone_code else None,
                phone_number=phone,
                date_of_birth=dob,
                mrital_status=marital_status,
                spouse_name=spouse_name,
                children=children,
                mailing_address=mailing_address,
                city=city,
                state=state,
                country=country_obj,  # Pass OBJECT not string/ID
                zip_code=zipcode,
                timezone=timezone_str,
                highest_education=education,
                course_applied=course_obj,  # Pass OBJECT not string/ID
                language_id=lang_obj,
                starting_year=starting_year,
                ministerial_status=ministerial_status,
                church_affiliation=church,
                scholarship_needed=scholarship,
                currently_employed=employed,
                income=income,
                affordable_amount=afford,
                message=message,

                # References
                reference_name1=ref1_name,
                reference_email1=ref1_email,
                reference_phone1=ref1_phone,

                reference_name2=ref2_name,
                reference_email2=ref2_email,
                reference_phone2=ref2_phone,

                reference_name3=ref3_name,
                reference_email3=ref3_email,
                reference_phone3=ref3_phone,

                # Files
                photo=photo_path,
                certificate1=c1,
                certificate2=c2,
                certificate3=c3,
                certificate4=c4,
                certificate5=c5,
            )
            
            logger.info(f"Student saved successfully!")
            logger.info(f"Database ID: {student.id}")
            logger.info(f"Student ID: {student.student_id}")
            logger.info(f"Name: {student.first_name} {student.last_name}")
            logger.info(f"Email: {student.email}")
            logger.info(f"Citizenship: {student.citizenship}")
            logger.info(f"Country: {student.country}")
            logger.info(f"Course: {student.course_applied}")

        except IntegrityError as e:
            logger.error(f" Database integrity error: {e}", exc_info=True)
            messages.error(request, f"Database integrity error: This email or student ID may already exist. {e}")
            return render(request, "site_pages/new_admission_form.html")
            
        except ValidationError as e:
            logger.error(f" Validation error: {e}", exc_info=True)
            messages.error(request, f"Validation error: {e}")
            return render(request, "site_pages/new_admission_form.html")
            
        except TypeError as e:
            logger.error(f"Type error (probably wrong data type): {e}", exc_info=True)
            messages.error(request, f"Data type error: {e}. Please check your form inputs.")
            return render(request, "site_pages/new_admission_form.html")
            
        except Exception as e:
            logger.error(f"Database save error: {e}", exc_info=True)
            messages.error(request, f"Database save error: {e}")
            return render(request, "site_pages/new_admission_form.html")

        # -------------------------------
        # SUCCESS
        # -------------------------------
        logger.info(f" Application submitted successfully for {first_name} {last_name}")
        messages.success(request, "Your application has been submitted successfully!")
        return redirect("new_admission_form")  # <--- POST/Redirect/GET

    # Default GET
    logger.info("Rendering new admission form (GET request)")
    return render(request, "site_pages/new_admission_form.html", {
        "countries": Countries.objects.all(),
        "courses": Courses.objects.all(),
        "languages": Languages.objects.all(),        
    })


def reference_form(request):
    # -------------------------------
    # Reference Details of the student
    # -------------------------------
    try:        
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
        return render(request, "site_pages/reference_form.html", {"countries": Countries.objects.all()})
    except Exception as e:
        logger.error(f"Error rendering reference form page: {e}", exc_info=True)
        messages.error(request, "Could not load the reference form page.")
        return render(request, "site_pages/reference_form.html")

def payment_options(request):
    return render(request,"site_pages/payment_options.html")


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
                    language_id=language,
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
    if request.method == "POST":

        # Get reCAPTCHA response from form
        recaptcha_response = request.POST.get('g-recaptcha-response')

        # Verify with Google
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        google_verify = requests.post(
            'https://www.google.com/recaptcha/api/siteverify', data=data
        )
        result = google_verify.json()
        print("*8888",settings.RECAPTCHA_SITE_KEY)
        if result.get('success'):
            print("✓ Human verified — continue saving form")
            return render(request,"site_pages/register.html" )
        else:
            print("✗ Invalid reCAPTCHA")
            return render(request, "site_pages/register.html", {
                "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY,
                "error": "Invalid CAPTCHA. Please try again."
            })

    return render(request, "site_pages/register.html", {
        "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY
    })
    
def admin_functions():
    print(AdminPages.objects.all())




@login_required
def student_index(request):
    try:
        student  = request.user.student
    except:
        student = None
    print(student,"--------------")
    return render(request, 'student/index.html')

def courses(request):
    courses = Courses.objects.filter(status=1).order_by('id')
    return render(request, 'site_pages/course_list.html', {'courses': courses})
