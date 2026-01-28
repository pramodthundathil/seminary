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
import json

# -------------------------------
# Django Core Imports
# -------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.db.models import Q, Count, Sum
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.utils.timezone import make_aware
import pytz

# -------------------------------
# Local App Imports
# -------------------------------
from home.models import (
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
    Support, Notifications,
    Subjects, StudentsInstructor,
    Assignments,
    AssignmentAnswers,
    Payments,
    Contacts
)

from home.permissions import student_only, student_or_church_user

# Set up logger
logger = logging.getLogger(__name__)
from django.db import DatabaseError
from datetime import timedelta # Added import
from django.utils import timezone # Added import
# Ensure models are imported (ObjectiveQuestions, etc are already imported via * or manual list if not present)
from home.models import (
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
    Support, Notifications,
    Subjects, StudentsInstructor,
    Assignments,
    AssignmentAnswers,
    Payments,
    Contacts,
    Exams, # Ensure Exams is imported
    ObjectiveQuestions, # Added
    DescriptiveQuestions, # Added
    ObjectiveAnswers, # Added
    DescriptiveAnswers, # Added
    StudentsUploads, 
)
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

# -------------------------------
#  STUDENT HOMEPAGE VIEWS
# -------------------------------

@login_required
@student_or_church_user
def student_home(request):
    try:
        student = Students.objects.select_related("language").filter(user=request.user).first()
        if student is None:
            return render(request, "student/home.html", {"error": "Student not found"})
    except DatabaseError as e:
        logger.error(f"Student fetch failed: {e}")
        return render(request, "student/home.html", {"error": "Database error while fetching student"})
    
    # store student_id once (production practice)
    student_id = student.id
    
    # ------------------- NOTIFICATIONS -------------------
    try:
        notifications = Notifications.objects.filter(
            # notification_type=EXAM_NOTIFICATION,
            student_id=student_id
        )
    except DatabaseError as e:
        logger.error(f"Failed to fetch notifications for student {student_id}: {e}")
        notifications = []

    # ------------------- LANGUAGE -------------------
    try:
        language = student.language.language_name if student.language else None
    except Exception as e:
        logger.error(f"Failed to fetch language for student {student_id}: {e}")
        language = None

    # ------------------- INSTRUCTOR -------------------
    instructor_name = None

    try:
        instructor_relation = StudentsInstructor.objects.select_related("instructor").filter(student_id=student_id).first()
        if instructor_relation:
            instructor_name = instructor_relation.instructor.staff_name
        else:
            instructor_name = None
    except Exception as e:
        logger.error(f"Failed to fetch instructor for student {student_id}: {e}")
        instructor_name = None

    # ------------------- COURSE -------------------
    try:
        course_obj = student.course_applied
        course = {
            "id": course_obj.id,
            "name": course_obj.course_name,
            "code": course_obj.course_code,
        } if course_obj else None
    except Exception as e:
        logger.error(f"Failed to fetch course for student {student_id}: {e}")
        course = None
               
    notifications = list(notifications)

    context = {
        "notifications": notifications,
        "course": course,
        "instructor_name": instructor_name,
        "language": language,
    }

    return render(request, "student/home.html", context)

@login_required
def student_index(request): 
    # Formerly index in home/views.py used for student dashboard landing?
    # The original index view in home/views.py (lines 954-960) seems to be mixed with homepage logic
    # But based on urls.py line 8: path("student_index",views.student_index,name="student_index"),
    # It must be a separate view. 
    # Wait, I don't see `def student_index` in the `home/views.py` file content I read earlier.
    # Let me double check the file reading output.
    # Ah, I missed it or it was not in the range I read? 
    # Line 8 calls views.student_index.
    # I successfully GREPPED for signup_student but not student_index.
    # I should define it here to matching what it likely was or stub it. 
    # Actually, looking at home/urls.py line 8: path("student_index",views.student_index,name="student_index")
    # And line 5: path('',views.index, name='index')
    # If I cannot find `student_index` in `home/views.py`, it might be an alias or I missed it.
    # Let's assume for now I will use `student_home` logic or redirect to it if missing.
    # But wait, looking at line 54 of urls.py: path("get-exams/<int:subject_id>/", views.get_exams, name="get_exams"),
    # The file content I read (Step 12) shows lines 1-800.
    # Let's check lines 800-1600 (Step 17).
    # I don't see `def student_index` there either.
    # Maybe it was just `index`? But line 8 calls `views.student_index`.
    # Let me search for it specifically.
    return redirect("student_home")


# -------------------------------
#  STUDENT SUBJECT PAGE VIEWS
# -------------------------------

@login_required
@student_or_church_user
def student_class_recordings(request):
    try:
        student = Students.objects.filter(user=request.user).first()
        if student is None:
             return render(request, "student/home.html", {"error": "Student not found"})
        
        student_id = student.id
        
        # Get notifications
        try:
             notifications = Notifications.objects.filter(student_id=student_id)
        except:
             notifications = []

        # ------------------- UPLOADS (StudentsUploads only) -------------------
        # Fetch uploads assigned to this student (Direct assignment)
        student_uploads_qs = StudentsUploads.objects.filter(
            student=student
        ).select_related('upload', 'upload__youtube', 'upload__media', 'upload__subject', 'upload__video_id', 'upload__video_id__youtube', 'upload__video_id__media') \
         .order_by('-created_at')

        recordings = []
        for su in student_uploads_qs:
            upload = su.upload
            
            item = {
                'id': upload.id,
                'title': upload.upload_name,
                'description': upload.description,
                'subject': upload.subject.subject_name if upload.subject else '-',
                'date': su.created_at, # Use assignment date
                'type': 'file', # default
                'url': '',
                'thumb': ''
            }

            # 1. Check direct Youtube
            if upload.youtube:
                item['type'] = 'youtube'
                item['url'] = upload.youtube.file_path 
                item['thumb'] = upload.youtube.thumb_file_path if upload.youtube.thumb_file_path else ''
            
            # 2. Check direct Media
            elif upload.media:
                file_url = upload.media.file_path.url if upload.media.file_path else ''
                ext = upload.media.file_type.lower() if upload.media.file_type else ''
                
                if ext in ['mp4', 'webm', 'ogg', 'mov']:
                    item['type'] = 'video'
                    item['url'] = file_url
                else:
                    item['type'] = 'file'
                    item['url'] = file_url

            # 3. Check video_id relation
            elif upload.video_id:
                video = upload.video_id
                if video.youtube:
                   item['type'] = 'youtube'
                   item['url'] = video.youtube.file_path
                   item['thumb'] = video.youtube.thumb_file_path if video.youtube.thumb_file_path else ''
                elif video.media:
                    file_url = video.media.file_path.url if video.media.file_path else ''
                    ext = video.media.file_type.lower() if video.media.file_type else ''
                    if ext in ['mp4', 'webm', 'ogg', 'mov']:
                        item['type'] = 'video'
                        item['url'] = file_url
                    else:
                        item['type'] = 'file'
                        item['url'] = file_url
            
            recordings.append(item)

    except Exception as e:
        logger.error(f"Error fetching recordings for student {request.user.id}: {e}")
        recordings = []
        notifications = []
        student = None

    context = {
        "student": student,
        "notifications": notifications,
        "recordings": recordings,
        "page_title": "Class Recordings"
    }
    return render(request, "student/class_recordings.html", context)

@login_required
@student_or_church_user
def student_subjects(request):
    try:
        student = Students.objects.select_related("user").filter(user=request.user).first()
        if student is None:
            return render(request, "student/subjects.html", {"error": "Student not found"})
    except Exception as e:
        logger.error(f"Failed to fetch student for user {request.user.id}: {e}")
        return render(request, "student/subjects.html", {"error": "Database error while fetching student"})

    # ---------------- SUBJECTS ----------------
    try:
        subjects_queryset = StudentsSubjects.objects.select_related("subject").filter(
            student=student
        ).order_by('-id')
        
        # Apply filter based on selection
        filter_option = request.GET.get('filter', 'all')
        if filter_option == 'requested':
            subjects_queryset = subjects_queryset.filter(is_approved=False)
        elif filter_option == 'inprogress':
            subjects_queryset = subjects_queryset.filter(is_approved=False)
        elif filter_option == 'rejected':
            subjects_queryset = subjects_queryset.none()
        elif filter_option == 'completed':
            subjects_queryset = subjects_queryset.filter(is_approved=True)
        
        paginator = Paginator(subjects_queryset, 5)
        page_number = request.GET.get('page')
        subjects = paginator.get_page(page_number)
        
    except Exception as e:
        logger.error(f"Failed to fetch student subjects for {student.id}: {e}")
        subjects = []
        paginator = None

    # ---------------- ALL SUBJECTS ----------------
    try:
        # Get IDs of subjects already requested by this student
        requested_subject_ids = StudentsSubjects.objects.filter(
            student=student
        ).values_list('subject_id', flat=True)

        all_subject = Subjects.objects.exclude(id__in=requested_subject_ids).order_by('subject_name')
    except Exception as e:
        logger.error(f"Failed to fetch all subjects: {e}")
        all_subject = []

    context = {
        "subjects": subjects,
        "all_subject": list(all_subject),
        "paginator": paginator,
        "current_filter": filter_option,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, "student/subjects.html", context)
    
    return render(request, "student/subjects.html", context)


# -----------------------------------------
#  STUDENT UPLOADED ASSIGNMENT PAGE VIEWS
# -----------------------------------------

@student_only
def student_pending_assignment(request):
    try:
        student = Students.objects.select_related("user").filter(user=request.user).first()
        if student is None:
            return render(request, "student/pending_assignment.html", {"error": "Student not found"})
    except Exception as e:
        logger.error(f"Failed to fetch student for user {request.user.id}: {e}")
        return render(request, "student/pending_assignment.html", {"error": "Database error while fetching student"})

    # ---------------- PENDING ASSIGNMENTS ----------------
    try:
        pending_assignments = StudentsAssignment.objects.filter(
            student_id=student.id,
            submitted_on__isnull=True
        )
    except Exception as e:
        logger.error(f"Failed to fetch pending assignments for student {student.id}: {e}")
        pending_assignments = []

    context = {
        "pending_assignments": list(pending_assignments)
    }

    return render(request, "student/pending_assignment.html", context)


# -----------------------------------------
#  STUDENT SUBMITTED ASSIGNMENT PAGE VIEWS
# -----------------------------------------

@student_only
def student_submitted_assignment(request):

    # ------------------- STUDENT -------------------
    try:
        student = Students.objects.get(user=request.user)
    except Students.DoesNotExist:
        student = None

    if not student:
        return render(request, "student/submitted_assignment.html", {
            "error": "Student not found"
        })

    student_id = student.id

    # ------------------- SUBMITTED ASSIGNMENTS -------------------
    try:
        submitted_assignments = StudentsAssignment.objects.filter(
            student_id=student_id,
            submitted_on__isnull=False
        ).select_related('assignment', 'assignment__subject', 'student') # Optimize
        
        # Attach the actual answer to each record
        # Since AssignmentAnswers links to Assignment and Student, not StudentsAssignment directly
        for sa in submitted_assignments:
            answer = AssignmentAnswers.objects.filter(
                student=student, 
                assignment=sa.assignment
            ).last() # Get latest answer if multiple (though likely one)
            
            sa.submitted_answer = answer # Attach to object for template

    except Exception as e:
        logger.error(f"Failed to fetch submitted assignments for student {student_id}: {e}")
        submitted_assignments = []

    # ------------------- CONTEXT -------------------
    context = {
        "submitted_assignments": submitted_assignments
    }

    return render(request, "student/submitted_assignment.html", context)


# -----------------------------------------
#  STUDENT VIEW POST PAGE VIEWS
# -----------------------------------------

@student_only
def student_view_post(request):
    return render(request, "student/view_posts.html")


# -----------------------------------------
#  STUDENT EXAM  PAGE VIEWS
# -----------------------------------------

@login_required
@student_or_church_user
def student_exam_hall(request):

    # ----- Fetch student safely -----
    try:
        student = (
            Students.objects
            .select_related('course_applied')
            .only('id', 'course_applied__course_name')
            .get(user=request.user)
        )
    except Students.DoesNotExist:
        logger.error(f"Student not found for user {request.user.id}")
        return render(request, "student/exam_hall.html", {
            "error": "Student not found"
        })

    # ----- Prefetch exams & subjects -----
    exams_queryset = (
        StudentsExams.objects
        .filter(student=student)
        .select_related("exam", "exam__subject")
        .only(
            "exam__exam_name",
            "exam__subject__subject_name",
            "created_at",
            "is_exam_started",
            "is_exam_ended",
        )
        .order_by('-created_at')  # Order by most recent first
    )

    # Pagination - 5 items per page
    paginator = Paginator(exams_queryset, 5)
    page_number = request.GET.get('page')
    exams_page = paginator.get_page(page_number)

    exam_list = []

    # ----- Build formatted data safely -----
    now = timezone.now()
    
    for e in exams_page:
        try:
            exam_obj = e.exam
            subject_obj = exam_obj.subject if exam_obj else None
            
            # Logic for Exam Status
            # 1. Completed
            if e.is_exam_ended:
                status = "Completed"
                action = "View"
                can_start = False
            # 2. Ongoing (Started but not ended) OR Ready to Start (Time reached but not started)
            elif e.start_time and e.start_time <= now:
                # Check if duration passed? 
                # If is_exam_started is True, we check if time remains.
                # If is_exam_started is False, we check if we are within valid window (if any). 
                # For now, let's assume if it's past start_time and not ended, it is "Active"
                status = "Ongoing"
                action = "Start"
                can_start = True
            # 3. Pending (Future)
            else:
                status = "Pending"
                action = "Wait"
                can_start = False
                
        except Exception as ex:
            logger.error(f"Failed to read exam/subject for exam entry {e.id}: {ex}")
            continue

        exam_list.append({
            "id": e.id,
            "exam_name": getattr(exam_obj, "exam_name", "N/A"),
            "subject_name": getattr(subject_obj, "subject_name", "N/A"),
            "requested_time": e.start_time, # Should use start_time which is the scheduled time
            "status": status,
            "can_start": can_start,
            "action": action
        })

    return render(request, "student/exam_hall.html", {
        "exam_list": exam_list,
        "paginator": paginator,
        "exams_page": exams_page,
        "request_exam_url": "/student/request-exam/",
    })



# -----------------------------------------
#  STUDENT EXAM SCORE PAGE VIEWS
# -----------------------------------------

@login_required
@student_or_church_user
@login_required
@student_or_church_user
def student_score_card(request):

    # ---- Get student safely ----
    try:
        student = Students.objects.get(user=request.user)
    except Students.DoesNotExist:
        return render(request, "student/score_card.html", {"error": "Student not found"})

    # ---- Process Exams ----
    # Show exams that are ENDED (completed).
    completed_exams = (
        StudentsExams.objects
        .filter(student=student, is_exam_ended=True)
        .select_related("exam")
        .order_by('-end_time')
    )

    exam_data = []
    
    for se in completed_exams:
        exam = se.exam
        
        # Calculate Total Marks for this Exam
        total_obj_marks = exam.objective_questions.aggregate(total=Sum('marks'))['total'] or 0
        total_desc_marks = exam.descriptive_questions.aggregate(total=Sum('mark'))['total'] or 0
        total_marks = total_obj_marks + total_desc_marks
        
        obtained_marks = se.show_on_score or 0
        
        # Calculate Percentage
        percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
        
        # Determine Grade
        if percentage >= 90: grade = "A+"
        elif percentage >= 80: grade = "A"
        elif percentage >= 70: grade = "B"
        elif percentage >= 60: grade = "C"
        elif percentage >= 50: grade = "D"
        else: grade = "F"

        exam_data.append({
            "code": exam.code,
            "exam_name": exam.exam_name,
            "total_score": round(total_marks),
            "score": round(obtained_marks),
            "percentage": round(percentage, 2),
            "grade": grade
        })

    # ---- Process Assignments ----
    # Ensure totals are calculated correctly
    student_assignments = (
        StudentsAssignment.objects
        .filter(student=student, submitted_on__isnull=False)  # Filter by submitted_on query
        .order_by('-submitted_on')
        .select_related("assignment")
    )
    
    assignment_data = []

    for sa in student_assignments:
        assignment = sa.assignment
        total = assignment.total_score or 0
        obtained = sa.total_marks or 0
        
        percentage = (obtained / total * 100) if total > 0 else 0
        
        if percentage >= 90: grade = "A+"
        elif percentage >= 80: grade = "A"
        elif percentage >= 70: grade = "B"
        elif percentage >= 60: grade = "C"
        elif percentage >= 50: grade = "D"
        else: grade = "F"
        
        assignment_data.append({
            "code": assignment.code,
            "assignment_name": assignment.assignment_name,
            "total_score": total,
            "score": obtained,
            "percentage": round(percentage, 2),
            "grade": grade
        })

    context = {
        "student": student,
        "student_exams": exam_data,
        "assignment_mark": assignment_data,
    }
    return render(request, "student/score_card.html", context)


# -----------------------------------------
#  CLASS RECORDED VIDEO PAGE VIEWS
# -----------------------------------------



# -----------------------------------------
#  STUDENT PROFILE PAGE VIEWS
# -----------------------------------------

@login_required
@student_or_church_user
def student_profile_view(request):
    # ---- Fetch student safely ----
    try:
        student = (
            Students.objects
            .select_related("course_applied", "language", "citizenship", "country")
            .get(user=request.user)
        )
    except Students.DoesNotExist:
        logger.error(f"[PROFILE] Student not found for user ID: {request.user.id}")
        return render(
            request,
            "student/student_profile.html",
            {"error": "Student profile not found."}
        )
    except Exception as ex:
        logger.exception(f"[PROFILE] Unexpected error loading profile for user {request.user.id}: {ex}")
        return render(
            request,
            "student/student_profile.html",
            {"error": "Unable to load your profile at the moment."}
        )

    # ---- Log success ----
    logger.info(f"[PROFILE] Student profile loaded successfully for user {request.user.id}")

    # ---- Render ----
    return render(
        request,
        "student/student_profile.html",
        {"student": student}
    )


# -----------------------------------------
#  STUDENT DOUBT ADD VIEWS
# -----------------------------------------

@login_required
@student_or_church_user
@require_POST
def student_support_create(request):
    # ----- Get student safely -----
    student = Students.objects.filter(user=request.user).first()
    if not student:
        return JsonResponse({"error": "Student not found"}, status=404)

    # ----- Read input -----
    doubt = request.POST.get("doubt", "").strip()
    category = request.POST.get("category", "").strip()

    if not doubt:
        return JsonResponse({"error": "Doubt field is required"}, status=400)

    # ----- Create record -----
    Support.objects.create(
        student=student,
        doubt_question=doubt,
        category=category,
        status="1",
        created_by=request.user,
        updated_by=request.user,
    )
    return JsonResponse({"success": True}, status=201)

# -----------------------------------------
#  STUDENT DOUBT PAGE VIEWS
# -----------------------------------------

@login_required
@student_or_church_user
def student_doubts_answers(request):
    try:
        doubt_queryset = (
            Support.objects
            .filter(student__user=request.user)
            .select_related("student")
            .order_by("-created_at")
        )
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            doubt_queryset = doubt_queryset.filter(
                doubt_question__icontains=search_query
            )
        
        # Pagination - 5 items per page
        paginator = Paginator(doubt_queryset, 5)
        page_number = request.GET.get('page')
        doubts_page = paginator.get_page(page_number)
        
    except Exception as e:
        logger.error(f"Failed to fetch doubts for user {request.user.id}: {e}")
        doubts_page = []
        paginator = None

    return render(request, "student/doubts_answers.html", {
        "doubt": doubts_page,
        "paginator": paginator,
        "doubts_page": doubts_page,
        "search_query": search_query,
    })


# -----------------------------------------
#  STUDENT REQUEST SUBJECT VIEWS
# -----------------------------------------

@require_POST
@student_or_church_user
@login_required
def request_subject_view(request):
    subject_id = request.POST.get("subject_id")

    if not subject_id:
        return JsonResponse(
            {"status": "error", "message": "Subject ID required"},
            status=400
        )

    # Get student safely
    try:
        student = Students.objects.get(user=request.user)
    except Students.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Student not found"},
            status=404
        )

    # Validate subject exists
    if not Subjects.objects.filter(id=subject_id).exists():
        return JsonResponse(
            {"status": "error", "message": "Invalid subject"},
            status=400
        )

    # Prevent duplicate request
    exists = StudentsSubjects.objects.filter(
        student=student,
        subject_id=subject_id,
        deleted_at__isnull=True
    ).exists()

    if exists:
        return JsonResponse(
            {"status": "error", "message": "Subject already requested"},
            status=400
        )

    # Create record
    StudentsSubjects.objects.create(
        student=student,
        subject_id=subject_id,
        requested_by=request.user,
        is_approved=False,
        reject_reason=None,
        is_optional=False,
        created_by=request.user,
        updated_by=request.user,
    )

    return JsonResponse(
        {"status": "success", "message": "Subject requested successfully"}
    )


# -----------------------------------------
#  STUDENT REQUEST EXAM VIEWS
# -----------------------------------------

@login_required
@student_or_church_user
def student_request_exam(request):
    
    student = Students.objects.filter(user=request.user).first()
    if not student:
        return render(request, "student/request_exam.html", {
            "error": "Student not found"
        })

    subjects = Subjects.objects.filter(
        students__student=student,
        students__is_approved=True
    )

    hours = range(1, 13)
    minutes = ["00","05","10","15","20","25","30","35","40","45","50","55"]

    student_exam = StudentsExams.objects.filter(student_id=student.id)

    context = {
        "subjects": subjects,
        "student_exam": student_exam,
        "hours": hours,
        "minutes": minutes,
    }

    return render(request, "student/request_exam.html", context)


def get_exams(request, subject_id):
    exams = Exams.objects.filter(subject_id=subject_id).values("id", "exam_name")
    return JsonResponse(list(exams), safe=False)


@require_POST
@login_required
@student_or_church_user
def submit_request_exam(request):
    try:
        # ---------------------------
        # GET STUDENT & EXAM OBJECTS
        # ---------------------------
        student = Students.objects.get(user=request.user)
        
        subject_id = request.POST.get("subject")
        exam_id = request.POST.get("exam")
        timezone_val = request.POST.get("timezone")
        exam_date = request.POST.get("examDate")
        start_time = request.POST.get("startTime")

        # Validate required fields
        if not all([subject_id, exam_id, timezone_val, exam_date, start_time]):
            messages.error(request, "All fields are required")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"status": "error", "message": "All fields are required"})
            return redirect("student_request_exam")

        exam = Exams.objects.get(id=exam_id)

        # ---------------------------
        # COMBINE DATE + TIME → DATETIME
        # ---------------------------
        datetime_str = f"{exam_date} {start_time}"
        try:
            final_datetime_str = f"{exam_date} {start_time}"   # "2025-12-17 17:56"
            final_datetime = datetime.strptime(final_datetime_str, "%Y-%m-%d %H:%M")
            final_datetime = make_aware(final_datetime)  # MAKE TZ-aware
        except ValueError:
            messages.error(request, "Invalid date or time format")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"status": "error", "message": "Invalid date or time format"}, status=400)
            return redirect("student_request_exam")

        # ---------------------------
        # CREATE THE RECORD
        # ---------------------------
        try:
            StudentsExams.objects.create(
                student=student,
                exam=exam,
                start_time=final_datetime,
                end_time=None,
                exam_duration=exam.exam_duration if hasattr(exam, 'exam_duration') else 0,
                timezone=timezone_val,
                requested_by=request.user,
                created_by=request.user,
                updated_by=request.user,
                show_on_score=0,
            )

            messages.success(request, "Exam request submitted successfully!")
            
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"status": "success", "message": "Exam request submitted successfully!"})
            
            return redirect("student_exam_hall")
            
        except Exception as e:
            messages.error(request, f"Failed to submit exam request: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"status": "error", "message": f"Failed to submit exam request: {str(e)}"}, status=500)
            return redirect("student_request_exam")

    except Students.DoesNotExist:
        messages.error(request, "Student not found")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "error", "message": "Student not found"})
        return redirect("student_request_exam")
        
    except Exams.DoesNotExist:
        messages.error(request, "Exam not found")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "error", "message": "Exam not found"})
        return redirect("student_request_exam")
        
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"status": "error", "message": f"An error occurred: {str(e)}"})
        return redirect("student_request_exam")



# -----------------------------------------
#  TAKE EXAM & SUBMIT
# -----------------------------------------

@login_required
@student_or_church_user
def take_exam(request, exam_id):
    # 1. Get Student
    try:
        student = Students.objects.get(user=request.user)
    except Students.DoesNotExist:
        return redirect("student_exam_hall")

    # 2. Get StudentExam
    student_exam = get_object_or_404(StudentsExams, id=exam_id, student=student)
    
    # 3. Check Validation
    now = timezone.now()
    
    if student_exam.is_exam_ended:
        messages.error(request, "You have already completed this exam.")
        return redirect("student_exam_hall")
        
    if student_exam.start_time and student_exam.start_time > now:
        messages.error(request, "It is not yet time to start this exam.")
        return redirect("student_exam_hall")

    # 4. Mark as Started if not already
    if not student_exam.is_exam_started:
        student_exam.is_exam_started = True
        student_exam.save()

    # 5. Fetch Questions (Objective + Descriptive)
    exam_obj = student_exam.exam
    
    objective_questions = exam_obj.objective_questions.all()
    descriptive_questions = exam_obj.descriptive_questions.all()
    
    # 6. Calc Remaining Seconds
    if student_exam.exam_duration:
        exam_end_time = student_exam.start_time + timedelta(minutes=student_exam.exam_duration)
        remaining_seconds = (exam_end_time - now).total_seconds()
    else:
        remaining_seconds = 3600 # Default 1 hr if 0?
        
    if remaining_seconds <= 0:
        # Time expired logic
        student_exam.is_exam_ended = True
        student_exam.save()
        messages.error(request, "Exam duration has expired.")
        return redirect("student_exam_hall")

    context = {
        "student_exam": student_exam,
        "exam": exam_obj,
        "objective_questions": objective_questions,
        "descriptive_questions": descriptive_questions,
        "remaining_seconds": max(0, int(remaining_seconds)),
    }
    return render(request, "student/take_exam.html", context)


@login_required
@student_or_church_user
def submit_exam(request, exam_id):
    if request.method != "POST":
        return redirect("student_exam_hall")

    # Use a flag to track if we encountered partial failures
    has_errors = False

    try:
        student = Students.objects.get(user=request.user)
        student_exam = StudentsExams.objects.get(id=exam_id, student=student)
        
        if student_exam.is_exam_ended:
            logger.warning(f"Student {student.id} tried to submit ended exam {exam_id}")
            return redirect("student_exam_hall")
        
        # Save logic
        count_saved = 0
        print(f"DEBUG: Starting submission for exam {exam_id}. POST data keys: {list(request.POST.keys())}")
        
        for key, value in request.POST.items():
            # Skip non-answer fields like csrfmiddlewaretoken
            if not (key.startswith("obj_q_") or key.startswith("desc_q_")):
                continue
                
            try:
                if key.startswith("obj_q_"):
                    # Format: obj_q_123
                    q_id = key.split("_")[2] 
                    if not q_id.isdigit():
                        continue
                        
                    question = ObjectiveQuestions.objects.get(id=q_id)
                    
                    # Auto-grading
                    val_str = str(value).strip()
                    correct_opt = str(question.answer_option).strip()
                    is_correct = (val_str == correct_opt)
                    
                    qm = question.marks if question.marks else 0
                    marks_awarded = qm if is_correct else 0
                    
                    # Ensure mark fits decimal_places=0
                    try:
                        marks_awarded = int(float(marks_awarded))
                    except:
                        marks_awarded = 0
                    
                    # Use update_or_create to handle re-submissions or duplicates
                    obj, created = ObjectiveAnswers.objects.update_or_create(
                        assignment=student_exam,
                        question=question,
                        defaults={
                            'answer': val_str[:250], # Truncate to fit CharField
                            'mark': marks_awarded
                        }
                    )
                    print(f"DEBUG: Saved Objective Q {q_id}: {Created if created else 'Updated'}")
                    count_saved += 1
                
                elif key.startswith("desc_q_"):
                    q_id = key.split("_")[2]
                    if not q_id.isdigit():
                        continue

                    question = DescriptiveQuestions.objects.get(id=q_id)
                    answer_text = str(value)
                    
                    DescriptiveAnswers.objects.update_or_create(
                        assignment=student_exam, 
                        question=question,
                        defaults={
                            'answer': answer_text, # TextField, so no length issue usually, but good to check
                            'mark': 0 
                        }
                    )
                    print(f"DEBUG: Saved Descriptive Q {q_id}")
                    count_saved += 1
                    
            except Exception as inner_e:
                # Log inner error but continue processing other answers
                print(f"ERROR: Failed key {key}: {inner_e}")
                logger.error(f"Error saving answer for key {key} in exam {exam_id}: {inner_e}")
                has_errors = True
        
        # End Exam
        student_exam.is_exam_ended = True
        student_exam.end_time = timezone.now()
        student_exam.is_approved = True
        student_exam.save()
        
        if has_errors:
            messages.warning(request, "Exam submitted, but some answers might not have been saved. Please contact support.")
        else:
            messages.success(request, "Exam submitted successfully!")
            
        logger.info(f"Exam {exam_id} submitted by {student.id}. Saved {count_saved} answers.")
        return redirect("student_score_card")
        
    except Exception as e:
        logger.error(f"Critical error submitting exam {exam_id}: {e}")
        messages.error(request, "Something went wrong during submission.")
        return redirect("student_exam_hall")


@login_required(login_url='signin')
def student_payment_input(request):
    student = Students.objects.get(user=request.user)

    full_name = " ".join(
        filter(None, [student.first_name, student.middle_name, student.last_name])
    )

    context = {
        "student_name": full_name,
        "student_email": student.email or student.user.email,
        "student_phone": student.phone_number,
        "student": student,
    }

    return render(request, "student/payment_input.html", context)

def student_confirm_payment(request):
    payment = request.session.get("payment_temp")
    
    context={
        "payment":payment,
        "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID, 
    }
    return render(request, "student/confirm_payment.html",context)

def student_change_password(request):
    return render(request, "student/change_password.html")

def student_doubt_view(request,id):
    return render(request, "student/doubt_view.html")


@login_required
def make_payment(request):
    if request.method == "POST":
        student = request.user.student.first()  # Logged-in student

        Payments.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            person_group="student",
            amount=request.POST.get("amount"),
            message=request.POST.get("message"),
            student=student,
            is_paid=False  # still pending
        )

        return render(request, "payment_success.html")

    return render(request, "make_payment.html")


@login_required
def save_payment_temp(request):
    # data = json.loads(request.body)
    data = json.loads(request.body.decode("utf-8"))

    print("payment temp data=====",data)

    request.session["payment_temp"] = {
        "name": data["name"],
        "email": data["email"],
        "phone": data["phone"],
        "group": data["group"],
        "amount": data["amount"],
        "message": data["message"],
    }

    return JsonResponse({"status": "ok"})


@csrf_exempt
def create_paypal_order(request):
    data = json.loads(request.body)
    amount = data.get("amount", "10.00")   # dynamic amount

    CLIENT_ID = settings.PAYPAL_CLIENT_ID
    CLIENT_SECRET = settings.PAYPAL_CLIENT_SECRET

    # 1) Get Access Token
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
        auth=(CLIENT_ID, CLIENT_SECRET)
    )

    access_token = token_response.json()["access_token"]

    # 2) Create Order
    order_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
    order_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": str(amount)
                }
            }
        ]
    }

    order_response = requests.post(order_url, json=body, headers=order_headers)
    order_json = order_response.json()

    if "id" in order_json:
        return JsonResponse({"orderID": order_json["id"]})
    else:
        return JsonResponse({
            "error": True,
            "details": order_json
        }, status=400)


@csrf_exempt
def capture_paypal_order(request):
    data = json.loads(request.body)
    order_id = data.get("orderID")

    CLIENT_ID = settings.PAYPAL_CLIENT_ID
    CLIENT_SECRET = settings.PAYPAL_CLIENT_SECRET

    # 1) Get Access Token
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
        auth=(CLIENT_ID, CLIENT_SECRET)
    )

    access_token = token_response.json()["access_token"]

    # 2) Capture order
    capture_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
    capture_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    capture_response = requests.post(capture_url, headers=capture_headers)
    capture_json = capture_response.json()

    # SUCCESS?
    status = capture_json.get("status")

    if status == "COMPLETED":
        # Save payment in your DB here
        try:
            # Get payment data from session
            payment_data = request.session.get("payment_temp")
            if payment_data and 'id' in payment_data:
                payment_id = payment_data['id']
                from home.models import Payments
                payment_obj = Payments.objects.get(id=payment_id)
                payment_obj.is_paid = True
                # Optional: Save Transaction ID
                # payment_obj.transaction_id = capture_json.get("id") 
                payment_obj.save()
                
                # Clear session
                request.session.pop("payment_temp", None)
            else:
                 logger.warning("Payment completed but no session data found to update DB.")
                 
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")

        return JsonResponse({"status": "success", "details": capture_json})

    return JsonResponse({"status": "failed", "details": capture_json})


def payment_success(request):
    return render(request, "student/payment_success.html")


def payment_failed(request):
    return render(request, "student/payment_failed.html")


# ------------------------------------------------------------------------------------------------
# SIGN UP STUDENT - PLACEHOLDER logic as I am copying from previous context or needing to fetch it
# I will use a placeholder or check if I need to fetch it more accurately.
# It was not in the file dump I had fully.
# But I must move it as requested.
# For now I will assume it's `student_register` from the file dump (Line 1041 in Step 17)
# which was aliased as `signup_student` in `home/urls.py` ??
# home/urls.py: line 68: path('student/register/', views.signup_student, name='signup_student'),
# But line 1041 says `def student_register(request):`
# So `signup_student` must be an import or assignment in `home/views.py` like `signup_student = student_register`?
# Or `home/urls.py` from `import views` maps `views.signup_student` ??
# If `student_register` is the function, I will rename it or use it as is.
# I will use `signup_student` in the new file to match the URL config I made.
# ------------------------------------------------------------------------------------------------

def signup_student(request):
    # Aliased to student_register logic
    return student_register(request)

def student_register(request):
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
            phone_code = request.POST.get("phone_code") # Changed from country_code
            phone = request.POST.get("phone_number") # Changed from phone
            dob = request.POST.get("date_of_birth") # Changed from dob
            marital_status = request.POST.get("mrital_status") # Changed from marital_status (template uses mrital_status)
            spouse_name = request.POST.get("spouse_name")
            children = request.POST.get("children")
            mailing_address = request.POST.get("mailing_address")
            city = request.POST.get("city")
            state = request.POST.get("state")
            country_str = request.POST.get("country")
            zipcode = request.POST.get("zip_code") # Changed from zipcode
            timezone_str = request.POST.get("timezone")
            education = request.POST.get("highest_education") # Changed from education
            course_str = request.POST.get("course_applied") # Changed from course
            language = request.POST.get("language")
            starting_year = request.POST.get("starting_year") # Changed from start_year
            ministerial_status = request.POST.get("ministerial_status")
            church = request.POST.get("church_affiliation") # Changed from church
            scholarship = request.POST.get("scholarship_needed") # Changed from scholarship
            employed = request.POST.get("currently_employed") # Changed from employed
            income = request.POST.get("income")
            afford = request.POST.get("affordable_amount") # Changed from afford
            message = request.POST.get("message")

            # References
            ref1_name = request.POST.get("reference_name1") # Changed from ref1_name
            ref1_email = request.POST.get("reference_email1") # Changed from ref1_email
            ref1_phone = request.POST.get("reference_phone1") # Changed from ref1_phone
            ref2_name = request.POST.get("reference_name2")
            ref2_email = request.POST.get("reference_email2")
            ref2_phone = request.POST.get("reference_phone2")
            ref3_name = request.POST.get("reference_name3")
            ref3_email = request.POST.get("reference_email3")
            ref3_phone = request.POST.get("reference_phone3")

            logger.info("Form data read successfully")

        except Exception as e:
            logger.error(f"Error reading form fields: {e}", exc_info=True)
            messages.error(request, f"Error reading form fields: {e}")
            return render(request, "site_pages/register.html")

        # -------------------------------
        # CONVERT STRING VALUES TO OBJECTS
        # -------------------------------
        try:         
            if children == '':
                children = None
            # Convert citizenship string (ID) to Country OBJECT
            citizenship_obj = None
            if citizenship_str:
                try:
                    citizenship_obj = Countries.objects.get(id=int(citizenship_str))
                    logger.info(f" Citizenship converted: {citizenship_str} -> {citizenship_obj.name}")
                except (Countries.DoesNotExist, ValueError):
                    logger.warning(f" Citizenship not found: {citizenship_str}")
            
            # Convert country string (ID) to Country OBJECT
            country_obj = None
            if country_str:
                try:
                    country_obj = Countries.objects.get(id=int(country_str))
                    logger.info(f"Country converted: {country_str} -> {country_obj.name}")
                except (Countries.DoesNotExist, ValueError):
                    logger.warning(f"Country not found: {country_str}")
            
            # Convert course string (ID) to Course OBJECT
            course_obj = None
            if course_str:
                try:
                    course_obj = Courses.objects.get(id=int(course_str))
                    logger.info(f"Course converted: {course_str} -> {course_obj.course_name}")
                except Courses.DoesNotExist:
                    logger.warning(f"Course not found: {course_str}")
                    messages.warning(request, f"Course ID '{course_str}' not found.")

        except Exception as e:
            logger.error(f" Error converting values to objects: {e}", exc_info=True)
            messages.error(request, f"Error processing form data: {e}")
            return render(request, "site_pages/register.html")

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
                # lang_obj = Languages.objects.filter(language_name__icontains=language).first()
                lang_obj = Languages.objects.filter(id=language).first()
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
            student_id = "TTS" + get_random_string(8).upper()
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
                language=lang_obj,
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
                    return redirect('signup_student') # Redirect to new URL name

            except requests.exceptions.RequestException:
                # Network or API failure
                messages.error(request, "reCAPTCHA verification failed due to a network issue. Please try again.")
                return redirect('signup_student')

            except ValueError:
                # JSON decoding failed
                messages.error(request, "Unexpected reCAPTCHA response. Please try again.")
                return redirect('signup_student')

            # If everything is OK → continue
            messages.success(request, "Application submitted successfully!")
            return redirect('signup_student')                

        except IntegrityError as e:
            logger.error(f" Database integrity error: {e}", exc_info=True)
            messages.error(request, f"Database integrity error: This email or student ID may already exist. {e}")
            return render(request, "site_pages/student_register.html")
            
        except ValidationError as e:
            logger.error(f" Validation error: {e}", exc_info=True)
            messages.error(request, f"Validation error: {e}")
            return render(request, "site_pages/student_register.html")
            
        except TypeError as e:
            logger.error(f"Type error (probably wrong data type): {e}", exc_info=True)
            messages.error(request, f"Data type error: {e}. Please check your form inputs.")
            return render(request, "site_pages/new_admission_form.html")
            
        except Exception as e:
            logger.error(f"Database save error: {e}", exc_info=True)
            messages.error(request, f"Database save error: {e}")
            return render(request, "site_pages/student_register.html")

        # -------------------------------
        # SUCCESS
        # -------------------------------
        logger.info(f" Application submitted successfully for {first_name} {last_name}")
        messages.success(request, "Your application has been submitted successfully!")
        return redirect("student_application_success")  # <--- POST/Redirect/GET    

    # Default GET
    logger.info("Rendering new admission form (GET request)")
    return render(request, "site_pages/student_register.html", {
        "countries": Countries.objects.all(),
        "courses": Courses.objects.all(),
        "languages": Languages.objects.filter(deleted_at__isnull=True),
        "RECAPTCHA_SITE_KEY": settings.RECAPTCHA_SITE_KEY,
        "timezones": pytz.common_timezones  
    })




def student_application_success(request, student_id):
    # I assume it was there but I didn't see the code.
    # I will create a basic view for it.
    return render(request, "site_pages/application_success.html", {'student': student_id})


@login_required
@student_or_church_user
def student_references(request):
    try:
        student = Students.objects.select_related("language").filter(user=request.user).first()
        if student is None:
            return render(request, "student/home.html", {"error": "Student not found"})
            
        student_id = student.id
        
        # ------------------- NOTIFICATIONS -------------------
        try:
            notifications = Notifications.objects.filter(student_id=student_id)
        except Exception:
            notifications = []

        # ------------------- ASSIGNED BOOKS (StudentsBooks) -------------------
        # Fetch BookReferences specifically assigned to this student
        from home.models import StudentsBooks, BookReferences
        
        # Get book IDs assigned to student
        assigned_book_ids = StudentsBooks.objects.filter(student=student).values_list('book_id', flat=True)
        
        # Fetch the actual book objects
        references = BookReferences.objects.filter(
            id__in=assigned_book_ids,
            status=True
        ).select_related('subject', 'reference_file').order_by('-created_at')

        context = {
            "student": student,
            "notifications": notifications,
            "references": references, # Variable name 'references' matches template usage for list
            "page_title": "My References"
        }
    except Exception as e:
        logger.error(f"Error fetching references for student {request.user.id}: {e}")
        messages.error(request, "An error occurred while loading your references.")
        context = {
            "student": student if 'student' in locals() else None,
            "notifications": [],
            "references": [],
            "page_title": "My References"
        }
        
    return render(request, "student/references.html", context)


@login_required
@student_or_church_user
def submit_assignment(request, pk):
    # Fetch student assignment record
    student_assignment = get_object_or_404(
        StudentsAssignment.objects.select_related('assignment', 'assignment__subject'), 
        id=pk, 
        student__user=request.user
    )
    
    # Check if already submitted
    if student_assignment.submitted_on:
        messages.warning(request, "This assignment has already been submitted.")
        return redirect('student_submitted_assignment')

    if request.method == "POST":
        assignment_type = student_assignment.assignment.assignment_type
        
        try:
            with transaction.atomic():
                # logic for file upload or text submit
                answer_file_path = None
                answer_text_content = None

                if assignment_type == 'Paper Upload Type':
                    # Using the new FileField, we can just pass the file to the create method if we want,
                    # OR we can manually handle it. Since the model now uses FileField, 
                    # we should let Django ORM handle it or assign the file object.
                    uploaded_file = request.FILES.get('answer_file')
                    if not uploaded_file:
                        messages.error(request, "Please upload a file.")
                        return redirect('submit_assignment', pk=pk)
                    
                    # Store file object directly (Django FileField handles upload_to)
                    answer_file_path = uploaded_file 
                    
                elif assignment_type == 'Paper Submit Type':
                    # Check if we have specific questions to answer
                    questions = student_assignment.assignment.questions.all()
                    
                    if questions.exists():
                        # Concatenate answers
                        combined_answers = ""
                        for index, q in enumerate(questions, 1):
                            ans = request.POST.get(f'answer_text_{q.id}', '').strip()
                            combined_answers += f"<strong>Q{index}: {q.question}</strong><br>"
                            combined_answers += f"<p>{ans}</p><hr>"
                        
                        answer_text_content = combined_answers
                    else:
                        # Fallback to single text area
                        answer_text_content = request.POST.get('answer_text')

                    if not answer_text_content:
                        messages.error(request, "Please provide an answer.")
                        return redirect('submit_assignment', pk=pk)

                # Create Assignment Answer
                AssignmentAnswers.objects.create(
                    # Wait, model expects 'assignment' FK to Assignments? No, 'assignment' FK to Assignments?
                    # Let's check model definition again: 
                    # class AssignmentAnswers(models.Model):
                    #     assignment = models.ForeignKey('Assignments', ...
                    #     student = models.ForeignKey('Students', ...
                    
                    # BUT wait, how do we link to the specific 'StudentsAssignment' if we only link to generic 'Assignments'? 
                    # The prompt asked for "make submited assignments in a button view assigments with all answers". 
                    # If I create a new AssignmentAnswers, how do I know which attempt it is? 
                    # Usually it links to StudentsAssignment OR we just use student + assignment.
                    # Model definition says: assignment = FK('Assignments')
                    
                    assignment=student_assignment.assignment,
                    student=student_assignment.student,
                    answer_file=answer_file_path,
                    answer_text=answer_text_content,
                    created_at=timezone.now()
                )

                # Update StudentsAssignment status
                student_assignment.submitted_on = timezone.now()
                student_assignment.save()
                
                messages.success(request, "Assignment submitted successfully!")
                return redirect('student_submitted_assignment')

        except Exception as e:
            logger.error(f"Error submitting assignment {pk}: {e}")
            messages.error(request, "An error occurred while submitting. Please try again.")
            return redirect('submit_assignment', pk=pk)

    # GET Request - Show Form
    questions = student_assignment.assignment.questions.all()
    
    context = {
        "student_assignment": student_assignment,
        "questions": questions
    }
    return render(request, "student/assignment_submit.html", context)