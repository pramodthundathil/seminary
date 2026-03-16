from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from home.models import ChurchAdmins, Students, Branches, Subjects, StudentsExams, Exams, StudentsAssignment
import logging

logger = logging.getLogger(__name__)

@login_required
def church_user_home(request):
    """
    Dashboard Home landing page for generic Church Users.
    """
    try:
        student = Students.objects.select_related("user", "language", "course_applied").filter(user=request.user).first()
        church_admin = student.user.church_admin if student and student.user else None
        
        if not student or not church_admin:
            messages.error(request, "Unauthorized access.")
            return redirect('signin')
            
        branch = church_admin.church_code.branches if church_admin.church_code else None

        # Notifications
        try:
            from home.models import Notifications
            notifications = list(Notifications.objects.filter(student_id=student.id))
        except Exception:
            notifications = []

        # Course details
        course = None
        if student.course_applied:
            course = {
                "id": student.course_applied.id,
                "name": student.course_applied.course_name,
                "code": student.course_applied.course_code,
            }

        # Instructor
        instructor_name = None
        try:
            from home.models import StudentsInstructor
            instructor_relation = StudentsInstructor.objects.select_related("instructor").filter(student_id=student.id).first()
            if instructor_relation:
                instructor_name = instructor_relation.instructor.staff_name
        except Exception:
            pass
            
        language = student.language.language_name if student.language else None

        context = {
            "student": student,
            "church_name": church_admin.name_of_church if church_admin else None,
            "branch_name": branch.branch_name if branch else None,
            "notifications": notifications,
            "course": course,
            "instructor_name": instructor_name,
            "language": language,
            "page_title": "Dashboard"
        }
        return render(request, "church/user_home.html", context)

    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        messages.error(request, "Error fetching your dashboard information.")
        return redirect('signin')

@login_required
def church_user_subjects(request):
    """
    Subjects list for Church Users.
    """
    try:
        # Get the currently logged-in student user
        student = Students.objects.select_related("user").filter(user=request.user).first()
        if not student:
            messages.error(request, "Student profile not found.")
            return render(request, "church/user_dashboard.html", {})

        # Ensure they are a church user
        # A student managed by a Church Admin will have user.church_admin set to that Admin's record
        church_admin = student.user.church_admin if student.user else None
        
        if not church_admin:
            messages.error(request, "You are not associated with a Church Admin.")
            return render(request, "church/user_dashboard.html", {})

        # Fetch subjects associated with the Church Admin's branch
        branch = church_admin.church_code.branches if church_admin.church_code else None
        
        subjects = []
        if branch:
            subjects = Subjects.objects.filter(branches=branch, deleted_at=None, status=True).order_by('subject_name')

    except Exception as e:
        messages.error(request, "Error fetching your subjects information.")
        subjects = []

    return render(request, "church/user_dashboard.html", {"subjects": subjects, "page_title": "My Subjects"})

@login_required
def church_user_subject_uploads(request, subject_id):
    """
    View for Church Users to see all study materials (uploads) associated with a specific subject.
    This replaces the ability to request exams/assignments directly by simply listing available resources.
    """
    try:
        # Security Verification
        student = Students.objects.select_related("user").filter(user=request.user).first()
        church_admin = student.user.church_admin if student and student.user else None
        
        if not student or not church_admin:
            messages.error(request, "Unauthorized access.")
            return redirect('church_user_subjects')
            
        branch = church_admin.church_code.branches if church_admin.church_code else None

        # Ensure the requested subject belongs to the user's branch
        subject = Subjects.objects.filter(id=subject_id, branches=branch, deleted_at=None, status=True).first()
        
        if not subject:
            messages.error(request, "Subject not found or access denied.")
            return redirect('church_user_subjects')

        # 1. Fetch Book References (Materials)
        from home.models import BookReferences, Assignments, Uploads
        
        references = BookReferences.objects.filter(
            subject=subject,
            status=True,
            deleted_at=None
        ).select_related('reference_file').order_by('-created_at')

        # 2. Fetch Assignments associated with the subject (just listing, not for submission here)
        assignments = Assignments.objects.filter(
            subject=subject,
            deleted_at=None
        ).order_by('-created_at')
        
        # 3. Fetch generic Uploads (like videos/recordings)
        uploads = Uploads.objects.filter(
            subject=subject,
            status=True
        ).select_related('youtube', 'media', 'video_id').order_by('-created_at')
        
        recordings = []
        for upload in uploads:
            import re
            item = {
                'id': upload.id,
                'title': upload.upload_name,
                'description': upload.description,
                'date': upload.created_at,
                'type': 'file',
                'url': '',
                'thumb': ''
            }

            if upload.youtube:
                item['type'] = 'youtube'
                item['url'] = upload.youtube.file_path
                regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                match = re.search(regex, item['url'])
                item['youtube_id'] = match.group(1) if match else None
                item['thumb'] = upload.youtube.thumb_file_path if upload.youtube.thumb_file_path else ''
            
            elif upload.media:
                file_url = upload.media.file_path.url if upload.media.file_path else ''
                ext = upload.media.file_type.lower() if upload.media.file_type else ''
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
            
            recordings.append(item)

        # 4. Fetch Exams for the subject
        exams = Exams.objects.filter(subject=subject, deleted_at=None)
        
        # Determine status for each exam for this student
        exam_list = []
        for exam in exams:
            # Check if there is an existing StudentsExams record
            se = StudentsExams.objects.filter(student=student, exam=exam, deleted_at=None).first()
            
            status = "Not Started"
            can_take = True
            se_id = None
            
            if se:
                se_id = se.id
                if se.is_exam_ended:
                    status = "Completed"
                    can_take = False
                elif se.is_exam_started:
                    status = "Ongoing"
                    can_take = True
                else:
                    status = "Ready"
                    can_take = True
            
            exam_list.append({
                "id": exam.id,
                "se_id": se_id,
                "name": exam.exam_name,
                "duration": exam.exam_duration if hasattr(exam, 'exam_duration') else 0,
                "status": status,
                "can_take": can_take
            })

        context = {
            "subject": subject,
            "references": references,
            "assignments": assignments,
            "recordings": recordings,
            "exams": exam_list,
            "page_title": f"Uploads - {subject.subject_name}"
        }

        return render(request, "church/subject_uploads.html", context)

    except Exception as e:
        logger.error(f"Subject uploads error: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading subject resources.")
        return redirect('church_user_subjects')

@login_required
def church_user_assignments(request):
    """
    View to list all assignments for all subjects managed by the user's church branch.
    """
    try:
        student = Students.objects.select_related("user").filter(user=request.user).first()
        church_admin = student.user.church_admin if student and student.user else None
        
        if not student or not church_admin:
            messages.error(request, "Unauthorized access.")
            return redirect('signin')
            
        branch = church_admin.church_code.branches if church_admin.church_code else None
        
        from home.models import Assignments
        assignments = []
        if branch:
            subjects = Subjects.objects.filter(branches=branch, deleted_at=None, status=True).values_list('id', flat=True)
            assignments = Assignments.objects.filter(subject_id__in=subjects, deleted_at=None).select_related('subject').order_by('-created_at')

        return render(request, "church/assignments.html", {"assignments": assignments, "page_title": "Assignments"})

    except Exception as e:
        messages.error(request, "Error fetching assignments.")
        return redirect('church_user_home')

@login_required
def church_user_view_assignment(request, assignment_id):
    """
    View to let a church user review details/questions about a single assignment.
    """
    try:
        student = Students.objects.select_related("user").filter(user=request.user).first()
        church_admin = student.user.church_admin if student and student.user else None
        
        if not student:
            messages.error(request, "Unauthorized access.")
            return redirect('signin')

        from home.models import Assignments, AssignmentQuestions, StudentsAssignment, AssignmentAnswers
        
        assignment = get_object_or_404(Assignments, id=assignment_id)
        questions = AssignmentQuestions.objects.filter(assignment=assignment).order_by('id')
        
        # Determine if logically assigned and if submitted
        # We need to know if we've successfully submitted it
        # Try to find an existing submission link record, or initialize one internally
        student_assignment = StudentsAssignment.objects.filter(student=student, assignment=assignment).first()
        submission = AssignmentAnswers.objects.filter(student=student, assignment=assignment).first() if student_assignment else None

        
        # If an action to submit was placed on the view
        if request.method == "POST":
            # Just mimicking the earlier logic for direct submission inside the viewer
            if submission:
                messages.warning(request, "You have already submitted this assignment.")
                return redirect('church_user_view_assignment', assignment_id=assignment.id)
                
            with transaction.atomic():
                # Verify student_assignment relation exists, if not create it
                if not student_assignment:
                    student_assignment = StudentsAssignment.objects.create(
                        student=student, 
                        assignment=assignment,
                        created_by=request.user,
                        updated_by=request.user
                    )

                assignment_type = assignment.assignment_type
                answer_file_path = None
                answer_text_content = None

                if assignment_type in ('paper_upload', 'Paper Upload Type', 'Paper Upload type'):
                    uploaded_file = request.FILES.get('answer_file')
                    if not uploaded_file:
                        messages.error(request, "Please upload a file.")
                        return redirect('church_user_view_assignment', assignment_id=assignment.id)
                    answer_file_path = uploaded_file 
                    
                elif assignment_type in ('paper_submit', 'Paper Submit Type', 'Paper Submit type'):
                    if questions.exists():
                        combined_answers = ""
                        for index, q in enumerate(questions, 1):
                            ans = request.POST.get(f'answer_text_{q.id}', '').strip()
                            combined_answers += f"<strong>Q{index}: {q.question}</strong><br>"
                            combined_answers += f"<p>{ans}</p><hr>"
                        answer_text_content = combined_answers
                    else:
                        answer_text_content = request.POST.get('answer_text')

                    if not answer_text_content:
                        messages.error(request, "Please provide an answer.")
                        return redirect('church_user_view_assignment', assignment_id=assignment.id)

                AssignmentAnswers.objects.create(
                    assignment=assignment,
                    student=student,
                    answer_file=answer_file_path,
                    answer_text=answer_text_content,
                    created_at=timezone.now()
                )

                student_assignment.submitted_on = timezone.now()
                student_assignment.save()
                
                messages.success(request, "Assignment submitted successfully!")
                return redirect('church_user_submitted_assignment')

        context = {
            "assignment": assignment,
            "questions": questions,
            "is_submitted": True if submission else False,
            "submission": submission
        }
        return render(request, "church/view_assignment.html", context)
        
    except Exception as e:
        logger.error(f"Error fetching assignment {assignment_id}: {e}")
        messages.error(request, "Error fetching assignment details.")
        return redirect('church_user_assignments')

@login_required
def church_user_recordings(request):
    """
    View to list all video recordings across all their branch subjects.
    """
    try:
        student = Students.objects.select_related("user").filter(user=request.user).first()
        try:
            church_admin = student.user.church_admin if student and student.user else None
        except ObjectDoesNotExist:
            church_admin = None
        except Exception:
            church_admin = None
        
        if not student or not church_admin:
            messages.error(request, "Unauthorized access.")
            return redirect('signin')
            
        branch = church_admin.church_code.branches if church_admin.church_code else None
        
        from home.models import Uploads
        recordings = []
        if branch:
            subjects = Subjects.objects.filter(branches=branch, deleted_at=None, status=True).values_list('id', flat=True)
            uploads = Uploads.objects.filter(subject_id__in=subjects, status=True).select_related('youtube', 'media', 'subject', 'video_id', 'video_id__youtube', 'video_id__media').order_by('-created_at')
            
            for upload in uploads:
                import re
                item = {
                    'id': upload.id,
                    'title': upload.upload_name,
                    'description': upload.description,
                    'subject': upload.subject.subject_name if upload.subject else '-',
                    'date': upload.created_at,
                    'type': 'file',
                    'url': '',
                    'thumb': ''
                }

                if upload.youtube:
                    item['type'] = 'youtube'
                    item['url'] = upload.youtube.file_path
                    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                    match = re.search(regex, item['url'])
                    item['youtube_id'] = match.group(1) if match else None
                    item['thumb'] = upload.youtube.thumb_file_path if upload.youtube.thumb_file_path else ''
                
                elif upload.media:
                    file_url = upload.media.file_path.url if upload.media.file_path else ''
                    ext = upload.media.file_type.lower() if upload.media.file_type else ''
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
                
                if item['type'] in ['video', 'youtube']:
                    recordings.append(item)

        return render(request, "church/recordings.html", {"recordings": recordings, "page_title": "Class Recordings"})

    except Exception as e:
        import traceback
        error_msg = f"Error fetching recordings: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        messages.error(request, f"Error fetching recordings: {str(e)}")
        return redirect('church_user_home')

from django.http import JsonResponse
import json
from django.contrib.auth import update_session_auth_hash

@login_required
def church_user_change_password(request):
    """
    Form view to handle password modifications for the local church user session.
    """
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
            update_session_auth_hash(request, user)  # Keep logged in

            return JsonResponse({"status": "success", "message": "Password changed successfully"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": "An error occurred"}, status=500)

    return render(request, "church/change_password.html")



@login_required
def church_user_submitted_assignment(request):
    try:
        student = Students.objects.select_related("user").get(user=request.user)
    except Students.DoesNotExist:
        return render(request, "church/submitted_assignment.html", {"error": "Student not found"})

    from home.models import Assignments, AssignmentQuestions, StudentsAssignment, AssignmentAnswers

    try:
        submitted_assignments = StudentsAssignment.objects.filter(
            student=student,
            submitted_on__isnull=False
        ).select_related('assignment', 'assignment__subject', 'student') 
        
        for sa in submitted_assignments:
            answer = AssignmentAnswers.objects.filter(
                student=student, 
                assignment=sa.assignment
            ).last() 
            sa.submitted_answer = answer 

    except Exception as e:
        logger.error(f"Failed to fetch submitted assignments for student {student.id}: {e}")
        submitted_assignments = []

    return render(request, "church/submitted_assignment.html", {"submitted_assignments": submitted_assignments})

from django.shortcuts import get_object_or_404
from django.db import transaction

@login_required
def church_submit_assignment(request, pk):
    try:
        student_assignment = StudentsAssignment.objects.select_related('assignment', 'assignment__subject').get(
            id=pk, 
            student__user=request.user
        )
    except StudentsAssignment.DoesNotExist:
        messages.error(request, "Assignment not found.")
    
    if student_assignment.submitted_on:
        messages.warning(request, "This assignment has already been submitted.")
        return redirect('church_user_submitted_assignment')

    if request.method == "POST":
        assignment_type = student_assignment.assignment.assignment_type
        
        try:
            with transaction.atomic():
                answer_file_path = None
                answer_text_content = None

                if assignment_type == 'Paper Upload Type':
                    uploaded_file = request.FILES.get('answer_file')
                    if not uploaded_file:
                        messages.error(request, "Please upload a file.")
                        return redirect('church_submit_assignment', pk=pk)
                    
                    answer_file_path = uploaded_file 
                    
                elif assignment_type == 'Paper Submit Type':
                    questions = student_assignment.assignment.questions.all()
                    
                    if questions.exists():
                        combined_answers = ""
                        for index, q in enumerate(questions, 1):
                            ans = request.POST.get(f'answer_text_{q.id}', '').strip()
                            combined_answers += f"<strong>Q{index}: {q.question}</strong><br>"
                            combined_answers += f"<p>{ans}</p><hr>"
                        
                        answer_text_content = combined_answers
                    else:
                        answer_text_content = request.POST.get('answer_text')

                    if not answer_text_content:
                        messages.error(request, "Please provide an answer.")
                        return redirect('church_submit_assignment', pk=pk)

                AssignmentAnswers.objects.create(
                    assignment=student_assignment.assignment,
                    student=student_assignment.student,
                    answer_file=answer_file_path,
                    answer_text=answer_text_content,
                    created_at=timezone.now()
                )

                student_assignment.submitted_on = timezone.now()
                student_assignment.save()
                
                messages.success(request, "Assignment submitted successfully!")
                return redirect('church_user_submitted_assignment')

        except Exception as e:
            logger.error(f"Error submitting assignment {pk}: {e}")
            messages.error(request, "An error occurred while submitting. Please try again.")
            return redirect('church_submit_assignment', pk=pk)

    questions = student_assignment.assignment.questions.all()
    
    context = {
        "student_assignment": student_assignment,
        "questions": questions
    }
    return render(request, "church/assignment_submit.html", context)

from django.core.paginator import Paginator
from django.db.models import Sum
from datetime import timedelta

@login_required
def church_user_exam_hall(request):
    try:
        student = Students.objects.select_related('course_applied').only('id', 'course_applied__course_name').get(user=request.user)
    except Students.DoesNotExist:
        return render(request, "church/exam_hall.html", {"error": "Student not found"})

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
            "is_approved",
            "start_time",
            "timezone"
        )
        .order_by('-created_at')
    )

    paginator = Paginator(exams_queryset, 5)
    page_number = request.GET.get('page')
    exams_page = paginator.get_page(page_number)

    exam_list = []
    now = timezone.now()
    
    for e in exams_page:
        try:
            exam_obj = e.exam
            subject_obj = exam_obj.subject if exam_obj else None
            
            if e.is_exam_ended:
                status, action, can_start = "Completed", "View", False
            elif e.is_approved and e.start_time and e.start_time <= now:
                status, action, can_start = "Ongoing", "Start", True
            elif not e.is_approved and e.start_time and e.start_time <= now:
                status, action, can_start = "Pending Approval", "Wait", False
            else:
                status, action, can_start = "Pending", "Wait", False
                
        except Exception as ex:
            continue

        exam_list.append({
            "id": e.id,
            "exam_name": getattr(exam_obj, "exam_name", "N/A"),
            "subject_name": getattr(subject_obj, "subject_name", "N/A"),
            "requested_time": e.start_time,
            "timezone": e.timezone,
            "status": status,
            "can_start": can_start,
            "action": action
        })

    return render(request, "church/exam_hall.html", {
        "exam_list": exam_list,
        "paginator": paginator,
        "exams_page": exams_page,
    })

from django.utils.timezone import make_aware
from datetime import datetime

@login_required
def church_user_start_exam(request, exam_id):
    """
    Directly start or resume an exam. Creates a StudentsExams record if one doesn't exist.
    """
    try:
        student = Students.objects.filter(user=request.user).first()
        if not student:
             messages.error(request, "Student profile not found.")
             return redirect('church_user_subjects')

        exam = get_object_or_404(Exams, id=exam_id, deleted_at=None)
        
        # Find or create StudentsExams
        student_exam, created = StudentsExams.objects.get_or_create(
            student=student,
            exam=exam,
            deleted_at=None,
            defaults={
                'start_time': timezone.now(),
                'is_approved': True,
                'is_exam_started': True,
                'timezone': 'UTC+05:30', 
                'requested_by': request.user,
                'created_by': request.user,
                'updated_by': request.user,
                'exam_duration': exam.exam_duration if hasattr(exam, 'exam_duration') else 0,
                'show_on_score': 0,
            }
        )
        
        if not created:
            if student_exam.is_exam_ended:
                messages.warning(request, "You have already completed this exam.")
                return redirect('church_user_subject_uploads', subject_id=exam.subject.id)
            
            if not student_exam.is_exam_started:
                student_exam.is_exam_started = True
                student_exam.start_time = timezone.now()
                student_exam.is_approved = True
                student_exam.save()
        
        from home.models import ObjectiveAnswers, DescriptiveAnswers
        
        # Initialize empty answers if they don't exist
        for obj_q in exam.objective_questions.all():
            ObjectiveAnswers.objects.get_or_create(
                assignment=student_exam,
                question=obj_q,
                defaults={'answer': '', 'mark': 0}
            )

        for desc_q in exam.descriptive_questions.all():
            DescriptiveAnswers.objects.get_or_create(
                assignment=student_exam,
                question=desc_q,
                defaults={'answer': '', 'mark': 0}
            )

        return redirect('church_user_take_exam', exam_id=student_exam.id)
        
    except Exception as e:
        messages.error(request, f"Error starting exam: {str(e)}")
        return redirect('church_user_subjects')

@login_required
def church_user_take_exam(request, exam_id):
    try:
        student = Students.objects.get(user=request.user)
    except Students.DoesNotExist:
        return redirect("church_user_exam_hall")

    student_exam = get_object_or_404(StudentsExams, id=exam_id, student=student)
    now = timezone.now()
    
    if student_exam.is_exam_ended:
        messages.error(request, "You have already completed this exam.")
        return redirect("church_user_exam_hall")
        
    if student_exam.start_time and student_exam.start_time > now:
        messages.error(request, "It is not yet time to start this exam.")
        return redirect("church_user_exam_hall")

    if not student_exam.is_exam_started:
        student_exam.is_exam_started = True
        student_exam.save()

    exam_obj = student_exam.exam
    objective_questions = exam_obj.objective_questions.all()
    descriptive_questions = exam_obj.descriptive_questions.all()
    
    from home.models import ObjectiveAnswers, DescriptiveAnswers
    
    # Ensure empty answers are perfectly initialized for this exam session
    for obj_q in objective_questions:
        ObjectiveAnswers.objects.get_or_create(
            assignment=student_exam,
            question=obj_q,
            defaults={'answer': '', 'mark': 0}
        )

    for desc_q in descriptive_questions:
        DescriptiveAnswers.objects.get_or_create(
            assignment=student_exam,
            question=desc_q,
            defaults={'answer': '', 'mark': 0}
        )
    
    if student_exam.exam_duration:
        exam_end_time = student_exam.start_time + timedelta(minutes=student_exam.exam_duration)
        remaining_seconds = (exam_end_time - now).total_seconds()
    else:
        remaining_seconds = 3600
        
    if remaining_seconds <= 0:
        student_exam.is_exam_ended = True
        student_exam.save()
        messages.error(request, "Exam duration has expired.")
        return redirect("church_user_exam_hall")

    return render(request, "church/take_exam.html", {
        "student_exam": student_exam,
        "exam": exam_obj,
        "objective_questions": objective_questions,
        "descriptive_questions": descriptive_questions,
        "remaining_seconds": max(0, int(remaining_seconds)),
    })

@login_required
def church_user_submit_exam(request, exam_id):
    if request.method != "POST":
        return redirect("church_user_exam_hall")

    has_errors = False
    try:
        student = Students.objects.get(user=request.user)
        student_exam = StudentsExams.objects.get(id=exam_id, student=student)
        
        if student_exam.is_exam_ended:
            return redirect("church_user_exam_hall")
        
        for key, value in request.POST.items():
            if not (key.startswith("obj_q_") or key.startswith("desc_q_")):
                continue
                
            try:
                if key.startswith("obj_q_"):
                    q_id = key.split("_")[2] 
                    if not q_id.isdigit(): continue
                        
                    question = ObjectiveQuestions.objects.get(id=q_id)
                    val_str = str(value).strip()
                    correct_opt = str(question.answer_option).strip()
                    is_correct = (val_str == correct_opt)
                    
                    qm = question.marks if question.marks else 0
                    marks_awarded = qm if is_correct else 0
                    try: marks_awarded = int(float(marks_awarded))
                    except: marks_awarded = 0
                    
                    ObjectiveAnswers.objects.update_or_create(
                        assignment=student_exam,
                        question=question,
                        defaults={'answer': val_str[:250], 'mark': marks_awarded}
                    )
                
                elif key.startswith("desc_q_"):
                    q_id = key.split("_")[2]
                    if not q_id.isdigit(): continue

                    question = DescriptiveQuestions.objects.get(id=q_id)
                    answer_text = str(value)
                    
                    DescriptiveAnswers.objects.update_or_create(
                        assignment=student_exam, 
                        question=question,
                        defaults={'answer': answer_text, 'mark': 0}
                    )
                    
            except Exception as inner_e:
                has_errors = True
        
        student_exam.is_exam_ended = True
        student_exam.end_time = timezone.now()
        student_exam.is_approved = True
        student_exam.save()
        
        if has_errors: messages.warning(request, "Exam submitted, but some answers might not have been saved. Please contact support.")
        else: messages.success(request, "Exam submitted successfully!")
            
        return redirect("church_user_score_card")
        
    except Exception as e:
        messages.error(request, "Something went wrong during submission.")
        return redirect("church_user_exam_hall")

@login_required
def church_user_score_card(request):
    try: student = Students.objects.get(user=request.user)
    except Students.DoesNotExist: return render(request, "church/score_card.html", {"error": "Student not found"})

    completed_exams = StudentsExams.objects.filter(student=student, is_exam_ended=True).select_related("exam").order_by('-end_time')
    exam_data = []
    
    for se in completed_exams:
        exam = se.exam
        total_obj_marks = exam.objective_questions.aggregate(total=Sum('marks'))['total'] or 0
        total_desc_marks = exam.descriptive_questions.aggregate(total=Sum('mark'))['total'] or 0
        total_marks = total_obj_marks + total_desc_marks
        obtained_marks = se.show_on_score or 0
        percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
        
        if percentage >= 90: grade = "A+"
        elif percentage >= 80: grade = "A"
        elif percentage >= 70: grade = "B"
        elif percentage >= 60: grade = "C"
        elif percentage >= 50: grade = "D"
        else: grade = "F"

        exam_data.append({
            "code": exam.code, "exam_name": exam.exam_name, "total_score": round(total_marks),
            "score": round(obtained_marks), "percentage": round(percentage, 2), "grade": grade
        })

    student_assignments = StudentsAssignment.objects.filter(student=student, submitted_on__isnull=False).order_by('-submitted_on').select_related("assignment")
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
            "code": assignment.code, "assignment_name": assignment.assignment_name, "total_score": total,
            "score": obtained, "percentage": round(percentage, 2), "grade": grade
        })

    def calc_grade(p):
        if p >= 90: return "A+"
        if p >= 80: return "A"
        if p >= 70: return "B"
        if p >= 60: return "C"
        if p >= 50: return "D"
        return "F"
        
    total_exam_max = sum(item['total_score'] for item in exam_data)
    total_exam_obtained = sum(item['score'] for item in exam_data)
    exam_percentage = (total_exam_obtained / total_exam_max * 100) if total_exam_max > 0 else 0
    total_assign_max = sum(item['total_score'] for item in assignment_data)
    total_assign_obtained = sum(item['score'] for item in assignment_data)
    assign_percentage = (total_assign_obtained / total_assign_max * 100) if total_assign_max > 0 else 0
    grand_total_max = total_exam_max + total_assign_max
    grand_total_obtained = total_exam_obtained + total_assign_obtained
    grand_percentage = (grand_total_obtained / grand_total_max * 100) if grand_total_max > 0 else 0

    return render(request, "church/score_card.html", {
        "student": student, "student_exams": exam_data, "assignment_mark": assignment_data,
        "exam_summary": { "total": round(total_exam_max), "score": round(total_exam_obtained), "percentage": round(exam_percentage, 2), "grade": calc_grade(exam_percentage) },
        "assignment_summary": { "total": round(total_assign_max), "score": round(total_assign_obtained), "percentage": round(assign_percentage, 2), "grade": calc_grade(assign_percentage) },
        "grand_summary": { "total": round(grand_total_max), "score": round(grand_total_obtained), "percentage": round(grand_percentage, 2), "grade": calc_grade(grand_percentage) }
    })

@login_required
def church_user_profile_view(request):
    try:
        student = Students.objects.select_related("course_applied", "language", "citizenship", "country").get(user=request.user)
    except Students.DoesNotExist:
        return render(request, "church/student_profile.html", {"error": "Student profile not found."})

    return render(request, "church/student_profile.html", {"student": student})

@login_required
def church_user_doubts_answers(request):
    try:
        doubt_queryset = Support.objects.filter(student__user=request.user).select_related("student").order_by("-created_at")
        search_query = request.GET.get('search', '')
        if search_query:
            doubt_queryset = doubt_queryset.filter(doubt_question__icontains=search_query)
        
        paginator = Paginator(doubt_queryset, 5)
        page_number = request.GET.get('page')
        doubts_page = paginator.get_page(page_number)
    except Exception as e:
        doubts_page = []
        paginator = None
        search_query = ""

    return render(request, "church/doubts_answers.html", {
        "doubt": doubts_page,
        "paginator": paginator,
        "doubts_page": doubts_page,
        "search_query": search_query,
    })

@login_required
def church_user_doubt_view(request, id):
    try:
        doubt = Support.objects.select_related('student').get(id=id, student__user=request.user)
    except Support.DoesNotExist:
        messages.error(request, "Doubt not found or you don't have permission to view it.")
        return redirect('church_user_doubts_answers')
        
    return render(request, "church/support_view.html", {'doubt': doubt})

from django.views.decorators.http import require_POST

@login_required
@require_POST
def church_user_support_create(request):
    doubt = request.POST.get('doubt')
    category = request.POST.get('category', 'general')
    
    if doubt:
        try:
            student = Students.objects.get(user=request.user)
            Support.objects.create(
                student=student,
                doubt_question=doubt,
                categories=category
            )
            return JsonResponse({'success': True})
        except Students.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found.'})
        except Exception as e:
            logger.error(f"Support creation failed: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'No doubt text provided.'})

@login_required
def church_admin_dashboard(request):
    """
    Dashboard for the actual Church Admin (the owner of the Church Code).
    """
    # 1. Fetch the Church Admin record based on the logged-in user
    admin = ChurchAdmins.objects.filter(student__user=request.user, deleted_at__isnull=True).first()
    
    if not admin:
        messages.error(request, "Could not locate your Church Administrator profile.")
        return redirect('signin')

    # 2. Fetch the Registered Users (Students linked via user__church_admin)
    registered_students_list = Students.objects.filter(
        user__church_admin=admin, 
        user__deleted_at__isnull=True
    ).exclude(user=request.user).select_related('user').order_by('-created_at')

    paginator = Paginator(registered_students_list, 5) # 5 per page on the mini dashboard view
    page_number = request.GET.get('page')
    registered_students = paginator.get_page(page_number)

    # 3. Retrieve the Branch mapping using the admin code
    # We need to look up the ChurchLoginCodeSettings -> Branches
    # However, let's look at how ChurchAdmins code maps to Branch 
    from home.models import ChurchLoginCodeSettings # Using correct import based on Phase 2 knowledge
    
    branch = None
    subjects = []
    
    # Try linking Admin Code -> Settings -> Branch
    # ChurchAdmins has a direct ForeignKey to ChurchLoginCodeSettings via 'church_code'
    settings_record = admin.church_code
    if settings_record and hasattr(settings_record, 'branches') and settings_record.branches:
        branch = settings_record.branches
        subjects = Subjects.objects.filter(branches=branch).order_by('subject_name')

    context = {
        'admin': admin,
        'registered_students': registered_students,
        'branch': branch,
        'subjects': subjects,
    }

    return render(request, "church/admin_dashboard.html", context)


@login_required
def church_admin_settings(request):
    """
    Settings for the Church Admin, displaying package and branch details,
    and providing an option to change their password.
    """
    # Fetch the Church Admin record based on the logged-in user
    admin = ChurchAdmins.objects.filter(student__user=request.user, deleted_at__isnull=True).first()
    
    if not admin:
        messages.error(request, "Could not locate your Church Administrator profile.")
        return redirect('signin')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is not correct.')
            elif len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
            elif new_password != confirm_password:
                messages.error(request, 'New password and confirm password do not match.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
            return redirect('church_admin_settings')

    # Retrieve the Branch mapping using the admin code
    branch = None
    settings_record = admin.church_code
    if settings_record and hasattr(settings_record, 'branches') and settings_record.branches:
        branch = settings_record.branches

    context = {
        'admin': admin,
        'settings_record': settings_record,
        'branch': branch,
    }

    return render(request, "church/admin_settings.html", context)


# ==========================================
# CHURCH ADMIN STUDENT MANAGEMENT OVERRIDES
# ==========================================
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from home.models import Users, Roles, RoleUsers

def get_church_admin_for_user(user):
    """Helper to cleanly extract the ChurchAdmin record for the current user."""
    return ChurchAdmins.objects.filter(student__user=user, deleted_at__isnull=True).first()


from django.core.paginator import Paginator

@login_required
def church_students_list(request):
    """Render table of all Students tied to this Church Admin."""
    admin = get_church_admin_for_user(request.user)
    if not admin:
        messages.error(request, "Not authorized.")
        return redirect('signin')

    students_list = Students.objects.filter(
        user__church_admin=admin, 
        user__deleted_at__isnull=True
    ).exclude(user=request.user).order_by('-created_at')

    paginator = Paginator(students_list, 10) # 10 students per page
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)

    return render(request, "church/students_list.html", {'admin': admin, 'students': students})


@login_required
def church_student_view(request, id):
    """Detailed view of a specific student tied to this Admin."""
    admin = get_church_admin_for_user(request.user)
    if not admin:
        return redirect('signin')

    student = get_object_or_404(Students, id=id, user__church_admin=admin)
    return render(request, "church/student_view.html", {'admin': admin, 'student': student})


@login_required
def church_student_approve(request, id):
    """Approve a student and dispatch credentials, replicating SuperAdmin logic safely."""
    admin = get_church_admin_for_user(request.user)
    if not admin:
        return JsonResponse({'success': False, 'message': 'Not Authorized'}, status=403)

    student = get_object_or_404(Students, id=id, user__church_admin=admin)
    
    try:
        student.status = True
        student.active = True
        student.approve_date = timezone.now()
        
        user = student.user
        password = 'password123' # Default parity

        if not user and student.email:
            existing_user = Users.objects.filter(email=student.email).first()
            if existing_user:
                user = existing_user
                student.user = user
            else:
                user = Users()
                user.name = f"{student.first_name} {student.last_name if student.last_name else ''}".strip()
                user.email = student.email
                user.username = student.email
                user.created_at = timezone.now()
                user.save()
                
                student_role = Roles.objects.filter(name__iexact='Student').first()
                if student_role:
                    RoleUsers.objects.create(user=user, role=student_role)
                student.user = user
        
        if user:
            user.is_active = True
            user.set_password(password)
            user.updated_at = timezone.now()
            user.save()

            try:
                subject = 'Welcome to Trinity Seminary - Registration Approved'
                message = f'''Dear {student.first_name},\n\nYour registration has been approved by your Church Administrator.\n\nLogin Details:\nURL: https://trinityseminary.in/login\nUsername: {user.email}\nPassword: {password}\n\nIMPORTANT: Please change your password immediately after your first login.\n\nBest regards,\nAdministration'''
                from_email = 'contact@byteboot.in'
                send_mail(subject, message, from_email, [user.email])
            except Exception as e:
                pass # Fail silently for email block

        student.save()
        messages.success(request, f"{student.first_name} has been approved.")
        return redirect('church_student_view', id=student.id)

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('church_student_view', id=student.id)


@login_required
def church_student_delete(request, id):
    """Delete a student profile linked to this Admin."""
    if request.method == 'POST':
        admin = get_church_admin_for_user(request.user)
        if not admin:
            return JsonResponse({'success': False, 'message': 'Not Authorized'}, status=403)

        try:
            student = get_object_or_404(Students, id=id, user__church_admin=admin)
            student.delete()
            return JsonResponse({'success': True, 'message': 'Student deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)

import re
from home.models import Uploads

@login_required
def church_subjects_list(request):
    """Render a paginated table of all Subjects mapped to this Admin's active branch/package."""
    admin = get_church_admin_for_user(request.user)
    if not admin:
        messages.error(request, "Not authorized.")
        return redirect('signin')

    settings_record = admin.church_code
    if not settings_record or not getattr(settings_record, 'branches', None):
        messages.warning(request, "No educational branch or package is assigned to your Church Code.")
        return render(request, "church/subjects_list.html", {'admin': admin, 'subjects': []})

    branch = settings_record.branches
    subjects_qs = Subjects.objects.filter(branches=branch).order_by('subject_name')

    paginator = Paginator(subjects_qs, 10)
    page_number = request.GET.get('page')
    subjects = paginator.get_page(page_number)

    return render(request, "church/subjects_list.html", {
        'admin': admin, 
        'branch': branch, 
        'subjects': subjects
    })


@login_required
def church_subject_view(request, id):
    """Detailed view of a specific subject rendering its associated uploads natively."""
    admin = get_church_admin_for_user(request.user)
    if not admin:
        return redirect('signin')

    settings_record = admin.church_code
    if not settings_record or not getattr(settings_record, 'branches', None):
        return redirect('church_subjects_list')

    branch = settings_record.branches
    subject = get_object_or_404(Subjects, id=id, branches=branch)

    # Fetch uploads specific to this subject
    raw_uploads = Uploads.objects.filter(
        subject=subject, 
        status=True
    ).select_related('youtube', 'media', 'video_id', 'video_id__youtube', 'video_id__media').order_by('-created_at')

    compiled_uploads = []
    for upload in raw_uploads:
        item = {
            'id': upload.id,
            'title': upload.upload_name,
            'description': upload.description,
            'type': 'file',
            'url': '',
            'thumb': ''
        }

        # Check native Youtube relation
        if upload.youtube:
            item['type'] = 'youtube'
            item['url'] = upload.youtube.file_path
            # Parse Regex to determine thumbnail directly
            regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
            match = re.search(regex, item['url'])
            item['youtube_id'] = match.group(1) if match else None
            item['thumb'] = upload.youtube.thumb_file_path if upload.youtube.thumb_file_path else ''
        
        # Check native MediaLibrary relation
        elif upload.media:
            file_url = upload.media.file_path.url if upload.media.file_path else ''
            ext = upload.media.file_type.lower() if upload.media.file_type else ''
            
            # Sub-sort between static videos and general documents
            if ext in ['mp4', 'webm', 'ogg', 'mov', 'm4v']:
                item['type'] = 'video'
                item['url'] = file_url
            elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                 item['type'] = 'image'
                 item['url'] = file_url
            else:
                item['type'] = 'pdf' # Generalize PDFs and other docs to standard embed logic
                item['url'] = file_url

        # Check raw AWS direct links
        elif upload.aws_url:
            item['url'] = upload.aws_url
            ext = upload.aws_url.split('.')[-1].lower() if '.' in upload.aws_url else ''
            if ext in ['mp4', 'webm', 'ogg', 'mov', 'm4v']:
                item['type'] = 'video'
            elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                 item['type'] = 'image'
            else:
                item['type'] = 'pdf'

        # Check secondary Video relation (legacy structuring)
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

        compiled_uploads.append(item)

    return render(request, "church/subject_view.html", {
        'admin': admin, 
        'subject': subject,
        'uploads': compiled_uploads
    })
