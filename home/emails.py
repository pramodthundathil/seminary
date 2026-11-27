"""
Centralized email notification and communications system for Trinity Theological Seminary.

Provides:
1. Admin notifications sent to `settings.ADMIN_EMAIL` (default: `admin@mytts.org`) for all
   critical events (student registrations, fee payments, church user registrations, church
   registrations, exam submissions, assignment submissions, requests, and support messages).
2. Beautifully themed, responsive, multi-part HTML + plain-text emails for students, church users,
   church admins, and guests, matching Trinity Theological Seminary's visual identity.
"""

import logging
import re
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
    if not emails:
        emails = ["admin@mytts.org"]
    return emails


def get_from_email():
    """Return the configured sender email address with display name."""
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if from_email and str(from_email).strip():
        return str(from_email).strip()
    user = getattr(settings, "EMAIL_HOST_USER", None) or "mytrinitytheologicalseminary@gmail.com"
    return f"Trinity Theological Seminary <{user}>"


def build_site_url(path=""):
    """
    Construct a full institutional URL using `settings.SITE_URL` (loaded from `.env`).
    Defaults to 'https://mytts.org/' if not explicitly set.
    All email action links and URLs are anchored to this base URL.
    """
    base_url = getattr(settings, "SITE_URL", None) or "https://mytts.org/"
    base_url = str(base_url).strip()
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"
    if not path:
        return base_url
    path_str = str(path).strip()
    if path_str.startswith(("http://", "https://")):
        # If an absolute local development URL was passed (e.g. 127.0.0.1 or localhost),
        # rewrite it to use the configured base_url from .env
        if "127.0.0.1" in path_str or "localhost" in path_str:
            from urllib.parse import urlparse
            parsed = urlparse(path_str)
            clean_path = parsed.path
            if parsed.query:
                clean_path += f"?{parsed.query}"
            return urljoin(base_url, clean_path.lstrip("/"))
        return path_str
    return urljoin(base_url, path_str.lstrip("/"))


def format_timestamp(dt=None):
    """Format a datetime cleanly for email display."""
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
    full_name = student.get_full_name() if hasattr(student, "get_full_name") else f"{getattr(student, 'first_name', '') or ''} {getattr(student, 'last_name', '') or ''}".strip()
    rows = [("Student Name", full_name or "N/A")]
    if getattr(student, "student_id", None):
        rows.append(("Student ID", student.student_id))
    if getattr(student, "email", None):
        rows.append(("Student Email", student.email))
    if getattr(student, "phone_number", None):
        pc = getattr(student, "phone_code", "") or ""
        rows.append(("Phone", f"+{pc} {student.phone_number}".strip() if pc else student.phone_number))
    if getattr(student, "course_applied", None):
        course_name = getattr(student.course_applied, "course_name", str(student.course_applied))
        rows.append(("Course Applied", course_name))
    if getattr(student, "country", None):
        country_name = getattr(student.country, "name", str(student.country))
        rows.append(("Country", country_name))
    elif getattr(student, "citizenship", None):
        cit_name = getattr(student.citizenship, "name", str(student.citizenship))
        rows.append(("Citizenship", cit_name))
    return rows


def _normalize_details(details):
    if not details:
        return []
    if isinstance(details, dict):
        items = list(details.items())
    else:
        items = list(details)
    return [(str(k), "N/A" if v in (None, "") else str(v)) for k, v in items]


# ==============================================================================
# BEAUTIFUL THEMED EMAIL BUILDER (BASE)
# ==============================================================================

def render_themed_email_html(
    category_label,
    title,
    lead_paragraph,
    details=None,
    highlight_box=None,
    action_button=None,
    footer_note=None,
):
    """
    Generate responsive, beautifully styled HTML fitting Trinity Theological Seminary's
    brand palette (Deep Navy #1B2845, Gradient to #0d9488, Cyan #00CED1 highlights).
    """
    detail_rows = _normalize_details(details)
    table_rows_html = "".join(
        f"""
        <tr>
          <th style="padding:11px 14px; text-align:left; background-color:#f8fafc; color:#475569; font-size:13px; font-weight:600; width:38%; border-bottom:1px solid #e2e8f0; vertical-align:top;">{escape(label)}</th>
          <td style="padding:11px 14px; color:#0f172a; font-size:14px; border-bottom:1px solid #e2e8f0; white-space:pre-wrap;">{escape(value)}</td>
        </tr>
        """
        for label, value in detail_rows
    )

    details_table_html = (
        f"""
        <table style="width:100%; border-collapse:collapse; margin:20px 0; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">
          {table_rows_html}
        </table>
        """
        if table_rows_html
        else ""
    )

    highlight_box_html = ""
    if highlight_box:
        title_text = highlight_box.get("title", "")
        items = highlight_box.get("items", [])
        box_theme = highlight_box.get("theme", "green")  # "green", "blue", "amber"

        if box_theme == "blue":
            box_bg = "#eff6ff"
            box_border = "#bfdbfe"
            box_left = "#2563eb"
            box_title_color = "#1e40af"
        elif box_theme == "amber":
            box_bg = "#fffbeb"
            box_border = "#fde68a"
            box_left = "#f59e0b"
            box_title_color = "#92400e"
        else:  # green / teal
            box_bg = "#ecfdf5"
            box_border = "#a7f3d0"
            box_left = "#10b981"
            box_title_color = "#065f46"

        items_html = "".join(
            f"""
            <div style="margin:6px 0; font-size:14px; color:#1e293b;">
              <span style="font-weight:600; color:#334155;">{escape(it_label)}:</span>
              <code style="font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace; font-size:15px; font-weight:700; background:#ffffff; padding:2px 8px; border-radius:4px; border:1px solid #cbd5e1; margin-left:6px; color:#0f172a;">{escape(it_val)}</code>
            </div>
            """
            for it_label, it_val in items
        )

        title_html = f'<div style="font-weight:700; font-size:15px; color:{box_title_color}; margin-bottom:8px;">{escape(title_text)}</div>' if title_text else ""
        note = highlight_box.get("note")
        note_html = f'<div style="font-size:12px; color:#64748b; margin-top:8px; font-style:italic;">{escape(note)}</div>' if note else ""

        highlight_box_html = f"""
        <div style="background:{box_bg}; border:1px solid {box_border}; border-left:4px solid {box_left}; border-radius:8px; padding:18px 20px; margin:22px 0;">
          {title_html}
          {items_html}
          {note_html}
        </div>
        """

    action_button_html = ""
    if action_button and action_button.get("url"):
        btn_label = action_button.get("label", "Click Here")
        btn_url = action_button.get("url", "#")
        btn_color = action_button.get("color", "gradient")  # "gradient", "green", "navy"
        if btn_color == "green":
            btn_bg = "#10b981"
            btn_shadow = "0 3px 8px rgba(16,185,129,0.3)"
        elif btn_color == "navy":
            btn_bg = "#1B2845"
            btn_shadow = "0 3px 8px rgba(27,40,69,0.3)"
        else:
            btn_bg = "linear-gradient(135deg, #0ea5e9, #1e3a8a)"
            btn_shadow = "0 4px 12px rgba(14,165,233,0.35)"

        action_button_html = f"""
        <div style="text-align:center; margin:28px 0 16px 0;">
          <a href="{escape(btn_url)}" style="display:inline-block; background:{btn_bg}; color:#ffffff !important; text-decoration:none; padding:13px 32px; border-radius:8px; font-weight:700; font-size:15px; letter-spacing:0.5px; box-shadow:{btn_shadow};">{escape(btn_label)}</a>
        </div>
        """

    footer_note_html = f"<p style='margin:12px 0 0 0; font-size:13px; color:#64748b;'>{escape(footer_note)}</p>" if footer_note else ""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background-color:#f1f5f9; margin:0; padding:24px 12px; color:#334155; -webkit-font-smoothing:antialiased;">
  <div style="max-width:640px; margin:0 auto; background:#ffffff; border-radius:12px; overflow:hidden; border:1px solid #e2e8f0; box-shadow:0 4px 18px rgba(15,23,42,0.06);">
    
    <!-- Header -->
    <div style="background:linear-gradient(135deg, #1B2845 0%, #1e3a8a 50%, #0d9488 100%); padding:28px 24px; text-align:center; color:#ffffff;">
      <div style="font-size:11px; text-transform:uppercase; letter-spacing:2px; color:#93c5fd; font-weight:700; margin-bottom:4px;">Trinity Theological Seminary</div>
      <div style="font-size:12px; text-transform:uppercase; letter-spacing:1px; color:#a7f3d0; margin-bottom:8px;">{escape(category_label)}</div>
      <h1 style="margin:0; font-size:22px; font-weight:700; line-height:1.3; color:#ffffff;">{escape(title)}</h1>
    </div>

    <!-- Main Content -->
    <div style="padding:28px 26px; color:#334155; font-size:14px; line-height:1.65;">
      <div style="margin-top:0; font-size:15px; color:#1e293b;">{lead_paragraph}</div>
      {highlight_box_html}
      {details_table_html}
      {action_button_html}
      {footer_note_html}
    </div>

    <!-- Institutional Footer -->
    <div style="background:#f8fafc; padding:18px 24px; text-align:center; font-size:12px; color:#64748b; border-top:1px solid #e2e8f0; line-height:1.5;">
      <div style="font-weight:600; color:#334155;">Trinity Theological Seminary</div>
      <div>Official Communications &bull; <a href="https://mytts.org" style="color:#0ea5e9; text-decoration:none;">mytts.org</a></div>
      <div style="margin-top:6px; font-size:11px; color:#94a3b8;">This is an automated institutional message. Please do not reply directly to this email.</div>
    </div>
  </div>
</body>
</html>"""


# ==============================================================================
# ADMIN NOTIFICATIONS (Sent to admin@mytts.org)
# ==============================================================================

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

    Exceptions are caught and logged so SMTP errors never disrupt user transactions.
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

    html_content = render_themed_email_html(
        category_label=f"Admin Alert &bull; {category}",
        title=title,
        lead_paragraph=f"<p style='margin:0;'>{escape(summary)}</p>",
        details=detail_rows,
        action_button={"label": action_label, "url": action_url, "color": "navy"} if action_url else None,
        footer_note=f"Logged at {format_timestamp()}",
    )

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
    registration_type="Student Registration",
    details=None,
    action_path=None,
):
    """Notify admin of a new student, church user, church admin, or guest registration."""
    rows = student_identity_rows(student)
    if details:
        rows.extend(_normalize_details(details))
    rows.append(("Submitted At", format_timestamp(getattr(student, "created_at", None))))

    display_name = (
        student.get_full_name()
        if student and hasattr(student, "get_full_name")
        else dict(rows).get("Name") or dict(rows).get("Email") or dict(rows).get("Student Name") or "New Registrant"
    )

    resolved_path = action_path or (f"/menu/students/view/{student.id}/" if student and getattr(student, "id", None) else "/menu/admin/applications/")

    return send_admin_notification(
        subject=f"New {registration_type}: {display_name}",
        title=f"New {registration_type}",
        summary=f"A new {registration_type.lower()} has been submitted for {display_name} and is ready for review.",
        details=rows,
        action_path=resolved_path,
        action_label="Review Application in Admin",
        category="Registration",
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
        ("Message / Purpose", getattr(payment, "message", None) or "N/A"),
        ("Recorded At", format_timestamp()),
    ])
    if getattr(payment, "church_admin", None):
        rows.append(("Church", getattr(payment.church_admin, "name_of_church", "N/A")))
    if extra_details:
        rows.extend(_normalize_details(extra_details))

    payer_name = getattr(payment, "name", None) or (student.get_full_name() if student else "Payer")
    action_path = f"/menu/payments/{payment.id}/view/" if getattr(payment, "id", None) else "/menu/admin/payments/"

    return send_admin_notification(
        subject=f"Fee Payment {payment_status}: {payer_name} ({amount_str})",
        title=f"Fee Payment {payment_status}",
        summary=f"A fee payment of {amount_str} from {payer_name} has been processed ({payment_status.lower()}).",
        details=rows,
        action_path=action_path,
        action_label="View Payment Record",
        category="Fee Payment",
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


# ==============================================================================
# BEAUTIFUL RECIPIENT EMAILS (Students, Church Users, Church Admins, Guests)
# ==============================================================================

def send_student_registration_email(
    student,
    temp_password=None,
    course=None,
    course_fee=0.0,
    payment_link=None,
):
    """
    Send a beautifully branded welcome and credentials email to the newly registered student.
    Handles both paid courses (with direct payment button) and free/sponsored courses.
    """
    if not student or not getattr(student, "email", None):
        logger.warning("send_student_registration_email: Missing student or email")
        return False

    first_name = getattr(student, "first_name", "") or "Student"
    student_id = getattr(student, "student_id", "") or "Assigned Upon Review"
    course_name = getattr(course, "course_name", None) or (
        getattr(student.course_applied, "course_name", "Selected Program")
        if getattr(student, "course_applied", None)
        else "Selected Program"
    )

    is_payment_required = float(course_fee or 0.0) > 0.0
    fee_str = f"${float(course_fee):.2f}" if is_payment_required else "No Fee / Sponsored"
    payment_status = "Pending Payment" if is_payment_required else "Complete / Enrolled"

    signin_url = build_site_url("/signin/")
    pay_url = build_site_url(payment_link) if payment_link else build_site_url("/register/payment/")

    subject = "Welcome to Trinity Theological Seminary - Your Registration Details"
    category_label = "Student Admissions &bull; Welcome"
    title = f"Welcome to Trinity, {first_name}!"

    lead_paragraph = f"""
    <p style="margin-top:0; font-size:15px; color:#1e293b;">
      Dear <strong>{escape(first_name)}</strong>,
    </p>
    <p>
      Thank you for applying to <strong>Trinity Theological Seminary</strong>. We are blessed to partner with you on your academic and spiritual journey. Your student application has been successfully received.
    </p>
    """

    # Highlight box for Credentials
    highlight_items = [
        ("Username / Login", student.email),
        ("Student ID", student_id),
    ]
    if temp_password:
        highlight_items.append(("Temporary Password", temp_password))

    highlight_box = {
        "title": "Your Student Account Credentials",
        "items": highlight_items,
        "note": "Please store these credentials securely. You can use them to log into the Student Portal.",
        "theme": "green",
    }

    # Summary details table
    details = [
        ("Student ID", student_id),
        ("Applicant Name", f"{getattr(student, 'first_name', '')} {getattr(student, 'last_name', '')}".strip()),
        ("Registered Email", student.email),
        ("Course / Program", course_name),
        ("Enrollment Fee", fee_str),
        ("Registration Status", payment_status),
    ]

    if is_payment_required:
        action_button = {
            "label": "Proceed to Complete Payment",
            "url": pay_url,
            "color": "green",
        }
        footer_note = f"To finalize your course enrollment, please complete your registration fee of {fee_str}. You may also log in at {signin_url} at any time."
    else:
        action_button = {
            "label": "Log In to Student Portal",
            "url": signin_url,
            "color": "gradient",
        }
        footer_note = "Your application is currently active. Please log in to complete your profile, view assigned textbooks, and review your course schedule."

    html_content = render_themed_email_html(
        category_label=category_label,
        title=title,
        lead_paragraph=lead_paragraph,
        details=details,
        highlight_box=highlight_box,
        action_button=action_button,
        footer_note=footer_note,
    )

    text_lines = [
        f"Dear {first_name},",
        "",
        "Welcome to Trinity Theological Seminary! Your student application has been successfully received.",
        "",
        "Your Account Details:",
        f"- Student ID: {student_id}",
        f"- Username / Email: {student.email}",
    ]
    if temp_password:
        text_lines.append(f"- Temporary Password: {temp_password}")
    text_lines.extend([
        f"- Course Applied: {course_name}",
        f"- Fee: {fee_str}",
        f"- Status: {payment_status}",
        "",
    ])
    if is_payment_required:
        text_lines.extend([
            f"Please complete your registration payment at: {pay_url}",
            "",
        ])
    text_lines.extend([
        f"Access the Student Portal: {signin_url}",
        "",
        "Blessings,",
        "Trinity Theological Seminary Admissions Team",
    ])
    text_content = "\n".join(text_lines)

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=get_from_email(),
            recipient_list=[student.email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Student registration email sent to %s", student.email)
        return True
    except Exception as exc:
        logger.error("Failed to send student registration email to %s: %s", student.email, exc, exc_info=True)
        return False


def send_payment_receipt_email(
    payment,
    student=None,
    church_admin=None,
    is_registration=False,
    extra_info=None,
):
    """
    Send an official, beautiful payment confirmation & receipt email to the student or payer.
    """
    payer_email = getattr(payment, "email", None) or (getattr(student, "email", None) if student else None)
    if not payer_email and church_admin and getattr(church_admin, "student", None):
        payer_email = getattr(church_admin.student, "email", None)

    if not payer_email:
        logger.warning("send_payment_receipt_email: No recipient email found for payment %s", getattr(payment, "id", None))
        return False

    student_obj = student or getattr(payment, "student", None)
    payer_name = getattr(payment, "name", None) or (student_obj.get_full_name() if student_obj else "Valued Student")
    amount_val = getattr(payment, "amount", None)
    amount_str = f"${float(amount_val):.2f}" if amount_val is not None else "$0.00"
    code = getattr(payment, "code", None) or f"TTS-PAY-{getattr(payment, 'id', 'REC')}"
    timestamp_str = format_timestamp()

    portal_url = build_site_url("/student/") if student_obj else build_site_url("/signin/")

    subject = f"Payment Receipt: {amount_str} - Trinity Theological Seminary"
    category_label = "Official Payment Receipt"
    title = "Payment Received & Confirmed"

    lead_paragraph = f"""
    <p style="margin-top:0; font-size:15px; color:#1e293b;">
      Dear <strong>{escape(payer_name)}</strong>,
    </p>
    <p>
      Thank you for your payment. We have successfully received and processed your payment of <strong style="color:#0f766e; font-size:16px;">{escape(amount_str)}</strong>. Please retain this email as your official transaction receipt.
    </p>
    """

    highlight_box = {
        "title": "Payment Summary",
        "items": [
            ("Amount Paid", amount_str),
            ("Receipt / Reference", code),
            ("Payment Status", "CONFIRMED & PAID"),
        ],
        "note": f"Transaction recorded on {timestamp_str}.",
        "theme": "green",
    }

    details = [
        ("Payer Name", payer_name),
        ("Payer Email", payer_email),
        ("Transaction Reference", code),
        ("Amount", amount_str),
        ("Payment Date", timestamp_str),
    ]
    if getattr(payment, "message", None):
        details.append(("Description", payment.message))
    if student_obj and getattr(student_obj, "student_id", None):
        details.append(("Student ID", student_obj.student_id))
    if extra_info:
        details.append(("Additional Info", extra_info))

    action_button = {
        "label": "Access Your Dashboard",
        "url": portal_url,
        "color": "gradient",
    }
    footer_note = "If you have any questions regarding this transaction, please contact the seminary finance office at billing@mytts.org."

    html_content = render_themed_email_html(
        category_label=category_label,
        title=title,
        lead_paragraph=lead_paragraph,
        details=details,
        highlight_box=highlight_box,
        action_button=action_button,
        footer_note=footer_note,
    )

    text_content = f"""Dear {payer_name},

Thank you for your payment to Trinity Theological Seminary.

Payment Receipt:
- Amount Paid: {amount_str}
- Reference Code: {code}
- Status: Confirmed & Paid
- Date: {timestamp_str}
- Payer: {payer_name} ({payer_email})

Access your dashboard: {portal_url}

Thank you for your support and partnership.
Trinity Theological Seminary Finance Department
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=get_from_email(),
            recipient_list=[payer_email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Payment receipt email sent to %s for %s", payer_email, amount_str)
        return True
    except Exception as exc:
        logger.error("Failed to send payment receipt email to %s: %s", payer_email, exc, exc_info=True)
        return False


def send_church_user_welcome_email(student, church_admin_obj=None, temp_password=None):
    """
    Send a beautifully styled confirmation email to a newly registered Church User.
    """
    if not student or not getattr(student, "email", None):
        return False

    first_name = getattr(student, "first_name", "Church Member")
    email = student.email
    church_name = getattr(church_admin_obj, "name_of_church", "Your Affiliated Church") if church_admin_obj else "Your Affiliated Church"
    church_code = getattr(church_admin_obj, "code", "") if church_admin_obj else ""

    subject = "Church User Registration - Trinity Theological Seminary"
    category_label = "Church Partnership &bull; User Registration"
    title = f"Welcome, {first_name}!"

    lead_paragraph = f"""
    <p style="margin-top:0; font-size:15px; color:#1e293b;">
      Dear <strong>{escape(first_name)}</strong>,
    </p>
    <p>
      Your account under <strong>{escape(church_name)}</strong> has been created successfully.
    </p>
    <p>
      <strong>Next Step:</strong> To maintain institutional integrity, your account requires authorization from both <strong>Trinity Theological Seminary</strong> and your <strong>Church Administrator</strong> before courses and exams are unlocked. You will receive an email as soon as your access is activated.
    </p>
    """

    highlight_items = [
        ("Login Email", email),
        ("Affiliated Church", church_name),
    ]
    if church_code:
        highlight_items.append(("Church Code", church_code))
    if temp_password:
        highlight_items.append(("Temporary Password", temp_password))

    highlight_box = {
        "title": "Account & Affiliation Details",
        "items": highlight_items,
        "note": "Account Status: Pending Church Admin & Seminary Approval.",
        "theme": "blue",
    }

    details = [
        ("Full Name", f"{getattr(student, 'first_name', '')} {getattr(student, 'last_name', '')}".strip()),
        ("Email Address", email),
        ("Church Affiliation", church_name),
        ("Approval Status", "Pending Approval"),
        ("Registered At", format_timestamp()),
    ]

    signin_url = build_site_url("/signin/")
    action_button = {
        "label": "Visit Portal Sign-in",
        "url": signin_url,
        "color": "navy",
    }

    html_content = render_themed_email_html(
        category_label=category_label,
        title=title,
        lead_paragraph=lead_paragraph,
        details=details,
        highlight_box=highlight_box,
        action_button=action_button,
        footer_note="Your Church Administrator has been alerted to review and approve your registration.",
    )

    text_content = f"""Dear {first_name},

Your church user account under {church_name} (Code: {church_code}) has been created successfully.

Please note: Your account requires approval from Trinity Theological Seminary and your Church Administrator before access is granted.

Login Email: {email}
Status: Pending Approval
Login Portal: {signin_url}

Best regards,
Trinity Theological Seminary
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=get_from_email(),
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Church user welcome email sent to %s", email)
        return True
    except Exception as exc:
        logger.error("Failed to send church user welcome email to %s: %s", email, exc, exc_info=True)
        return False


def send_church_admin_welcome_email(
    church_admin_obj,
    student,
    temp_password=None,
    payment_link=None,
):
    """
    Send an official welcome and setup email to a newly registered Church Administrator / Pastor.
    """
    recipient_email = getattr(student, "email", None)
    if not recipient_email:
        return False

    first_name = getattr(student, "first_name", "Pastor / Church Admin")
    church_name = getattr(church_admin_obj, "name_of_church", "Church")
    code = getattr(church_admin_obj, "code", "N/A")
    amount = float(getattr(church_admin_obj, "amount", 0.0) or 0.0)
    is_paid = getattr(church_admin_obj, "is_paid", False)

    subject = f"Church Registration Confirmation: {church_name} - Trinity Theological Seminary"
    category_label = "Church Leadership &bull; New Church Registration"
    title = f"Welcome, {first_name}!"

    pay_url = build_site_url(payment_link) if payment_link else build_site_url("/register/payment/")
    signin_url = build_site_url("/signin/")

    lead_paragraph = f"""
    <p style="margin-top:0; font-size:15px; color:#1e293b;">
      Dear <strong>{escape(first_name)}</strong>,
    </p>
    <p>
      Thank you for registering <strong>{escape(church_name)}</strong> with the Trinity Theological Seminary Church Partnership Program. Your unique church enrollment code has been generated.
    </p>
    """

    highlight_items = [
        ("Church Name", church_name),
        ("Your Church Code", code),
        ("Admin Email", recipient_email),
    ]
    if temp_password:
        highlight_items.append(("Temporary Password", temp_password))
    highlight_items.append(("Payment Status", "Paid" if is_paid else f"Pending Payment (${amount:.2f})"))

    highlight_box = {
        "title": "Your Church Code & Credentials",
        "items": highlight_items,
        "note": "Members of your congregation will use this Church Code when registering.",
        "theme": "amber" if not is_paid else "green",
    }

    details = [
        ("Church Name", church_name),
        ("Pastor / Administrator", f"{getattr(student, 'first_name', '')} {getattr(student, 'last_name', '')}".strip()),
        ("Church Code", code),
        ("Registration Fee", f"${amount:.2f}"),
        ("Max Member Seats", str(getattr(church_admin_obj, "max_user_no", "Standard"))),
        ("Status", "Active" if is_paid else "Pending Payment / Approval"),
    ]

    if not is_paid and amount > 0:
        action_button = {
            "label": "Complete Church Registration Fee",
            "url": pay_url,
            "color": "green",
        }
        footer_note = f"Please complete your registration payment of ${amount:.2f} to activate your church admin dashboard."
    else:
        action_button = {
            "label": "Access Church Admin Dashboard",
            "url": signin_url,
            "color": "navy",
        }
        footer_note = "Your church code is ready. You can share this code with members of your congregation."

    html_content = render_themed_email_html(
        category_label=category_label,
        title=title,
        lead_paragraph=lead_paragraph,
        details=details,
        highlight_box=highlight_box,
        action_button=action_button,
        footer_note=footer_note,
    )

    text_content = f"""Dear {first_name},

Thank you for registering {church_name} with Trinity Theological Seminary!

Church Details:
- Church Name: {church_name}
- Church Code: {code}
- Admin Email: {recipient_email}
- Fee: ${amount:.2f}
- Status: {'Active' if is_paid else 'Pending Payment'}

Portal: {signin_url}

Best regards,
Trinity Theological Seminary Church Partnership Team
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=get_from_email(),
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Church admin welcome email sent to %s", recipient_email)
        return True
    except Exception as exc:
        logger.error("Failed to send church admin welcome email to %s: %s", recipient_email, exc, exc_info=True)
        return False


def send_church_admin_approval_request_email(church_admin_obj, church_user):
    """
    Send an HTML notification to the Church Administrator (Pastor) when a new user
    registers using their church code and requires approval.
    """
    pastor_email = None
    pastor_name = "Church Administrator"
    if church_admin_obj and getattr(church_admin_obj, "student", None):
        pastor_email = church_admin_obj.student.email
        pastor_name = church_admin_obj.student.first_name or "Church Administrator"

    if not pastor_email:
        return False

    user_name = f"{getattr(church_user, 'first_name', '')} {getattr(church_user, 'last_name', '')}".strip() or "Church Member"
    user_email = getattr(church_user, "email", "N/A")
    church_name = getattr(church_admin_obj, "name_of_church", "your church")

    subject = f"Member Registration - Approval Required: {user_name}"
    category_label = "Church Administration &bull; Action Required"
    title = "New Member Registration Awaiting Approval"

    dashboard_url = build_site_url("/church/admin-dashboard/")

    lead_paragraph = f"""
    <p style="margin-top:0; font-size:15px; color:#1e293b;">
      Hello <strong>{escape(pastor_name)}</strong>,
    </p>
    <p>
      A new member has registered using your church code for <strong>{escape(church_name)}</strong> and is awaiting your authorization.
    </p>
    """

    details = [
        ("Member Name", user_name),
        ("Member Email", user_email),
        ("Phone", getattr(church_user, "phone_number", "N/A")),
        ("Church Affiliation", church_name),
        ("Registration Date", format_timestamp()),
    ]

    action_button = {
        "label": "Review & Approve Member",
        "url": dashboard_url,
        "color": "navy",
    }

    html_content = render_themed_email_html(
        category_label=category_label,
        title=title,
        lead_paragraph=lead_paragraph,
        details=details,
        action_button=action_button,
        footer_note="Please log in to your Church Admin Dashboard to review and activate this member's access.",
    )

    text_content = f"""Hello {pastor_name},

A new user has registered under your church code for {church_name} and requires your approval.

Details:
- Name: {user_name}
- Email: {user_email}
- Phone: {getattr(church_user, 'phone_number', 'N/A')}

Please log in to your Church Admin Dashboard to review and approve this member:
{dashboard_url}

Best regards,
Trinity Theological Seminary
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=get_from_email(),
            recipient_list=[pastor_email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Church admin approval request sent to %s for user %s", pastor_email, user_email)
        return True
    except Exception as exc:
        logger.error("Failed to send church admin approval request to %s: %s", pastor_email, exc, exc_info=True)
        return False


def send_guest_welcome_email(user, guest_id, temp_password):
    """
    Send a beautifully styled welcome email with credentials to a newly registered guest.
    """
    recipient_email = getattr(user, "email", None)
    if not recipient_email:
        return False

    name = getattr(user, "name", "Guest Visitor")
    signin_url = build_site_url("/signin/")

    subject = "Your Guest Account - Trinity Theological Seminary"
    category_label = "Guest Registration &bull; Welcome"
    title = f"Welcome, {name}!"

    lead_paragraph = f"""
    <p style="margin-top:0; font-size:15px; color:#1e293b;">
      Dear <strong>{escape(name)}</strong>,
    </p>
    <p>
      Your guest account at <strong>Trinity Theological Seminary</strong> has been created successfully. You may now log in to explore guest courses and resources.
    </p>
    """

    highlight_box = {
        "title": "Your Guest Login Credentials",
        "items": [
            ("Email", recipient_email),
            ("Guest ID / Username", guest_id),
            ("Temporary Password", temp_password),
        ],
        "note": "Please change your temporary password upon logging in.",
        "theme": "blue",
    }

    details = [
        ("Guest Name", name),
        ("Email Address", recipient_email),
        ("Guest ID", guest_id),
        ("Created At", format_timestamp()),
    ]

    action_button = {
        "label": "Log In as Guest",
        "url": signin_url,
        "color": "gradient",
    }

    html_content = render_themed_email_html(
        category_label=category_label,
        title=title,
        lead_paragraph=lead_paragraph,
        details=details,
        highlight_box=highlight_box,
        action_button=action_button,
        footer_note="If you did not request this account, please contact support@mytts.org.",
    )

    text_content = f"""Dear {name},

Your guest account at Trinity Theological Seminary has been created successfully.

Login Details:
- Email: {recipient_email}
- Guest ID: {guest_id}
- Temporary Password: {temp_password}

Login URL: {signin_url}

Best regards,
Trinity Theological Seminary
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=get_from_email(),
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Guest welcome email sent to %s", recipient_email)
        return True
    except Exception as exc:
        logger.error("Failed to send guest welcome email to %s: %s", recipient_email, exc, exc_info=True)
        return False


def send_student_approval_email(student, temp_password=None, approved_by="Administration"):
    """
    Send a beautifully branded approval notification to a newly approved student or church user.
    Includes login credentials and a direct link to the portal.
    """
    if not student or not getattr(student, "email", None):
        return False

    recipient_email = student.email
    full_name = student.get_full_name() or "Student"
    login_url = build_site_url("/login/")
    is_church_user = bool(getattr(student, "user", None) and getattr(student.user, "church_admin", None))
    role_label = "Church Member / Student" if is_church_user else "Student"

    subject = f"Registration Approved: Welcome to Trinity Theological Seminary - {full_name}"
    category_label = "Enrollment Approved"
    title = "Your Registration Has Been Approved!"
    lead_paragraph = (
        f"Dear {escape(full_name)},<br><br>"
        f"We are delighted to inform you that your registration as a <strong>{escape(role_label)}</strong> "
        f"at Trinity Theological Seminary has been approved by {escape(str(approved_by))}. "
        f"You may now log in to the student portal to access your courses, materials, and dashboard."
    )

    highlight_items = [
        ("Username / Email", recipient_email),
    ]
    if temp_password:
        highlight_items.append(("Temporary Password", temp_password))
    highlight_items.append(("Portal URL", login_url))

    highlight_box = {
        "title": "Your Login Credentials",
        "items": highlight_items,
        "note": "For security reasons, please change your password immediately after your first login." if temp_password else "You can log in using your existing credentials.",
        "theme": "teal",
    }

    course_name = getattr(student.course_applied, "course_name", "General Curriculum") if getattr(student, "course_applied", None) else "Church Program"

    details = [
        ("Student / User ID", student.student_id or "N/A"),
        ("Full Name", full_name),
        ("Email Address", recipient_email),
        ("Program / Course", course_name),
        ("Approved By", str(approved_by)),
        ("Approved At", format_timestamp()),
    ]

    action_button = {
        "label": "Log In to Student Portal",
        "url": login_url,
        "color": "gradient",
    }

    html_content = render_themed_email_html(
        category_label=category_label,
        title=title,
        lead_paragraph=lead_paragraph,
        details=details,
        highlight_box=highlight_box,
        action_button=action_button,
        footer_note="If you experience any issues logging in, please contact admin@mytts.org for assistance.",
    )

    pwd_line = f"- Temporary Password: {temp_password}\n" if temp_password else ""
    text_content = f"""Dear {full_name},

Your registration at Trinity Theological Seminary has been approved by {approved_by}!

Login Details:
- Portal URL: {login_url}
- Username / Email: {recipient_email}
{pwd_line}
Important: Please change your password upon logging in.

Best regards,
Trinity Theological Seminary
"""

    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=get_from_email(),
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info("Student approval email sent to %s", recipient_email)
        return True
    except Exception as exc:
        logger.error("Failed to send student approval email to %s: %s", recipient_email, exc, exc_info=True)
        return False

