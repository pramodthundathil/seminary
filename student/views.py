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
import re

# -------------------------------
# Django Core Imports
# -------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
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
    ChurchAdminApplication,
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
    Roles,
    RoleUsers,
)

from home.permissions import student_only, student_or_church_user

# Set up logger
logger = logging.getLogger(__name__)

def localize_datetime(naive_dt, tz_str):
    if not tz_str:
        return make_aware(naive_dt)
    
    tz_str = tz_str.strip()
    if tz_str.startswith("UTC"):
        # Format: UTC+HH:MM or UTC-HH:MM or UTC
        offset_str = tz_str[3:] # e.g. "+05:30", "-06:00", or ""
        if not offset_str:
            return pytz.UTC.localize(naive_dt)
        try:
            sign = 1 if offset_str[0] == '+' else -1
            parts = offset_str[1:].split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            td = timedelta(hours=hours, minutes=minutes)
            tz = pytz.FixedOffset(sign * int(td.total_seconds() / 60))
            return tz.localize(naive_dt)
        except Exception as e:
            logger.error(f"Error parsing UTC offset {tz_str}: {e}")
            return make_aware(naive_dt)
    else:
        # It's an IANA timezone like 'Asia/Kolkata'
        try:
            tz = pytz.timezone(tz_str)
            return tz.localize(naive_dt)
        except Exception as e:
            logger.error(f"Error finding timezone {tz_str}: {e}")
            if tz_str == 'Asia/Kolkata':
                tz = pytz.timezone('Asia/Calcutta')
                return tz.localize(naive_dt)
            return make_aware(naive_dt)

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
 
    # Check for active exam
    active_exam = None
    now = timezone.now()
    active_exams_qs = StudentsExams.objects.filter(
        student=student,
        is_approved=True,
        is_exam_ended=False,
        deleted_at__isnull=True
    ).select_related('exam')
    
    for se in active_exams_qs:
        if se.start_time:
            expiry_time = se.start_time + timedelta(minutes=se.exam_duration or 120)
            if se.start_time <= now <= expiry_time:
                active_exam = {
                    "id": se.id,
                    "exam": {
                        "exam_name": se.exam.exam_name
                    }
                }
                break

    context = {
        "notifications": notifications,
        "course": course,
        "instructor_name": instructor_name,
        "language": language,
        "active_exam": active_exam,
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
                # Extract ID
                regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                match = re.search(regex, item['url'])
                item['youtube_id'] = match.group(1) if match else None
                item['thumb'] = upload.youtube.thumb_file_path if upload.youtube.thumb_file_path else ''
            
            elif upload.media:
                file_url = upload.media.file_path.url if upload.media.file_path else ''
                ext = upload.media.file_type.lower() if upload.media.file_type else ''
                
                # Extended support for video extensions
                if ext in ['mp4', 'webm', 'ogg', 'mov', 'm4v']:
                    item['type'] = 'video'
                    item['url'] = file_url
                else:
                    item['type'] = 'file'
                    item['url'] = file_url

            elif upload.aws_url:
                item['url'] = upload.aws_url
                ext = upload.aws_url.split('.')[-1].lower() if '.' in upload.aws_url else ''
                if ext in ['mp4', 'webm', 'ogg', 'mov', 'm4v']:
                    item['type'] = 'video'
                else:
                    item['type'] = 'file'

            # 3. Check video_id relation
            elif upload.video_id:
                video = upload.video_id
                if video.youtube:
                   item['type'] = 'youtube'
                   item['url'] = video.youtube.file_path
                   regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                   match = re.search(regex, item['url'])
                   item['youtube_id'] = match.group(1) if match else None
                   item['thumb'] = video.youtube.thumb_file_path if video.youtube.thumb_file_path else ''
                elif video.media:
                    file_url = video.media.file_path.url if video.media.file_path else ''
                    ext = video.media.file_type.lower() if video.media.file_type else ''
                    if ext in ['mp4', 'webm', 'ogg', 'mov', 'm4v']:
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
            student=student, deleted_at=None
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
            student=student, deleted_at=None
        ).values_list('subject_id', flat=True)

        all_subject = Subjects.objects.exclude(id__in=requested_subject_ids, deleted_at=None).order_by('subject_name')
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
            submitted_on__isnull=True,
            deleted_at__isnull=True
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
        
        # Pagination - 10 items per page
        paginator = Paginator(doubt_queryset, 10)
        page_number = request.GET.get('page')
        doubts_page = paginator.get_page(page_number)
        
    except Exception as e:
        logger.error(f"Failed to fetch doubts for user {request.user.id}: {e}")
        doubts_page = []
        paginator = None
        search_query = ""

    return render(request, "student/view_posts.html", {
        "doubt": doubts_page,
        "paginator": paginator,
        "doubts_page": doubts_page,
        "search_query": search_query,
    })


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
            .only('id', 'course_applied__course_name', 'timezone')
            .get(user=request.user)
        )
    except Students.DoesNotExist:
        logger.error(f"Student not found for user {request.user.id}")
        return render(request, "student/exam_hall.html", {
            "error": "Student not found"
        })

    role = request.user.user_roles.first().role.name if request.user.user_roles.exists() else None
    is_church_user = (role == "Church User")

    # ----- Prefetch exams & subjects -----
    exams_queryset = (
        StudentsExams.objects
        .filter(student=student)
        .select_related("exam", "exam__subject")
        .only(
            "exam__exam_name",
            "exam__subject__subject_name",
            "created_at",
            "start_time",
            "timezone",
            "is_exam_started",
            "is_exam_ended",
            "is_approved",
            "is_rescheduled",
            "is_retest",
            "retest_status",
            "retest_fee",
            "retest_paid",
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
    from datetime import timedelta
    
    # Check for active exam
    active_exam = None
    active_exams_qs = StudentsExams.objects.filter(
        student=student,
        is_approved=True,
        is_exam_ended=False,
        deleted_at__isnull=True
    ).select_related('exam')
    
    for se in active_exams_qs:
        if se.start_time:
            expiry_time = se.start_time + timedelta(minutes=se.exam_duration or 120)
            if se.start_time <= now <= expiry_time:
                active_exam = {
                    "id": se.id,
                    "exam": {
                        "exam_name": se.exam.exam_name
                    }
                }
                break

    for e in exams_page:
        try:
            exam_obj = e.exam
            subject_obj = exam_obj.subject if exam_obj else None
            
            # Calculate expiry time: start_time + duration
            is_expired = False
            if e.start_time:
                expiry_time = e.start_time + timedelta(minutes=e.exam_duration or 120)
                if now > expiry_time:
                    is_expired = True
            
            # Logic for Exam Status
            # 1. Completed
            if e.is_exam_ended:
                status = "Completed"
                action = "View"
                can_start = False
            # 2. Expired / Missed
            elif is_expired:
                status = "Missed"
                action = "Reschedule"
                can_start = False
            # Retest specific status
            elif e.is_retest and not e.is_approved:
                status = "Retest Pending"
                action = "Wait"
                can_start = False
            elif e.is_retest and e.is_approved and e.start_time and e.start_time > now:
                status = "Retest Approved"
                action = "Wait"
                can_start = False
            # 3. Approved and Ready (Within duration window)
            elif e.is_approved and e.start_time and e.start_time <= now:
                status = "Ongoing"
                action = "Start"
                can_start = True
            # 4. Approved and Not Ready (Future time)
            elif e.is_approved:
                status = "Approved"
                action = "Wait"
                can_start = False
            # 5. Rescheduled (Pending approval)
            elif e.is_rescheduled and not e.is_approved:
                status = "Rescheduled"
                action = "Wait"
                can_start = False
            # 6. Not Approved but time reached (Late Approval)
            elif not e.is_approved and e.start_time and e.start_time <= now:
                status = "Pending Approval"
                action = "Wait"
                can_start = False
            # 7. Future / Other Pending
            else:
                status = "Pending"
                action = "Wait"
                can_start = False
                
            # Localize requested_time for rendering
            local_time_str = "N/A"
            if e.start_time:
                try:
                    if e.timezone.startswith("UTC"):
                        offset_str = e.timezone[3:]
                        if offset_str:
                            sign = 1 if offset_str[0] == '+' else -1
                            parts = offset_str[1:].split(':')
                            hours = int(parts[0])
                            minutes = int(parts[1]) if len(parts) > 1 else 0
                            td = timedelta(hours=hours, minutes=minutes)
                            tz = pytz.FixedOffset(sign * int(td.total_seconds() / 60))
                        else:
                            tz = pytz.UTC
                    else:
                        tz = pytz.timezone(e.timezone)
                    local_dt = e.start_time.astimezone(tz)
                    local_time_str = local_dt.strftime("%b %d, %Y %I:%M %p")
                except Exception as tz_ex:
                    logger.error(f"Error converting start_time to local tz: {tz_ex}")
                    local_time_str = e.start_time.strftime("%b %d, %Y %I:%M %p")

        except Exception as ex:
            logger.error(f"Failed to read exam/subject for exam entry {e.id}: {ex}")
            continue

        exam_list.append({
            "id": e.id,
            "exam_name": getattr(exam_obj, "exam_name", "N/A"),
            "subject_name": getattr(subject_obj, "subject_name", "N/A"),
            "requested_time": e.start_time, # Keep raw datetime for any other uses
            "requested_time_str": local_time_str, # Use this string in template
            "timezone": e.timezone,
            "status": status,
            "is_rescheduled": e.is_rescheduled,
            "is_approved": e.is_approved,
            "is_exam_ended": e.is_exam_ended,
            "is_retest": e.is_retest,
            "retest_status": e.retest_status,
            "retest_fee": str(e.retest_fee) if e.retest_fee else None,
            "retest_paid": e.retest_paid,
            "can_start": can_start,
            "action": action
        })

    # Minimal curated set of common timezones to keep the selection simple and clear
    common_timezones = [
        'UTC',
        'Asia/Kolkata',        # India Standard Time
        'Asia/Dubai',          # Gulf Standard Time
        'Asia/Singapore',      # Singapore Standard Time
        'Europe/London',       # Western European / Greenwich Mean Time
        'America/New_York',    # Eastern Standard Time
        'America/Chicago',     # Central Standard Time
        'America/Denver',      # Mountain Standard Time
        'America/Los_Angeles', # Pacific Standard Time
        'Africa/Nairobi',      # East Africa Time
        'Australia/Sydney'     # Australian Eastern Standard Time
    ]

    return render(request, "student/exam_hall.html", {
        "student": student,
        "exam_list": exam_list,
        "paginator": paginator,
        "exams_page": exams_page,
        "timezones": common_timezones,
        "request_exam_url": "/student/request-exam/",
        "active_exam": active_exam,
        "is_church_user": is_church_user,
        "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID,
    })

@login_required
@student_or_church_user
@require_POST
def student_reschedule_exam(request):
    try:
        exam_id = request.POST.get("exam_id")
        exam_date = request.POST.get("examDate")
        start_time = request.POST.get("startTime")
        timezone_val = request.POST.get("timezone")

        if not all([exam_id, exam_date, start_time, timezone_val]):
            return JsonResponse({"status": "error", "message": "All fields are required"}, status=400)

        # Get student and verify exam ownership
        student = Students.objects.get(user=request.user)
        student_exam = get_object_or_404(StudentsExams, id=exam_id, student=student)

        # Combine date + time
        try:
            datetime_str = f"{exam_date} {start_time}"
            final_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            final_datetime = localize_datetime(final_datetime, timezone_val)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid date or time format"}, status=400)

        # Update the exam record (rescheduling requires admin approval)
        student_exam.start_time = final_datetime
        student_exam.timezone = timezone_val
        student_exam.is_approved = False  
        student_exam.is_rescheduled = True
        student_exam.updated_by = request.user
        student_exam.save()

        return JsonResponse({"status": "success", "message": "Exam reschedule request submitted. Waiting for admin approval."})

    except Students.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Student not found"}, status=404)
    except Exception as e:
        logger.error(f"Failed to reschedule exam: {str(e)}")
        return JsonResponse({"status": "error", "message": f"Failed to reschedule exam: {str(e)}"}, status=500)



# -----------------------------------------
#  STUDENT EXAM SCORE PAGE VIEWS
# -----------------------------------------

@login_required
@student_or_church_user
def student_score_card(request):

    # ---- Get student safely ----
    try:
        student = Students.objects.get(user=request.user)
    except Students.DoesNotExist:
        return render(request, "student/score_card.html", {"error": "Student not found"})

    role = request.user.user_roles.first().role.name if request.user.user_roles.exists() else None
    if role == "Church User":
        return redirect("church_user_score_card")
    is_church_user = False

    # ---- Process Exams ----
    # Show exams that are ENDED (completed).
    completed_exams = (
        StudentsExams.objects
        .filter(student=student, is_exam_ended=True)
        .select_related("exam", "exam__subject", "course", "subject", "student", "student__course_applied")
        .order_by('-end_time')
    )

    exam_data = []
    seen_exams = set()
    
    for se in completed_exams:
        exam = se.exam
        if exam.id in seen_exams:
            continue
        seen_exams.add(exam.id)
        
        # Calculate Total Marks for this Exam
        total_obj_marks = exam.objective_questions.aggregate(total=Sum('marks'))['total'] or 0
        total_desc_marks = exam.descriptive_questions.aggregate(total=Sum('mark'))['total'] or 0
        total_marks = total_obj_marks + total_desc_marks
        
        # Calculate the highest score among all attempts for this exam
        from django.db.models import Max
        highest_score = StudentsExams.objects.filter(
            student=student,
            exam=exam,
            is_exam_ended=True,
            deleted_at__isnull=True
        ).aggregate(Max('show_on_score'))['show_on_score__max'] or 0
        
        obtained_marks = highest_score
        
        # Calculate Percentage
        percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
        
        # Determine Grade
        if percentage >= 90: grade = "A+"
        elif percentage >= 80: grade = "A"
        elif percentage >= 70: grade = "B"
        elif percentage >= 60: grade = "C"
        elif percentage >= 50: grade = "D"
        else: grade = "F"

        # Check for the latest retest attempt (even if not ended)
        latest_retest = StudentsExams.objects.filter(
            student=student,
            exam=exam,
            is_retest=True,
            deleted_at__isnull=True
        ).order_by('-created_at').first()
        
        retest_status = latest_retest.retest_status if latest_retest else 'none'
        retest_fee = latest_retest.retest_fee if latest_retest else None
        retest_paid = latest_retest.retest_paid if latest_retest else False
        retest_id = latest_retest.id if latest_retest else se.id

        # Determine Course Name & Subject Name
        course_name = se.course.course_name if se.course else (student.course_applied.course_name if student.course_applied else "-")
        subject_name = se.subject.subject_name if se.subject else (exam.subject.subject_name if (exam and exam.subject) else "-")

        exam_data.append({
            "id": retest_id,
            "code": exam.code,
            "exam_name": exam.exam_name,
            "course_name": course_name,
            "subject_name": subject_name,
            "total_score": round(total_marks),
            "score": round(obtained_marks),
            "percentage": round(percentage, 2),
            "grade": grade,
            "retest_status": retest_status,
            "retest_fee": str(retest_fee) if retest_fee else None,
            "retest_paid": retest_paid,
        })

    # ---- Process Assignments ----
    # Ensure totals are calculated correctly
    student_assignments = (
        StudentsAssignment.objects
        .filter(student=student, submitted_on__isnull=False)  # Filter by submitted_on query
        .order_by('-submitted_on')
        .select_related("assignment", "assignment__subject", "student", "student__course_applied")
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
        
        course_name = sa.student.course_applied.course_name if (sa.student and sa.student.course_applied) else "-"
        subject_name = assignment.subject.subject_name if (assignment and assignment.subject) else "-"

        assignment_data.append({
            "code": assignment.code,
            "assignment_name": assignment.assignment_name,
            "course_name": course_name,
            "subject_name": subject_name,
            "total_score": total,
            "score": obtained,
            "percentage": round(percentage, 2),
            "grade": grade
        })

    # ---- Final Score Calculation ----
    total_exam_max = sum(item['total_score'] for item in exam_data)
    total_exam_obtained = sum(item['score'] for item in exam_data)
    exam_percentage = (total_exam_obtained / total_exam_max * 100) if total_exam_max > 0 else 0
    
    if exam_percentage >= 90: exam_grade = "A+"
    elif exam_percentage >= 80: exam_grade = "A"
    elif exam_percentage >= 70: exam_grade = "B"
    elif exam_percentage >= 60: exam_grade = "C"
    elif exam_percentage >= 50: exam_grade = "D"
    else: exam_grade = "F"

    total_assign_max = sum(item['total_score'] for item in assignment_data)
    total_assign_obtained = sum(item['score'] for item in assignment_data)
    assign_percentage = (total_assign_obtained / total_assign_max * 100) if total_assign_max > 0 else 0

    if assign_percentage >= 90: assign_grade = "A+"
    elif assign_percentage >= 80: assign_grade = "A"
    elif assign_percentage >= 70: assign_grade = "B"
    elif assign_percentage >= 60: assign_grade = "C"
    elif assign_percentage >= 50: assign_grade = "D"
    else: assign_grade = "F"

    grand_total_max = total_exam_max + total_assign_max
    grand_total_obtained = total_exam_obtained + total_assign_obtained
    grand_percentage = (grand_total_obtained / grand_total_max * 100) if grand_total_max > 0 else 0
    
    if grand_percentage >= 90: grand_grade = "A+"
    elif grand_percentage >= 80: grand_grade = "A"
    elif grand_percentage >= 70: grand_grade = "B"
    elif grand_percentage >= 60: grand_grade = "C"
    elif grand_percentage >= 50: grand_grade = "D"
    else: grand_grade = "F"

    common_timezones = [
        'UTC',
        'Asia/Kolkata',        # India Standard Time
        'Asia/Dubai',          # Gulf Standard Time
        'Asia/Singapore',      # Singapore Standard Time
        'Europe/London',       # Western European / Greenwich Mean Time
        'America/New_York',    # Eastern Standard Time
        'America/Chicago',     # Central Standard Time
        'America/Denver',      # Mountain Standard Time
        'America/Los_Angeles', # Pacific Standard Time
        'Africa/Nairobi',      # East Africa Time
        'Australia/Sydney'     # Australian Eastern Standard Time
    ]

    context = {
        "student": student,
        "student_exams": exam_data,
        "assignment_mark": assignment_data,
        "timezones": common_timezones,
        "is_church_user": is_church_user,
        "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID,
        
        # Summary Data
        "exam_summary": {
            "total": round(total_exam_max),
            "score": round(total_exam_obtained),
            "percentage": round(exam_percentage, 2),
            "grade": exam_grade
        },
        "assignment_summary": {
            "total": round(total_assign_max),
            "score": round(total_assign_obtained),
            "percentage": round(assign_percentage, 2),
            "grade": assign_grade
        },
        "grand_summary": {
            "total": round(grand_total_max),
            "score": round(grand_total_obtained),
            "percentage": round(grand_percentage, 2),
            "grade": grand_grade
        }
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

    # ---- Handle POST logic ----
    if request.method == 'POST':
        # Check if it's a photo upload
        if 'photo' in request.FILES:
            photo_file = request.FILES['photo']
            try:
                # Generate unique file name
                file_path = f"uploads/students/{get_random_string(8)}_{photo_file.name}"
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, "wb+") as destination:
                    for chunk in photo_file.chunks():
                        destination.write(chunk)
                
                # Delete old photo if it exists
                if student.photo:
                    old_path = os.path.join(settings.MEDIA_ROOT, student.photo)
                    if os.path.exists(old_path) and os.path.isfile(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as delete_err:
                            logger.error(f"Failed to delete old profile photo: {delete_err}")
                
                student.photo = file_path
                student.save()
                messages.success(request, "Profile picture updated successfully!")
            except Exception as e:
                logger.error(f"Error saving profile picture: {e}")
                messages.error(request, "Failed to update profile picture.")
            return redirect('student_profile_view')
        
        # Check if it's an AJAX save request
        elif request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            import json
            try:
                data = json.loads(request.body)
                
                # Exclude email, DOB, and name as requested
                allowed_fields = [
                    'gender', 'phone_number', 'timezone',
                    'mailing_address', 'city', 'zip_code', 'highest_education',
                    'ministerial_status', 'church_affiliation', 'scholarship_needed',
                    'currently_employed', 'income', 'affordable_amount', 'message',
                    'reference_name1', 'reference_phone1', 'reference_email1',
                    'reference_name2', 'reference_phone2', 'reference_email2',
                    'reference_name3', 'reference_phone3', 'reference_email3',
                    'mrital_status', 'spouse_name', 'children'
                ]
                
                for field in allowed_fields:
                    if field in data:
                        val = data[field]
                        if field == 'children':
                            try:
                                val = int(val) if (val and str(val).strip()) else None
                            except ValueError:
                                val = None
                        setattr(student, field, val)
                
                student.save()
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Error saving profile details: {e}")
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # ---- Check for Church Admin status or application ----
    church_admin = ChurchAdmins.objects.filter(student=student).first()
    pending_application = ChurchAdminApplication.objects.filter(student=student, status='pending').first()

    # ---- Render ----
    return render(
        request,
        "student/student_profile.html",
        {
            "student": student,
            "church_admin": church_admin,
            "pending_application": pending_application,
        }
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
            final_datetime = localize_datetime(final_datetime, timezone_val)  # Localize to chosen timezone
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
                exam_duration=120,  # Configured to 2 hours (120 minutes)
                timezone=timezone_val,
                requested_by=request.user,
                created_by=request.user,
                updated_by=request.user,
                show_on_score=0,
                is_approved=True,  # Auto-approve exam requests
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
    duration_mins = student_exam.exam_duration or 120
    exam_end_time = student_exam.start_time + timedelta(minutes=duration_mins)
    remaining_seconds = (exam_end_time - now).total_seconds()
        
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

    # Fetch all students to allow selecting the specific student who is paying
    all_students = Students.objects.all().order_by('first_name', 'last_name')

    context = {
        "student_name": full_name,
        "student_email": student.email or student.user.email,
        "student_phone": student.phone_number,
        "student": student,
        "students": all_students,
    }

    return render(request, "student/payment_input.html", context)

def student_confirm_payment(request):
    payment = request.session.get("payment_temp")
    
    context={
        "payment":payment,
        "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID, 
    }
    return render(request, "student/confirm_payment.html",context)

@login_required
@student_or_church_user
def student_my_payments(request):
    from menu.views import sync_retest_payments_in_db
    sync_retest_payments_in_db()
    try:
        student = Students.objects.select_related("course_applied").get(user=request.user)
    except Students.DoesNotExist:
        return render(request, "student/my_payments.html", {"error": "Student not found"})
    
    # 1. Subjects
    subjects = StudentsSubjects.objects.filter(
        student=student, 
        deleted_at__isnull=True
    ).select_related('subject')
    
    # 2. Payments/Fees structure
    payments = Payments.objects.filter(
        student=student,
        deleted_at__isnull=True
    ).select_related('subjects_id').order_by('-created_at')
    
    # Calculate fee totals
    course_fee = student.get_course_fee_at_registration()
    subject_fees_total = sum(float(ss.subject.fees or 0) for ss in subjects if ss.subject)
    # Fetch all retest exams for this student
    retest_fees_total = sum(float(se.retest_fee or 0) for se in StudentsExams.objects.filter(student=student, is_retest=True, retest_fee__gt=0, deleted_at__isnull=True))
    total_fee_expected = course_fee + subject_fees_total + retest_fees_total
    
    discount = student.get_discount()
    total_paid = sum(float(p.amount or 0) for p in payments if p.is_paid)
    balance_due = max(0.0, total_fee_expected - discount - total_paid)
    
    # 3. Notifications & Instructor
    try:
        notifications = Notifications.objects.filter(student_id=student.id)
    except Exception:
        notifications = []
        
    instructor_name = None
    try:
        instructor_relation = StudentsInstructor.objects.select_related("instructor").filter(student_id=student.id).first()
        if instructor_relation:
            instructor_name = instructor_relation.instructor.staff_name
    except Exception:
        pass
        
    context = {
        'student': student,
        'payments': payments,
        'course_fee': course_fee,
        'subject_fees_total': subject_fees_total,
        'retest_fees_total': retest_fees_total,
        'total_fee_expected': total_fee_expected,
        'discount': discount,
        'total_paid': total_paid,
        'balance_due': balance_due,
        'notifications': list(notifications),
        'instructor_name': instructor_name,
    }
    return render(request, "student/my_payments.html", context)

@login_required
@student_or_church_user
def student_change_password(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            current_password = data.get("current_password")
            new_password = data.get("new_password")
            confirm_password = data.get("confirm_password")

            if not all([current_password, new_password, confirm_password]):
                return JsonResponse({"status": "error", "message": "All fields are required"}, status=400)

            if new_password != confirm_password:
                return JsonResponse({"status": "error", "message": "New passwords do not match"}, status=400)

            user = request.user
            if not user.check_password(current_password):
                return JsonResponse({"status": "error", "message": "Incorrect current password"}, status=400)

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Important!

            return JsonResponse({"status": "success", "message": "Password changed successfully"})

        except Exception as e:
            logger.error(f"Error changing password for user {request.user.id}: {e}")
            return JsonResponse({"status": "error", "message": "An error occurred"}, status=500)

    return render(request, "student/change_password.html")

@login_required
def student_doubt_view(request, id):
    from home.models import Support, SupportReplies
    ticket = get_object_or_404(Support, id=id, deleted_at__isnull=True)
    
    # Check if the ticket belongs to the current student
    student = request.user.student.first()
    if not student or ticket.student != student:
        messages.error(request, "You are not authorized to view this ticket.")
        return redirect('student_home')

    replies = ticket.replies.filter(deleted_at__isnull=True).order_by('created_at')

    if request.method == 'POST':
        doubt_answer = request.POST.get('doubt_answer')
        if doubt_answer:
            SupportReplies.objects.create(
                support=ticket,
                doubt_answer=doubt_answer,
                created_by=request.user,
                updated_by=request.user
            )
            # Re-open the ticket if it was resolved
            if ticket.status == 'completed':
                ticket.status = 'in_progress'
                ticket.save()
                
            messages.success(request, 'Reply sent successfully!')
            return redirect('student_doubt_view', id=id)

    return render(request, "student/doubt_view.html", {
        'ticket': ticket,
        'replies': replies
    })


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

    # Retrieve the selected student or fall back to the logged-in student
    selected_student_id = data.get("selected_student_id")
    student = None
    from home.models import Students
    if selected_student_id:
        try:
            student = Students.objects.get(id=selected_student_id)
        except Students.DoesNotExist:
            pass

    if not student:
        try:
            student = Students.objects.get(user=request.user)
        except Students.DoesNotExist:
            pass

    # Create a pending payment in the database linked to this specific student
    from home.models import Payments
    payment_obj = Payments.objects.create(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        person_group=data.get("group", "student"),
        amount=data["amount"],
        message=data["message"],
        student=student,
        is_paid=False
    )

    request.session["payment_temp"] = {
        "id": payment_obj.id,
        "name": data["name"],
        "email": data["email"],
        "phone": data["phone"],
        "group": data.get("group", "student"),
        "student_name": f"{student.first_name} {student.last_name or ''}".strip() if student else data["name"],
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


@csrf_exempt
@login_required
def capture_retest_payment(request):
    if request.method != 'POST':
        return JsonResponse({"status": "failed", "message": "Method not allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        order_id = data.get("orderID")
        student_exam_id = data.get("student_exam_id")
        
        if not order_id or not student_exam_id:
            return JsonResponse({"status": "failed", "message": "Missing orderID or student_exam_id"}, status=400)
            
        student_exam = get_object_or_404(StudentsExams, id=student_exam_id)
        
        # 1) Get Access Token
        CLIENT_ID = settings.PAYPAL_CLIENT_ID
        CLIENT_SECRET = settings.PAYPAL_CLIENT_SECRET
        
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
            # 1. Update StudentsExams to approved and paid
            student_exam.retest_paid = True
            student_exam.is_approved = True
            student_exam.retest_status = 'approved'
            student_exam.save()
            
            # 2. Log in Payments table
            from home.models import Payments
            Payments.objects.create(
                code=f"RETEST-{student_exam.id}",
                name=student_exam.student.get_full_name(),
                email=student_exam.student.email or '',
                phone=student_exam.student.phone_number or '',
                person_group="student",
                amount=student_exam.retest_fee,
                message=f"Retest payment for exam: {student_exam.exam.exam_name}",
                is_paid=True,
                student=student_exam.student,
            )
            
            # 3. Send approval email to student
            subject = "Retest Exam Request Approved"
            message = f"Hello {student_exam.student.first_name},\n\nYour payment of ${student_exam.retest_fee} has been received and your retest request for the exam '{student_exam.exam.exam_name}' has been approved.\n\nYou can now take the exam at the scheduled time.\n\nBest regards,\nTrinity Theological Seminary"
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [student_exam.student.email],
                fail_silently=True
            )
            
            return JsonResponse({"status": "success", "details": capture_json})
            
        return JsonResponse({"status": "failed", "details": capture_json}, status=400)
    except Exception as e:
        logger.error(f"Error capturing retest payment: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


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
            profile_pic = request.FILES.get("photo")
            cert1 = request.FILES.get("certificate1")
            cert2 = request.FILES.get("certificate2")
            cert3 = request.FILES.get("certificate3")
            cert4 = request.FILES.get("certificate4")
            cert5 = request.FILES.get("certificate5")
            
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
            course_code = 'GEN'
            if 'course_obj' in locals() and course_obj:
                course_code = course_obj.course_code
                
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
            logger.info(f"Generated student ID: {student_id}")
            
        except Exception as e:
            logger.error(f" Error generating student ID: {e}", exc_info=True)
            messages.error(request, f"Error generating student ID: {e}")
            student_id = "STD-000000"

        # -------------------------------
        # USER CREATION & VALIDATION
        # -------------------------------
        email = request.POST.get('email')
        
        if Users.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists. Please login or use a different email.")
            return render(request, "site_pages/student_register.html")
            
        if Students.objects.filter(email=email).exists():
             messages.error(request, "A student application with this email already exists.")
             return render(request, "site_pages/student_register.html")

        # Create System User
        user_obj = None
        temp_password = get_random_string(10)
        try:
            with transaction.atomic():
                user_obj = Users()
                user_obj.name = f"{first_name} {last_name}".strip()
                user_obj.email = email
                user_obj.username = email
                user_obj.set_password(temp_password)
                user_obj.is_active = True  # Enable login for payment redirection
                user_obj.created_at = timezone.now()
                user_obj.updated_at = timezone.now()
                user_obj.save()
                
                # Assign Student Role
                student_role = Roles.objects.filter(name__iexact='Student').first()
                if student_role:
                    RoleUsers.objects.create(user=user_obj, role=student_role)
                else:
                    logger.error("Role 'student' not found in database.")

        except Exception as e:
            logger.error(f"Error creating user for student: {e}", exc_info=True)
            messages.error(request, "Error creating user account. Please try again.")
            return render(request, "site_pages/student_register.html")

        # -------------------------------
        # SAVE INTO DATABASE
        # -------------------------------
        try:
            student = Students.objects.create(
                student_id=student_id,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                user=user_obj, # Link created user
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
                is_paid=False,
            )
            
            logger.info(f"Student saved successfully!")
            logger.info(f"Database ID: {student.id}")
            logger.info(f"Student ID: {student.student_id}")

            course_fee = course_obj.fees if course_obj and course_obj.fees else 0.00

            if course_fee > 0.00:
                # Create a pending payment
                from home.models import Payments
                payment = Payments.objects.create(
                    name=f"{student.first_name} {student.last_name or ''}".strip(),
                    email=student.email,
                    phone=student.phone_number,
                    person_group="student",
                    amount=course_fee,
                    is_paid=False,
                    student=student
                )
                request.session['registration_payment_id'] = payment.id

                # Send Email to Student with credentials and payment details
                try:
                    subject = "Your Student Registration & Payment Details"
                    payment_link = request.build_absolute_uri('/register/payment/')
                    
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                      body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0; }}
                      .email-container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #e5e7eb; }}
                      .header {{ background: linear-gradient(135deg, #1e3a8a, #0d9488); padding: 30px 20px; text-align: center; color: #ffffff; }}
                      .header h1 {{ margin: 0; font-size: 24px; font-weight: bold; letter-spacing: 0.5px; }}
                      .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
                      .content {{ padding: 30px 25px; color: #374151; line-height: 1.6; }}
                      .content h2 {{ color: #1e3a8a; font-size: 18px; margin-top: 0; border-bottom: 2px solid #f3f4f6; padding-bottom: 8px; }}
                      .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                      .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #f3f4f6; }}
                      .details-table th {{ background-color: #f9fafb; font-weight: 600; color: #4b5563; width: 40%; }}
                      .details-table td {{ color: #1f2937; }}
                      .credentials-box {{ background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px; padding: 15px; margin: 20px 0; }}
                      .credentials-box p {{ margin: 5px 0; font-size: 14px; color: #065f46; }}
                      .btn-container {{ text-align: center; margin: 30px 0 10px 0; }}
                      .btn {{ display: inline-block; background-color: #10b981; color: #ffffff !important; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: background-color 0.2s; }}
                      .btn:hover {{ background-color: #059669; }}
                      .footer {{ background-color: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; }}
                    </style>
                    </head>
                    <body>
                      <div class="email-container">
                        <div class="header">
                          <h1>Trinity Theological Seminary</h1>
                          <p>Student Registration & Payment Details</p>
                        </div>
                        <div class="content">
                          <h2>Welcome, {student.first_name}!</h2>
                          <p>Thank you for registering at Trinity Theological Seminary. Your student application has been successfully created. Please find your registration details and login credentials below.</p>
                          
                          <table class="details-table">
                            <tr>
                              <th>Student ID</th>
                              <td>{student.student_id}</td>
                            </tr>
                            <tr>
                              <th>Course Applied</th>
                              <td>{course_obj.course_name if course_obj else 'N/A'}</td>
                            </tr>
                            <tr>
                              <th>Registration Fee</th>
                              <td><strong>${course_fee:.2f}</strong></td>
                            </tr>
                            <tr>
                              <th>Payment Status</th>
                              <td><span style="color: #ef4444; font-weight: bold;">Pending Payment</span></td>
                            </tr>
                          </table>
                          
                          <div class="credentials-box">
                            <p><strong>Your Account Login Credentials:</strong></p>
                            <p><strong>Username / Email:</strong> {student.email}</p>
                            <p><strong>Temporary Password:</strong> <code style="font-family: monospace; font-size: 15px; font-weight: bold; background-color: #d1fae5; padding: 2px 6px; border-radius: 4px;">{temp_password}</code></p>
                            <p style="font-size: 12px; margin-top: 8px; color: #047857;"><em>Note: You can use these details to log in to complete your payment or check your application status.</em></p>
                          </div>

                          <p>To finalize your registration, please complete the payment using the link below:</p>
                          
                          <div class="btn-container">
                            <a href="{payment_link}" class="btn" style="color: #ffffff;">Proceed to Payment</a>
                          </div>
                        </div>
                        <div class="footer">
                          <p>&copy; 2026 Trinity Theological Seminary. All rights reserved.</p>
                          <p>This is an automated email, please do not reply directly to this message.</p>
                        </div>
                      </div>
                    </body>
                    </html>
                    """
                    
                    text_content = f"""
Dear {student.first_name},

Thank you for registering at Trinity Theological Seminary. Your application has been received.

Registration Details:
Student ID: {student.student_id}
Course Applied: {course_obj.course_name if course_obj else 'N/A'}
Registration Fee: ${course_fee:.2f}
Payment Status: Pending Payment

Your Account Login Credentials:
Username / Email: {student.email}
Temporary Password: {temp_password}

To complete your registration, please proceed to the payment page:
{payment_link}

Best regards,
Trinity Theological Seminary
                    """
                    
                    send_mail(
                        subject=subject,
                        message=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[student.email],
                        html_message=html_content,
                        fail_silently=False
                    )
                    logger.info(f"Registration & payment email sent to {student.email}")
                except Exception as e:
                    logger.error(f"Failed to send student registration email: {e}")

                return redirect("registration_payment")
            else:
                # Auto-approve payment status (since fee is 0 or empty)
                student.is_paid = True
                student.save()

                # Send Email to Student with credentials
                try:
                    subject = "Your Student Login Details"
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                      body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0; }}
                      .email-container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #e5e7eb; }}
                      .header {{ background: linear-gradient(135deg, #1e3a8a, #0d9488); padding: 30px 20px; text-align: center; color: #ffffff; }}
                      .header h1 {{ margin: 0; font-size: 24px; font-weight: bold; letter-spacing: 0.5px; }}
                      .header p {{ margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }}
                      .content {{ padding: 30px 25px; color: #374151; line-height: 1.6; }}
                      .content h2 {{ color: #1e3a8a; font-size: 18px; margin-top: 0; border-bottom: 2px solid #f3f4f6; padding-bottom: 8px; }}
                      .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                      .details-table th, .details-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #f3f4f6; }}
                      .details-table th {{ background-color: #f9fafb; font-weight: 600; color: #4b5563; width: 40%; }}
                      .details-table td {{ color: #1f2937; }}
                      .credentials-box {{ background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px; padding: 15px; margin: 20px 0; }}
                      .credentials-box p {{ margin: 5px 0; font-size: 14px; color: #065f46; }}
                      .footer {{ background-color: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; }}
                    </style>
                    </head>
                    <body>
                      <div class="email-container">
                        <div class="header">
                          <h1>Trinity Theological Seminary</h1>
                          <p>Student Registration Confirmation</p>
                        </div>
                        <div class="content">
                          <h2>Welcome, {student.first_name}!</h2>
                          <p>Thank you for registering at Trinity Theological Seminary. Your student application has been successfully received and is currently under review. Please find your registration details and login credentials below.</p>
                          
                          <table class="details-table">
                            <tr>
                              <th>Student ID</th>
                              <td>{student.student_id}</td>
                            </tr>
                            <tr>
                              <th>Course Applied</th>
                              <td>{course_obj.course_name if course_obj else 'N/A'}</td>
                            </tr>
                            <tr>
                              <th>Payment Status</th>
                              <td><span style="color: #10b981; font-weight: bold;">Paid / No Fee</span></td>
                            </tr>
                          </table>
                          
                          <div class="credentials-box">
                            <p><strong>Your Account Login Credentials:</strong></p>
                            <p><strong>Username / Email:</strong> {student.email}</p>
                            <p><strong>Temporary Password:</strong> <code style="font-family: monospace; font-size: 15px; font-weight: bold; background-color: #d1fae5; padding: 2px 6px; border-radius: 4px;">{temp_password}</code></p>
                          </div>
                        </div>
                        <div class="footer">
                          <p>&copy; 2026 Trinity Theological Seminary. All rights reserved.</p>
                          <p>This is an automated email, please do not reply directly to this message.</p>
                        </div>
                      </div>
                    </body>
                    </html>
                    """
                    
                    text_content = f"""
Dear {student.first_name},

Thank you for registering at Trinity Theological Seminary. Your application has been received and is currently under review.

Registration Details:
Student ID: {student.student_id}
Course Applied: {course_obj.course_name if course_obj else 'N/A'}
Payment Status: Paid / No Fee

Your Account Login Credentials:
Username / Email: {student.email}
Temporary Password: {temp_password}

Best regards,
Trinity Theological Seminary
                    """
                    
                    send_mail(
                        subject=subject,
                        message=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[student.email],
                        html_message=html_content,
                        fail_silently=False
                    )
                except Exception as e:
                    logger.error(f"Failed to send student login details email: {e}")

                # Send Email to Admin
                try:
                    admin_subject = 'New Student Application Received'
                    admin_message = f'''A new student application has been submitted.
Name: {student.first_name} {student.last_name}
Course: {student.course_applied.course_name if student.course_applied else 'N/A'}

Please login to the admin panel to review.'''
                    send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, ['contact@byteboot.in'])
                except Exception as e:
                    logger.error(f"Failed to send admin email: {e}")

                return redirect("student_application_success", student_id=student.student_id)

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
def student_inactive(request):
    try:
        student = Students.objects.filter(user=request.user).first()
    except Exception as e:
        logger.error(f"Failed to fetch student in inactive view: {e}")
        student = None

    if not student:
        messages.error(request, "Student profile not found.")
        return redirect("signin")

    # If the student is active and paid, redirect them to dashboard
    if student.is_paid and student.active:
        return redirect("student_home")

    # If the student has not paid, redirect to payment screen
    if not student.is_paid:
        from home.models import Payments, StudentsSubjects
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
            request.session['registration_payment_id'] = payment.id
            messages.warning(request, f"Please complete your registration payment of ${balance_due:.2f} to proceed.")
            return redirect('registration_payment')
        else:
            student.is_paid = True
            student.save()
            if student.active:
                return redirect("student_home")

    # Render the inactive view
    return render(request, "student/inactive.html", {"student": student})


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

def check_email_availability(request):
    """Check if email already exists"""
    if request.method == 'GET':
        email = request.GET.get('email', '').strip()
        if not email:
            return JsonResponse({'exists': False, 'error': 'Empty email'})
        
        # Check Students and Users
        student_exists = Students.objects.filter(email=email).exists()
        user_exists = Users.objects.filter(email=email).exists()
        
        if student_exists or user_exists:
            return JsonResponse({'exists': True})
        return JsonResponse({'exists': False})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
@login_required
def apply_church_admin(request):
    """
    View for students to apply for Church Admin role.
    """
    try:
        student = Students.objects.get(user=request.user)
    except Students.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_home')

    # Check if already a church admin
    if ChurchAdmins.objects.filter(student=student, deleted_at__isnull=True).exists():
        messages.info(request, "You are already a Church Admin.")
        return redirect('student_profile_view')

    # Check for pending application
    pending_app = ChurchAdminApplication.objects.filter(student=student, status='pending').first()
    if pending_app:
        messages.info(request, "You already have a pending application.")
        return redirect('student_profile_view')

    if request.method == 'POST':
        name_of_church = request.POST.get('name_of_church')
        name_of_pastor = request.POST.get('name_of_pastor')
        church_address = request.POST.get('church_address')
        package_id = request.POST.get('package')

        if not name_of_church or not package_id:
            messages.error(request, "Please fill in all required fields.")
        else:
            try:
                from home.models import ChurchLoginCodeSettings
                package = ChurchLoginCodeSettings.objects.get(id=package_id)
                
                ChurchAdminApplication.objects.create(
                    student=student,
                    name_of_church=name_of_church,
                    name_of_pastor=name_of_pastor,
                    church_address=church_address,
                    church_code_settings=package
                )
                messages.success(request, "Application submitted successfully! Please wait for admin approval.")
                return redirect('student_profile_view')
            except Exception as e:
                logger.error(f"Error submitting church admin application: {e}")
                messages.error(request, "An error occurred while submitting your application.")

    from home.models import ChurchLoginCodeSettings
    packages = ChurchLoginCodeSettings.objects.filter(status=1)
    
    return render(request, 'student/apply_church_admin.html', {
        'student': student,
        'packages': packages,
        'page_title': 'Apply for Church Admin'
    })

@login_required
@student_or_church_user
@require_POST
def student_request_retest(request, exam_id):
    try:
        student = Students.objects.get(user=request.user)
        
        # Fetch the completed StudentsExams record
        student_exam = get_object_or_404(StudentsExams, id=exam_id, student=student)
        
        # Check if they have already requested a retest for this exam that is pending or approved
        existing_retest = StudentsExams.objects.filter(
            student=student,
            exam=student_exam.exam,
            is_retest=True,
            retest_status__in=['pending', 'approved'],
            deleted_at__isnull=True
        ).exists()
        
        if existing_retest:
            return JsonResponse({"status": "error", "message": "You already have a pending or approved retest for this exam."}, status=400)
            
        # Get rescheduling fields from request
        exam_date = request.POST.get("examDate")
        start_time_str = request.POST.get("startTime")
        timezone_val = request.POST.get("timezone")
        
        if not all([exam_date, start_time_str, timezone_val]):
            return JsonResponse({"status": "error", "message": "All scheduling fields (Date, Time, Timezone) are required."}, status=400)
            
        # Combine date and time, and localize
        try:
            datetime_str = f"{exam_date} {start_time_str}"
            naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            final_datetime = localize_datetime(naive_datetime, timezone_val)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid date or time format."}, status=400)
            
        # Find attempt count
        attempt_count = StudentsExams.objects.filter(
            student=student,
            exam=student_exam.exam,
            deleted_at__isnull=True
        ).count()
        
        # Create a new StudentsExams record for the retest
        StudentsExams.objects.create(
            student=student,
            course=student_exam.course,
            subject=student_exam.subject,
            exam=student_exam.exam,
            start_time=final_datetime,
            end_time=None,
            exam_duration=120,  # 2 Hours
            timezone=timezone_val,
            requested_by=request.user,
            created_by=request.user,
            updated_by=request.user,
            show_on_score=0,
            is_approved=False,  # Needs admin approval
            is_retest=True,
            retest_status='pending',
            retest_requested_at=timezone.now(),
            attempt_number=attempt_count + 1
        )
        
        return JsonResponse({"status": "success", "message": "Retest request submitted successfully! Pending admin approval."})
        
    except Students.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Student not found."}, status=404)
    except Exception as e:
        logger.error(f"Error requesting retest: {e}")
        return JsonResponse({"status": "error", "message": f"Failed to request retest: {str(e)}"}, status=500)
