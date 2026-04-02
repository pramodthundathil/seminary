from django.urls import path
from . import views

urlpatterns = [
    # Student Dashboard
    path("index", views.student_index, name="student_index"), # Moved from home/urls.py: path("student_index",...
    path("", views.student_home, name="student_home"),
    path("references/", views.student_references, name="student_references"),
    path("subjects/", views.student_subjects, name="student_subjects"),
    path("pending-assignment/", views.student_pending_assignment, name="student_pending_assignment"),
    path("submitted-assignment/", views.student_submitted_assignment, name="student_submitted_assignment"),
    path("exam-hall/", views.student_exam_hall, name="student_exam_hall"),
    path("score-card/", views.student_score_card, name="student_score_card"),
    path("class-recordings/", views.student_class_recordings, name="student_class_recordings"),
    path("profile/", views.student_profile_view, name="student_profile_view"),
    path('support/create/', views.student_support_create, name='student_support_create'),
    path("request-subject/", views.request_subject_view, name="request_subject"),
    path("exam-hall/request-exam/", views.student_request_exam, name="student_request_exam"),
    path("view-posts/", views.student_view_post, name="student_view_post"),
    path("change-password/", views.student_change_password, name="student_change_password"),
    path("view/<int:id>/", views.student_doubt_view, name="student_doubt_view"),
    
    # Payment
    path("make-payment/", views.make_payment, name="make_payment"),
    path("payment/save-temp/", views.save_payment_temp, name="save_payment_temp"),
    path("create-paypal-order/", views.create_paypal_order, name="create_paypal_order"),
    path("capture-paypal-order/", views.capture_paypal_order, name="capture_paypal_order"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-failed/", views.payment_failed, name="payment_failed"),
    path("doubts-answers/", views.student_doubts_answers, name="student_doubts_answers"),
    path('request-exam/submit/', views.submit_request_exam, name='submit-request-exam'),
    path("take-exam/<int:exam_id>/", views.take_exam, name="take_exam"),
    path("submit-exam/<int:exam_id>/", views.submit_exam, name="submit_exam"),
    path("reschedule-exam/", views.student_reschedule_exam, name="student_reschedule_exam"),
    path("payment-input/", views.student_payment_input, name="student_payment_input"),

    path("confirm-payment/", views.student_confirm_payment, name="student_confirm_payment"),
    path("register/", views.signup_student, name="signup_student"),
    path('application/success/<str:student_id>/', views.student_application_success, name='student_application_success'),

    # API
    path("get-exams/<int:subject_id>/", views.get_exams, name="get_exams"),
    
    path('submit_assignment/<int:pk>', views.submit_assignment, name="submit_assignment" ),
    path("check-email/", views.check_email_availability, name="check_email_availability"),
]
