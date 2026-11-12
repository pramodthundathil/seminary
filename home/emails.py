"""
Centralized admin email notification system for Trinity Theological Seminary.

Every student action (registrations, exam submissions, assignment submissions,
fee payments, academic/exam/church-admin requests, support tickets/replies,
contact submissions, chats, and profile updates) sends a structured HTML +
plain-text notification to `settings.ADMIN_EMAIL` (default: `admin@mytts.org`).
"""

import logging
from html import escape
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_admin_emails():
    """Return a non-empty list of admin notification email addresses."""
    raw = getattr(settings, "ADMIN_EMAIL", None) or "admin@mytts.org"
    if isinstance(raw, (list, tuple)):
        emails = [str(item).strip() for item in raw if str(item).strip()]
    else:
        emails = [part.strip() for part in str(raw).split(",") if part.strip()]
    return emails or ["admin@mytts.org"]


def get_from_email():
    """Return the configured sender email address."""
    return (
        getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "EMAIL_HOST_USER", None)
        or "mytrinitytheologicalseminary@gmail.com"
    )


def build_site_url(path=""):
    """Join a relative admin path with `settings.SITE_URL`."""
    base_url = getattr(settings, "SITE_URL", None) or "http://127.0.0.1:8000/"
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"
    if not path:
        return base_url
    if path.startswith(("http://", "https://")):
        return path
    return urljoin(base_url, path.lstrip("/"))


def format_timestamp(dt=None):
    """Format a datetime (or current UTC/local time) cleanly for email display."""
    target = dt or timezone.now()
    try:
        if timezone.is_aware(target):
            target = timezone.localtime(target)
        return target.strftime("%b %d, %Y %I:%M %p %Z").strip()
    except Exception:
        return str(target)


def student_identity_rows(student):
    """Extract standard `(label, value)` rows describing a student."""
    if not student:
        return []
    full_name = student.get_full_name() if hasattr(student, "get_full_name") else f"{student.first_name or ''} {student.last_name or ''}".strip()
    rows = [("Student Name", full_name or "N/A")]
    if getattr(student, "student_id", None):
        rows.append(("Student ID", student.student_id))
    if getattr(student, "email", None):
        rows.append(("Student Email", student.email))
    if getattr(student, "course_applied", None):
        rows.append(("Course", getattr(student.course_applied, "course_name", str(student.course_applied))))
    return rows


def _normalize_details(details):
    if not details:
        return []
    if isinstance(details, dict):
        items = list(details.items())
    else:
        items = list(details)
    return [(str(k), "N/A" if v in (None, "") else str(v)) for k, v in items]


def send_admin_notification(
    subject,
    title,
    summary,
    details=None,
    action_path=None,
    action_label="Open in Admin Panel",
    category="Student Activity",
):
    """
    Send an HTML + plain-text notification email to the configured admin email(s).

    Exceptions are caught and logged so SMTP errors never disrupt student actions.
    """
    recipients = get_admin_emails()
    from_email = get_from_email()
    full_subject = subject if subject.startswith("[") else f"[TTS Admin] {subject}"
    detail_rows = _normalize_details(details)
    action_url = build_site_url(action_path) if action_path else None

    text_lines = [
        "Trinity Theological Seminary - Admin Notification",
        f"Category: {category}",
        f"Title: {title}",
        "",
        summary,
        "",
    ]
    if detail_rows:
        text_lines.append("Details:")
        for label, value in detail_rows:
            text_lines.append(f"- {label}: {value}")
        text_lines.append("")
    if action_url:
        text_lines.append(f"{action_label}: {action_url}")
        text_lines.append("")
    text_lines.extend([
        "Best regards,",
        "Trinity Theological Seminary Automated Notification System",
    ])
    text_content = "\n".join(text_lines)

    rows_html = "".join(
        f"""
        <tr>
          <th style="padding:10px 12px; text-align:left; background:#f8fafc; color:#475569; font-weight:600; width:36%; border-bottom:1px solid #e2e8f0; vertical-align:top;">{escape(label)}</th>
          <td style="padding:10px 12px; color:#0f172a; border-bottom:1px solid #e2e8f0; white-space:pre-wrap;">{escape(value)}</td>
        </tr>
        """
        for label, value in detail_rows
    )

    details_table_html = (
        f"""
        <table style="width:100%; border-collapse:collapse; margin:18px 0; border:1px solid #e2e8f0; border-radius:6px;">
          {rows_html}
        </table>
        """
        if rows_html
        else ""
    )

    action_button_html = (
        f"""
        <div style="text-align:center; margin:24px 0 8px 0;">
          <a href="{escape(action_url)}" style="display:inline-block; background:#1e3a8a; color:#ffffff; text-decoration:none; padding:11px 24px; border-radius:6px; font-weight:600; font-size:14px;">{escape(action_label)}</a>
        </div>
        """
        if action_url
        else ""
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:'Helvetica Neue',Helvetica,Arial,sans-serif; background:#f1f5f9; margin:0; padding:20px;">
  <div style="max-width:640px; margin:0 auto; background:#ffffff; border-radius:8px; overflow:hidden; border:1px solid #e2e8f0; box-shadow:0 2px 6px rgba(15,23,42,0.06);">
    <div style="background:linear-gradient(135deg,#1e3a8a,#0d9488); padding:22px 24px; color:#ffffff;">
      <div style="font-size:12px; text-transform:uppercase; letter-spacing:1px; opacity:0.85;">{escape(category)}</div>
      <h1 style="margin:6px 0 0 0; font-size:20px; font-weight:700;">{escape(title)}</h1>
    </div>
    <div style="padding:24px; color:#334155; font-size:14px; line-height:1.6;">
      <p style="margin-top:0;">{escape(summary)}</p>
      {details_table_html}
      {action_button_html}
    </div>
    <div style="background:#f8fafc; padding:14px 24px; text-align:center; font-size:12px; color:#64748b; border-top:1px solid #e2e8f0;">
      Trinity Theological Seminary &bull; Automated Admin Alert ({escape(format_timestamp())})
    </div>
  </div>
</body>
</html>"""

    try:
        send_mail(
            subject=full_subject,
            message=text_content,
            from_email=from_email,
            recipient_list=recipients,
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Admin notification sent to %s: %s", recipients, full_subject)
        return True
    except Exception as exc:
        logger.error("Failed to send admin notification '%s' to %s: %s", full_subject, recipients, exc, exc_info=True)
        return False


def notify_admin_student_registration(
    student=None,
    registration_type="Student Application",
    details=None,
    action_path="/menu/admin/applications/",
):
    """Notify admin of a new student, church user, church admin, or guest registration."""
    rows = student_identity_rows(student)
    if details:
        rows.extend(_normalize_details(details))
    rows.append(("Submitted At", format_timestamp(getattr(student, "created_at", None))))

    display_name = (
        student.get_full_name()
        if student and hasattr(student, "get_full_name")
        else dict(rows).get("Name") or dict(rows).get("Email") or "New Registrant"
    )
    return send_admin_notification(
        subject=f"New {registration_type}: {display_name}",
        title=f"New {registration_type}",
        summary=f"A new {registration_type.lower()} has been submitted and is ready for review.",
        details=rows,
        action_path=action_path,
        action_label="Review Applications",
        category="Registration",
    )


def notify_admin_student_approved(student, approved_by="Administration", is_church_user=False):
    """Notify admin when a student or church user account is approved."""
    role_label = "Church User" if is_church_user else "Student"
    rows = student_identity_rows(student)
    rows.extend([
        ("Account Type", role_label),
        ("Approved By", approved_by),
        ("Approved At", format_timestamp()),
    ])
    full_name = student.get_full_name() if student else "Unknown"
    return send_admin_notification(
        subject=f"{role_label} Approved: {full_name}",
        title=f"{role_label} Account Approved",
        summary=f"The {role_label.lower()} account for {full_name} has been approved.",
        details=rows,
        action_path=f"/menu/students/view/{student.id}/" if student else "/menu/admin/students/",
        action_label="View Student",
        category="Account Approval",
    )


def notify_admin_exam_submission(student_exam, has_errors=False, is_church_user=False, auto_ended=False):
    """Notify admin when a student or church user submits (or times out on) an exam."""
    student = getattr(student_exam, "student", None)
    exam = getattr(student_exam, "exam", None)
    subject_obj = getattr(student_exam, "subject", None) or (getattr(exam, "subject", None) if exam else None)

    rows = student_identity_rows(student)
    rows.extend([
        ("User Type", "Church User" if is_church_user else "Student"),
        ("Subject", getattr(subject_obj, "subject_name", "N/A") if subject_obj else "N/A"),
        ("Exam", getattr(exam, "exam_name", "N/A") if exam else "N/A"),
        ("Attempt", f"#{getattr(student_exam, 'attempt_number', 1) or 1}"),
        ("Objective/Current Score", str(getattr(student_exam, "show_on_score", 0) or 0)),
        ("Submission Mode", "Auto-closed (Timer Expired)" if auto_ended else "Submitted by Student"),
        ("Submitted At", format_timestamp(getattr(student_exam, "end_time", None))),
    ])
    if has_errors:
        rows.append(("Warning", "Partial answer-save warnings occurred during submission"))

    exam_name = getattr(exam, "exam_name", "Exam") if exam else "Exam"
    student_name = student.get_full_name() if student else "Student"
    return send_admin_notification(
        subject=f"Exam Submitted: {exam_name} - {student_name}",
        title="Exam Submission Received",
        summary=f"{student_name} has submitted the exam '{exam_name}'.",
        details=rows,
        action_path=f"/menu/admin/students/exam-answer-sheet/{student_exam.id}/",
        action_label="Review & Grade Answer Sheet",
        category="Exam Submission",
    )


def notify_admin_assignment_submission(student_assignment, is_church_user=False):
    """Notify admin when a student or church user submits an assignment."""
    student = getattr(student_assignment, "student", None)
    assignment = getattr(student_assignment, "assignment", None)
    subject_obj = getattr(assignment, "subject", None) if assignment else None

    rows = student_identity_rows(student)
    rows.extend([
        ("User Type", "Church User" if is_church_user else "Student"),
        ("Subject", getattr(subject_obj, "subject_name", "N/A") if subject_obj else "N/A"),
        ("Assignment", getattr(assignment, "assignment_name", "N/A") if assignment else "N/A"),
        ("Assignment Type", getattr(assignment, "assignment_type", "N/A") if assignment else "N/A"),
        ("Submitted At", format_timestamp(getattr(student_assignment, "submitted_on", None))),
    ])

    assignment_name = getattr(assignment, "assignment_name", "Assignment") if assignment else "Assignment"
    student_name = student.get_full_name() if student else "Student"
    return send_admin_notification(
        subject=f"Assignment Submitted: {assignment_name} - {student_name}",
        title="Assignment Submission Received",
        summary=f"{student_name} has submitted the assignment '{assignment_name}'.",
        details=rows,
        action_path=f"/menu/admin/students/assignment-answer-sheet/{student_assignment.id}/",
        action_label="Review & Grade Assignment",
        category="Assignment Submission",
    )


def notify_admin_payment(payment, payment_status="Paid", extra_details=None):
    """Notify admin whenever a fee payment is received or recorded."""
    student = getattr(payment, "student", None)
    rows = student_identity_rows(student)
    amount_val = getattr(payment, "amount", None)
    amount_str = f"${float(amount_val):.2f}" if amount_val is not None else "N/A"
    rows.extend([
        ("Payer Name", getattr(payment, "name", None) or "N/A"),
        ("Payer Email", getattr(payment, "email", None) or "N/A"),
        ("Phone", getattr(payment, "phone", None) or "N/A"),
        ("Group", getattr(payment, "person_group", None) or "N/A"),
        ("Amount", amount_str),
        ("Status", payment_status),
        ("Reference / Code", getattr(payment, "code", None) or "N/A"),
        ("Message", getattr(payment, "message", None) or "N/A"),
        ("Recorded At", format_timestamp()),
    ])
    if getattr(payment, "church_admin", None):
        rows.append(("Church", getattr(payment.church_admin, "name_of_church", "N/A")))
    if extra_details:
        rows.extend(_normalize_details(extra_details))

    payer_name = getattr(payment, "name", None) or (student.get_full_name() if student else "Payer")
    return send_admin_notification(
        subject=f"Fee Payment {payment_status}: {payer_name} ({amount_str})",
        title=f"Fee Payment {payment_status}",
        summary=f"A fee payment of {amount_str} from {payer_name} has been {payment_status.lower()}.",
        details=rows,
        action_path=f"/menu/payments/{payment.id}/view/" if getattr(payment, "id", None) else "/menu/admin/payments/",
        action_label="View Payment Details",
        category="Fee Payment",
    )


def notify_admin_request(request_type, student=None, details=None, action_path=None):
    """Notify admin of any student request (subject, exam, reschedule, retest, church admin, reference, etc.)."""
    rows = student_identity_rows(student)
    if details:
        rows.extend(_normalize_details(details))
    rows.append(("Requested At", format_timestamp()))

    actor_name = student.get_full_name() if student else dict(rows).get("Applicant Name") or dict(rows).get("Name") or "Student"
    return send_admin_notification(
        subject=f"{request_type}: {actor_name}",
        title=request_type,
        summary=f"{actor_name} submitted a {request_type.lower()}.",
        details=rows,
        action_path=action_path or "/menu/admin/dashboard",
        action_label="Review Request",
        category="Student Request",
    )


def notify_admin_chat_or_support(
    action_type,
    sender_name,
    sender_email=None,
    student=None,
    category=None,
    subject_text=None,
    message_text=None,
    extra_details=None,
    action_path=None,
):
    """Notify admin of support tickets, student/church chat replies, contact forms, or AI chat messages."""
    rows = student_identity_rows(student)
    if not student:
        rows.append(("Sender Name", sender_name or "Visitor"))
        if sender_email:
            rows.append(("Sender Email", sender_email))
    elif sender_email and sender_email != getattr(student, "email", None):
        rows.append(("Sender Email", sender_email))

    if category:
        rows.append(("Category", category))
    if subject_text:
        rows.append(("Subject", subject_text))
    if message_text:
        rows.append(("Message", message_text))
    if extra_details:
        rows.extend(_normalize_details(extra_details))
    rows.append(("Sent At", format_timestamp()))

    actor = sender_name or (student.get_full_name() if student else "Student")
    return send_admin_notification(
        subject=f"{action_type}: {actor}",
        title=action_type,
        summary=f"New message/chat activity ({action_type.lower()}) from {actor}.",
        details=rows,
        action_path=action_path or "/menu/admin/support",
        action_label="View Message in Admin",
        category="Chat & Support",
    )

