from datetime import timedelta
from decimal import Decimal
import json
from unittest.mock import Mock, patch

from django.conf import settings
from django.core import mail
from django.template import TemplateDoesNotExist
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from home.emails import get_admin_emails, send_admin_notification
from home.models import (
    Assignments,
    Branches,
    ChurchAdminApplication,
    ChurchAdmins,
    ChurchLoginCodeSettings,
    Contacts,
    Countries,
    Courses,
    DescriptiveQuestions,
    Exams,
    Languages,
    ObjectiveQuestions,
    Payments,
    Qualifications,
    ReferenceForm,
    RoleUsers,
    Roles,
    Students,
    StudentsAssignment,
    StudentsExams,
    StudentsSubjects,
    Subjects,
    Support,
    Users,
)
from student.views import send_admin_payment_notification


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ADMIN_EMAIL="admin@mytts.org",
    DEFAULT_FROM_EMAIL="mytrinitytheologicalseminary@gmail.com",
    SITE_URL="http://127.0.0.1:8000/",
)
class AdminEmailNotificationSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        mail.outbox = []

        self.role_student = Roles.objects.create(name="Student", guard_name="web")
        self.role_church_user = Roles.objects.create(name="Church User", guard_name="web")
        self.role_admin = Roles.objects.create(name="Admin", guard_name="web")

        # Admin user (created first so created_by/updated_by FKs can reference it)
        self.admin_user = Users.objects.create(
            name="Super Admin",
            email="admin@mytts.org",
            username="superadmin",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        self.admin_user.set_password("secret123")
        self.admin_user.save()
        RoleUsers.objects.create(user=self.admin_user, role=self.role_admin)

        now = timezone.now()
        self.language = Languages.objects.create(
            language_name="English",
            status=True,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.country = Countries.objects.create(
            sortname="US", name="United States", phonecode=1, created_at=now
        )
        self.qualification = Qualifications.objects.create(
            qualification_name="Bachelor",
            display_order=1,
            status=True,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.branch = Branches.objects.create(
            branch_name="Main Branch",
            branch_code="MAIN",
            is_associate_degree=True,
            status=True,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.course_paid = Courses.objects.create(
            course_code="BTH",
            course_name="Bachelor of Theology",
            highest_qualification=self.qualification,
            credit_hours=110,
            fees=150.0,
            status=1,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.course_free = Courses.objects.create(
            course_code="FREE",
            course_name="Free Certificate",
            highest_qualification=self.qualification,
            credit_hours=20,
            fees=0.0,
            status=1,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.package = ChurchLoginCodeSettings.objects.create(
            name="Starter Church Package",
            branches=self.branch,
            max_user_no=10,
            amount=50.0,
            expired_in_days="365",
            status=1,
        )

        # Active paid student
        self.student_user = Users.objects.create(
            name="John Student",
            email="john.student@example.com",
            username="john.student@example.com",
            is_active=True,
        )
        self.student_user.set_password("secret123")
        self.student_user.save()
        RoleUsers.objects.create(user=self.student_user, role=self.role_student)
        self.student = Students.objects.create(
            student_id="TTSBTH0001",
            user=self.student_user,
            first_name="John",
            last_name="Student",
            email="john.student@example.com",
            timezone="UTC",
            language=self.language,
            course_applied=self.course_paid,
            country=self.country,
            citizenship=self.country,
            phone_number="1234567890",
            status=True,
            active=True,
            is_paid=True,
        )

        # Church admin + church user
        self.ca_user = Users.objects.create(
            name="Pastor Admin",
            email="pastor@church.org",
            username="pastor@church.org",
            is_active=True,
        )
        self.ca_user.set_password("secret123")
        self.ca_user.save()
        self.ca_student = Students.objects.create(
            student_id="CHAB001",
            user=self.ca_user,
            first_name="Pastor",
            last_name="Admin",
            email="pastor@church.org",
            timezone="UTC",
            language=self.language,
            status=True,
            active=True,
            is_paid=True,
        )
        self.church_admin = ChurchAdmins.objects.create(
            student=self.ca_student,
            name_of_church="Grace Chapel",
            name_of_paster="Pastor Admin",
            church_code=self.package,
            code="GRACE1",
            amount=50.0,
            max_user_no=10,
            current_user_no=2,
            is_paid=True,
        )

        self.church_user = Users.objects.create(
            name="Mary Church",
            email="mary.church@example.com",
            username="mary.church@example.com",
            church_admin=self.church_admin,
            is_active=True,
        )
        self.church_user.set_password("secret123")
        self.church_user.save()
        RoleUsers.objects.create(user=self.church_user, role=self.role_church_user)
        self.church_student = Students.objects.create(
            student_id="CHUB001",
            user=self.church_user,
            first_name="Mary",
            last_name="Church",
            email="mary.church@example.com",
            timezone="UTC",
            language=self.language,
            status=True,
            active=True,
            is_paid=True,
        )

        # Subject, Exam, Assignment
        self.subject = Subjects.objects.create(
            subject_code="BIB101",
            subject_name="Biblical Foundations",
            branches=self.branch,
            no_of_exams=1,
            class_hours=Decimal("10.00"),
            fees=25.0,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.other_subject = Subjects.objects.create(
            subject_code="THE201",
            subject_name="Systematic Theology",
            branches=self.branch,
            no_of_exams=1,
            class_hours=Decimal("10.00"),
            fees=30.0,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        StudentsSubjects.objects.create(
            student=self.student,
            subject=self.subject,
            is_approved=True,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )

        self.exam = Exams.objects.create(
            code="EX101",
            exam_name="Foundations Midterm",
            exam_type="objective",
            subject=self.subject,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.obj_q = ObjectiveQuestions.objects.create(
            exam=self.exam,
            question="Who led the Israelites out of Egypt?",
            option1="Moses",
            option2="David",
            option3="Noah",
            option4="Abraham",
            answer_option="option1",
            marks=10,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.desc_q = DescriptiveQuestions.objects.create(
            exam=self.exam,
            question="Summarize Genesis 1.",
            mark=20,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )

        self.assignment = Assignments.objects.create(
            code="ASN101",
            assignment_name="Hermeneutics Essay",
            assignment_type="paper_submit",
            subject=self.subject,
            total_score=100,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )

    def _admin_emails(self):
        return [m for m in mail.outbox if "admin@mytts.org" in m.to]

    def _mock_recaptcha_ok(self):
        resp = Mock()
        resp.json.return_value = {"success": True}
        return resp

    def test_settings_and_helper_defaults(self):
        self.assertEqual(settings.ADMIN_EMAIL, "admin@mytts.org")
        self.assertEqual(get_admin_emails(), ["admin@mytts.org"])

        ok = send_admin_notification(
            subject="Test Subject",
            title="Test Title",
            summary="Summary <script>alert(1)</script>",
            details=[("Field", "Value & <tag>")],
            action_path="/menu/admin/dashboard",
        )
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@mytts.org"])
        self.assertEqual(mail.outbox[0].from_email, "mytrinitytheologicalseminary@gmail.com")
        self.assertIn("&lt;script&gt;", mail.outbox[0].alternatives[0][0])

    def test_helper_resilience_on_smtp_failure(self):
        with patch("home.emails.send_mail", side_effect=RuntimeError("SMTP down")):
            ok = send_admin_notification("Test", "Title", "Summary")
        self.assertFalse(ok)

    def test_student_registration_paid_and_free_send_admin_email(self):
        # Paid course registration
        res = self.client.post(
            reverse("signup_student"),
            {
                "first_name": "Alice",
                "last_name": "Paid",
                "email": "alice.paid@example.com",
                "gender": "Female",
                "phone_code": "1",
                "phone_number": "5550001111",
                "date_of_birth": "1998-01-15",
                "timezone": "UTC",
                "course_applied": self.course_paid.id,
                "language": self.language.id,
                "country": self.country.id,
                "citizenship": self.country.id,
            },
        )
        self.assertEqual(res.status_code, 302)
        admin_msgs = self._admin_emails()
        self.assertEqual(len(admin_msgs), 1)
        self.assertIn("Alice Paid", admin_msgs[0].subject)
        self.assertIn("Pending Payment", admin_msgs[0].body)

        # Free course registration
        mail.outbox = []
        res2 = self.client.post(
            reverse("signup_student"),
            {
                "first_name": "Bob",
                "last_name": "Free",
                "email": "bob.free@example.com",
                "gender": "Male",
                "phone_code": "1",
                "phone_number": "5550002222",
                "date_of_birth": "1997-02-20",
                "timezone": "UTC",
                "course_applied": self.course_free.id,
                "language": self.language.id,
                "country": self.country.id,
                "citizenship": self.country.id,
            },
        )
        self.assertEqual(res2.status_code, 302)
        admin_msgs2 = self._admin_emails()
        self.assertEqual(len(admin_msgs2), 1)
        self.assertIn("Bob Free", admin_msgs2[0].subject)
        self.assertNotIn("contact@byteboot.in", str(admin_msgs2[0].to))

    @patch("home.views.requests.post")
    def test_guest_and_church_registrations_send_admin_email(self, mock_post):
        mock_post.return_value = self._mock_recaptcha_ok()

        # Guest registration
        res = self.client.post(
            reverse("guest_register"),
            {
                "first_name": "Gary",
                "last_name": "Guest",
                "email": "gary.guest@example.com",
                "phone_code": "1",
                "phone_number": "5551112222",
                "date_of_birth": "1995-05-05",
                "gender": "Male",
                "mailing_address": "123 Main St",
                "city": "Dallas",
                "state": "TX",
                "country": self.country.id,
                "zipcode": "75001",
                "timezone": "UTC",
                "language": self.language.id,
                "church_affiliation": "Hope Church",
                "associate_degree": self.branch.id,
                "g-recaptcha-response": "ok",
            },
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Guest Registration", self._admin_emails()[0].subject)

        # Church user registration
        mail.outbox = []
        res_cu = self.client.post(
            reverse("church_admin_register"),
            {
                "register_as": "user",
                "first_name": "Clara",
                "last_name": "ChurchUser",
                "email": "clara.cu@example.com",
                "phone_code": "1",
                "phone_number": "5553334444",
                "date_of_birth": "1994-03-10",
                "gender": "Female",
                "mailing_address": "456 Oak St",
                "city": "Austin",
                "state": "TX",
                "country": self.country.id,
                "zipcode": "78701",
                "timezone": "UTC",
                "language": self.language.id,
                "church_code": "GRACE1",
                "church_affiliation": "Grace Chapel",
                "g-recaptcha-response": "ok",
            },
        )
        self.assertEqual(res_cu.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Church User Registration", self._admin_emails()[0].subject)

        # Church admin registration
        mail.outbox = []
        res_ca = self.client.post(
            reverse("church_admin_register"),
            {
                "register_as": "admin",
                "first_name": "David",
                "last_name": "ChurchAdmin",
                "email": "david.ca@example.com",
                "phone_code": "1",
                "phone_number": "5554445555",
                "date_of_birth": "1985-08-12",
                "gender": "Male",
                "mailing_address": "789 Pine St",
                "city": "Houston",
                "state": "TX",
                "country": self.country.id,
                "zipcode": "77001",
                "timezone": "UTC",
                "language": self.language.id,
                "associate_degree": self.branch.id,
                "package": self.package.id,
                "name_of_church": "New Life Church",
                "g-recaptcha-response": "ok",
            },
        )
        self.assertEqual(res_ca.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Church Admin Registration", self._admin_emails()[0].subject)

    @patch("home.views.requests.post")
    def test_contact_reference_and_chatbot_send_admin_email(self, mock_post):
        mock_post.return_value = self._mock_recaptcha_ok()

        # Contact Us
        res_contact = self.client.post(
            reverse("contact-us"),
            {
                "name": "Sam Visitor",
                "email": "sam@example.com",
                "subject": "Admission Question",
                "message": "How do I enroll?",
                "g-recaptcha-response": "ok",
            },
        )
        self.assertEqual(res_contact.status_code, 302)
        self.assertEqual(Contacts.objects.count(), 1)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Contact Us Inquiry", self._admin_emails()[0].subject)

        # Reference Form
        mail.outbox = []
        res_ref = self.client.post(
            reverse("reference_form"),
            {
                "first_name": "Pastor",
                "last_name": "Ref",
                "email": "ref@church.org",
                "contact": "5559990000",
                "nationality": "US",
                "applicant_name": "John Student",
                "relationship": "Pastor",
                "known_since": "2020",
                "spiritual_commitment": "Excellent",
                "biblical_knowledge": "Good",
                "recommendation": "Highly Recommend",
                "comments": "Strong character.",
                "g-recaptcha-response": "ok",
            },
        )
        self.assertEqual(res_ref.status_code, 302)
        self.assertEqual(ReferenceForm.objects.count(), 1)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Reference Form Submission", self._admin_emails()[0].subject)

        # AI Chatbot
        mail.outbox = []
        with patch(
            "home.views.generate_chat_reply",
            return_value={"success": True, "reply": "You can apply online.", "model": "gemini"},
        ):
            res_chat = self.client.post(
                reverse("chatbot_api"),
                data=json.dumps({"message": "How do I apply?", "history": []}),
                content_type="application/json",
            )
        self.assertEqual(res_chat.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("AI Chatbot Message", self._admin_emails()[0].subject)

    def test_student_and_church_exam_submissions_send_admin_email(self):
        # Student exam submission
        self.client.force_login(self.student_user)
        se = StudentsExams.objects.create(
            student=self.student,
            course=self.course_paid,
            subject=self.subject,
            exam=self.exam,
            start_time=timezone.now() - timedelta(minutes=15),
            is_approved=True,
            is_exam_started=True,
            timezone="UTC",
            show_on_score=0,
            created_by=self.student_user,
            updated_by=self.student_user,
        )
        res = self.client.post(
            reverse("submit_exam", args=[se.id]),
            {
                f"obj_q_{self.obj_q.id}": "1",
                f"desc_q_{self.desc_q.id}": "God created the heavens and the earth.",
            },
        )
        self.assertEqual(res.status_code, 302)
        se.refresh_from_db()
        self.assertTrue(se.is_exam_ended)
        self.assertEqual(se.show_on_score, 10)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Exam Submitted", self._admin_emails()[0].subject)
        self.assertIn("Foundations Midterm", self._admin_emails()[0].body)

        # Church user exam submission
        mail.outbox = []
        self.client.force_login(self.church_user)
        cu_se = StudentsExams.objects.create(
            student=self.church_student,
            subject=self.subject,
            exam=self.exam,
            start_time=timezone.now() - timedelta(minutes=10),
            is_approved=True,
            is_exam_started=True,
            timezone="UTC",
            show_on_score=0,
            created_by=self.church_user,
            updated_by=self.church_user,
        )
        res_cu = self.client.post(
            reverse("church_user_submit_exam", args=[cu_se.id]),
            {
                f"obj_q_{self.obj_q.id}": "1",
                f"desc_q_{self.desc_q.id}": "Creation summary.",
            },
        )
        self.assertEqual(res_cu.status_code, 302)
        cu_se.refresh_from_db()
        self.assertTrue(cu_se.is_exam_ended)
        self.assertEqual(cu_se.show_on_score, 10)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Exam Submitted", self._admin_emails()[0].subject)
        self.assertIn("Church User", self._admin_emails()[0].body)

    def test_student_and_church_assignment_submissions_send_admin_email(self):
        # Student assignment submission
        self.client.force_login(self.student_user)
        sa = StudentsAssignment.objects.create(
            student=self.student,
            assignment=self.assignment,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        res = self.client.post(
            reverse("submit_assignment", args=[sa.id]),
            {"answer_text": "My hermeneutics essay response."},
        )
        self.assertEqual(res.status_code, 302)
        sa.refresh_from_db()
        self.assertIsNotNone(sa.submitted_on)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Assignment Submitted", self._admin_emails()[0].subject)

        # Church user submit_assignment view
        mail.outbox = []
        self.client.force_login(self.church_user)
        cu_sa = StudentsAssignment.objects.create(
            student=self.church_student,
            assignment=self.assignment,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        res_cu = self.client.post(
            reverse("church_submit_assignment", args=[cu_sa.id]),
            {"answer_text": "Church user assignment response."},
        )
        self.assertEqual(res_cu.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Assignment Submitted", self._admin_emails()[0].subject)

        # Church user view_assignment direct POST
        mail.outbox = []
        asn2 = Assignments.objects.create(
            code="ASN102",
            assignment_name="Exegesis Paper",
            assignment_type="paper_submit",
            subject=self.subject,
            total_score=100,
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        res_cu2 = self.client.post(
            reverse("church_user_view_assignment", args=[asn2.id]),
            {"answer_text": "Exegesis response."},
        )
        self.assertEqual(res_cu2.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Exegesis Paper", self._admin_emails()[0].subject)

    def test_student_requests_and_profile_actions_send_admin_email(self):
        self.client.force_login(self.student_user)

        # Subject request
        res_sub = self.client.post(
            reverse("request_subject"), {"subject_id": self.other_subject.id}
        )
        self.assertEqual(res_sub.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Subject Request", self._admin_emails()[0].subject)

        # Exam request
        mail.outbox = []
        res_ex = self.client.post(
            reverse("submit-request-exam"),
            {
                "subject": self.subject.id,
                "exam": self.exam.id,
                "timezone": "UTC",
                "examDate": "2026-12-01",
                "startTime": "10:00",
            },
        )
        self.assertEqual(res_ex.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Exam Schedule Request", self._admin_emails()[0].subject)

        # Reschedule (missed) + retest request
        se = StudentsExams.objects.filter(student=self.student, exam=self.exam).first()
        mail.outbox = []
        res_resched = self.client.post(
            reverse("student_reschedule_exam"),
            {
                "exam_id": se.id,
                "examDate": "2026-12-05",
                "startTime": "14:00",
                "timezone": "UTC",
            },
        )
        self.assertEqual(res_resched.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Exam Reschedule", self._admin_emails()[0].subject)

        # Retest request via scorecard
        se.is_exam_ended = True
        se.is_exam_started = True
        se.save()
        mail.outbox = []
        res_retest = self.client.post(
            reverse("student_request_retest", args=[se.id]),
            {"examDate": "2026-12-10", "startTime": "15:00", "timezone": "UTC"},
        )
        self.assertEqual(res_retest.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Exam Retest Request", self._admin_emails()[0].subject)

        # Church admin application
        mail.outbox = []
        res_ca_app = self.client.post(
            reverse("apply_church_admin"),
            {
                "name_of_church": "Faith Fellowship",
                "name_of_pastor": "John Student",
                "church_address": "100 Church Rd",
                "package": self.package.id,
            },
        )
        self.assertEqual(res_ca_app.status_code, 302)
        self.assertEqual(ChurchAdminApplication.objects.count(), 1)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Church Admin Application", self._admin_emails()[0].subject)

        # Profile update via AJAX
        mail.outbox = []
        res_prof = self.client.post(
            reverse("student_profile_view"),
            data=json.dumps({"city": "Dallas"}),
            content_type="application/json",
        )
        self.assertEqual(res_prof.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Student Profile Updated", self._admin_emails()[0].subject)

        # Forgot password (should notify admin WITHOUT exposing password)
        mail.outbox = []
        res_fp = self.client.post(
            reverse("forgot_password"), {"email": self.student.email}
        )
        self.assertEqual(res_fp.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Password Reset Request", self._admin_emails()[0].subject)
        self.assertNotIn("Temporary Password:", self._admin_emails()[0].body)

    def test_support_and_doubt_chats_send_admin_email(self):
        # Student creates support query + replies
        self.client.force_login(self.student_user)
        res_sup = self.client.post(
            reverse("student_support_create"),
            {"doubt": "Need help with syllabus", "category": "subject"},
        )
        self.assertEqual(res_sup.status_code, 201)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("New Support / Doubt Query", self._admin_emails()[0].subject)

        ticket = Support.objects.filter(student=self.student).first()
        mail.outbox = []
        res_rep = self.client.post(
            reverse("student_doubt_view", args=[ticket.id]),
            {"doubt_answer": "Here is a follow-up question."},
        )
        self.assertEqual(res_rep.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Support / Doubt Chat Reply", self._admin_emails()[0].subject)

        # Church user creates support query + replies (also verifies fixed model kwargs)
        mail.outbox = []
        self.client.force_login(self.church_user)
        res_cu_sup = self.client.post(
            reverse("church_user_support_create"),
            {"doubt": "Question about class video", "category": "general"},
        )
        self.assertEqual(res_cu_sup.status_code, 200)
        self.assertTrue(res_cu_sup.json()["success"])
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("New Church User Support / Doubt Query", self._admin_emails()[0].subject)

        cu_ticket = Support.objects.filter(student=self.church_student).first()
        mail.outbox = []
        res_cu_rep = self.client.post(
            reverse("church_user_doubt_view", args=[cu_ticket.id]),
            {"doubt_answer": "Follow up from church user."},
        )
        self.assertEqual(res_cu_rep.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Church User Support / Doubt Chat Reply", self._admin_emails()[0].subject)

    def test_all_fee_payment_paths_send_admin_email_to_admin_address(self):
        payment = Payments.objects.create(
            code="PAY001",
            name="John Student",
            email="john.student@example.com",
            phone="1234567890",
            person_group="student",
            amount=Decimal("100.00"),
            message="Tuition fee",
            is_paid=False,
            student=self.student,
        )

        # Direct helper
        send_admin_payment_notification(payment)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertNotIn("info@mytts.org", str([m.to for m in mail.outbox]))

        # process_direct_payment
        mail.outbox = []
        self.client.force_login(self.student_user)
        session = self.client.session
        session["payment_temp"] = {"id": payment.id}
        session.save()
        res_dp = self.client.post(reverse("process_direct_payment"))
        self.assertEqual(res_dp.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Fee Payment Paid", self._admin_emails()[0].subject)

        # capture_registration_payment (student)
        mail.outbox = []
        reg_pay = Payments.objects.create(
            code="REG001",
            name="John Student",
            email="john.student@example.com",
            person_group="student",
            amount=Decimal("150.00"),
            is_paid=False,
            student=self.student,
        )
        session = self.client.session
        session["registration_payment_id"] = reg_pay.id
        session.save()
        token_resp = Mock()
        token_resp.json.return_value = {"access_token": "tok"}
        cap_resp = Mock()
        cap_resp.json.return_value = {"status": "COMPLETED"}
        with patch("home.views.requests.post", side_effect=[token_resp, cap_resp]):
            res_cap = self.client.post(
                reverse("capture_registration_payment"),
                data=json.dumps({"orderID": "ORD123"}),
                content_type="application/json",
            )
        self.assertEqual(res_cap.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Paid (Student Registration)", self._admin_emails()[0].subject)

        # capture_registration_payment (church_admin)
        mail.outbox = []
        ca_pay = Payments.objects.create(
            code="CA001",
            name="Pastor Admin",
            email="pastor@church.org",
            person_group="church_admin",
            amount=Decimal("50.00"),
            is_paid=False,
            church_admin=self.church_admin,
        )
        session = self.client.session
        session["registration_payment_id"] = ca_pay.id
        session.save()
        with patch("home.views.requests.post", side_effect=[token_resp, cap_resp]):
            res_ca_cap = self.client.post(
                reverse("capture_registration_payment"),
                data=json.dumps({"orderID": "ORD456"}),
                content_type="application/json",
            )
        self.assertEqual(res_ca_cap.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Paid (Church Admin Registration)", self._admin_emails()[0].subject)

        # capture_retest_payment
        mail.outbox = []
        se_retest = StudentsExams.objects.create(
            student=self.student,
            exam=self.exam,
            is_retest=True,
            retest_fee=Decimal("25.00"),
            retest_status="pending",
            timezone="UTC",
            show_on_score=0,
            created_by=self.student_user,
            updated_by=self.student_user,
        )
        with patch("student.views.requests.post", side_effect=[token_resp, cap_resp]):
            res_ret = self.client.post(
                reverse("capture_retest_payment"),
                data=json.dumps({"orderID": "ORD789", "student_exam_id": se_retest.id}),
                content_type="application/json",
            )
        self.assertEqual(res_ret.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Fee Payment Paid", self._admin_emails()[0].subject)

        # capture_paypal_order
        mail.outbox = []
        pay_pp = Payments.objects.create(
            code="PAYPP01",
            name="John Student",
            email="john.student@example.com",
            person_group="student",
            amount=Decimal("75.00"),
            is_paid=False,
            student=self.student,
        )
        session = self.client.session
        session["payment_temp"] = {"id": pay_pp.id}
        session.save()
        with patch("student.views.requests.post", side_effect=[token_resp, cap_resp]):
            res_pp = self.client.post(
                reverse("capture_paypal_order"),
                data=json.dumps({"orderID": "ORDPP01"}),
                content_type="application/json",
            )
        self.assertEqual(res_pp.status_code, 200)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Fee Payment Paid", self._admin_emails()[0].subject)

        # make_payment (legacy endpoint still notifies admin before template render)
        mail.outbox = []
        try:
            self.client.post(
                reverse("make_payment"),
                {
                    "name": "John Student",
                    "email": "john.student@example.com",
                    "phone": "1234567890",
                    "amount": "40.00",
                    "message": "Library fee",
                },
            )
        except TemplateDoesNotExist:
            pass
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Submitted (Pending Verification)", self._admin_emails()[0].subject)

    def test_approval_emails_use_admin_email_and_default_sender(self):
        self.client.force_login(self.admin_user)
        res = self.client.post(reverse("student_approve_action", args=[self.church_student.id]))
        self.assertEqual(res.status_code, 302)
        admin_msgs = self._admin_emails()
        self.assertEqual(len(admin_msgs), 1)
        self.assertIn("Church User Approved", admin_msgs[0].subject)
        for m in mail.outbox:
            self.assertNotEqual(m.from_email, "contact@byteboot.in")
            self.assertNotIn("contact@byteboot.in", m.to)

        # Church admin approving church user
        mail.outbox = []
        self.client.force_login(self.ca_user)
        res_ca = self.client.post(reverse("church_student_approve", args=[self.church_student.id]))
        self.assertEqual(res_ca.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Church User Approved", self._admin_emails()[0].subject)
        for m in mail.outbox:
            self.assertNotEqual(m.from_email, "contact@byteboot.in")
            self.assertNotIn("contact@byteboot.in", m.to)

        # Church user starting an exam + student exam auto-expiry
        mail.outbox = []
        self.church_user.refresh_from_db()
        self.client.force_login(self.church_user)
        res_start = self.client.get(reverse("church_user_start_exam", args=[self.exam.id]))
        self.assertEqual(res_start.status_code, 302)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Church User Exam Started", self._admin_emails()[0].subject)

        mail.outbox = []
        self.client.force_login(self.student_user)
        expired_se = StudentsExams.objects.create(
            student=self.student,
            exam=self.exam,
            start_time=timezone.now() - timedelta(minutes=200),
            exam_duration=150,
            is_approved=True,
            is_exam_started=True,
            is_exam_ended=False,
            timezone="UTC",
            show_on_score=0,
            created_by=self.student_user,
            updated_by=self.student_user,
        )
        res_exp = self.client.get(reverse("take_exam", args=[expired_se.id]))
        self.assertEqual(res_exp.status_code, 302)
        expired_se.refresh_from_db()
        self.assertTrue(expired_se.is_exam_ended)
        self.assertEqual(len(self._admin_emails()), 1)
        self.assertIn("Exam Submitted", self._admin_emails()[0].subject)
