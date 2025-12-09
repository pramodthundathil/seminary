from django.urls import path 
from  .import views

urlpatterns = [
    path('',views.index, name='index'),

    #----student dashboard---#
    path("student_index",views.student_index,name="student_index"),
    path("student/", views.student_home, name="student_home"),
    path("student/subjects/", views.student_subjects, name="student_subjects"),
    path("student/pending-assignment/", views.student_pending_assignment, name="student_pending_assignment"),
    path("student/submitted-assignment/", views.student_submitted_assignment, name="student_submitted_assignment"),
    path("student/exam-hall/", views.student_exam_hall, name="student_exam_hall"),
    path("student/score-card/", views.student_score_card, name="student_score_card"),
    path("student/class-recordings/", views.student_class_recordings, name="student_class_recordings"),
    path("student/student-profile/", views.student_profile_view, name="student_profile_view"),
    path('student/support/create/', views.student_support_create, name='student_support_create'),
    path("student/request-subject/", views.request_subject_view, name="request_subject"),
    path("student/exam-hall/request-exam/", views.student_request_exam, name="student_request_exam"),
    path("student/view-posts/", views.student_view_post, name="student_view_post"),
    path("student/view-posts/", views.student_view_post, name="student_view_post"),
    path("student/change-password/", views.student_change_password, name="student_change_password"),
    path("student/view/<int:id>/", views.student_doubt_view, name="student_doubt_view"),
    path("student/make-payment/", views.make_payment, name="make_payment"),
    path("student/payment/save-temp/", views.save_payment_temp, name="save_payment_temp"),
    path("student/create-paypal-order/", views.create_paypal_order, name="create_paypal_order"),
    path("student/capture-paypal-order/", views.capture_paypal_order, name="capture_paypal_order"),
    path("student/payment-success/", views.payment_success, name="payment_success"),
    path("student/payment-failed/", views.payment_failed, name="payment_failed"),
    path("student/doubts-answers/", views.student_doubts_answers, name="student_doubts_answers"),
    path('student/request-exam/submit/', views.submit_request_exam, name='submit-request-exam'),
    path("student/payment-input/", views.student_payment_input, name="student_payment_input"),
    path("student/confirm-payment/", views.student_confirm_payment, name="student_confirm_payment"),





    path("get-exams/<int:subject_id>/", views.get_exams, name="get_exams"),


# Dynamic page URL (keep this last)
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
   


    path("signin/",views.signin,name="signin"),
    path("signout",views.signout,name="signout"),
    path("register/",views.register,name="register"),
    path("contact-us/",views.contact,name="contact-us"),
    # path("signup_student/",views.signup_student,name="signup_student"),
    path('student/register/', views.signup_student, name='signup_student'),    
    path('student/application/success/<str:student_id>/', views.student_application_success, name='student_application_success'),

    # Admissions dropdown pages   
    path('reference-form/', views.reference_form, name='reference_form'),
    path('make-payment/', views.payment_options, name='payment_options'),





    path("check/",views.test_menu_debug,name="test_menu_debug"),
    path("course-list/",views.courses,name="course-list"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    
   # Guest Registration
    path('guest/register/', views.signup_guest, name='guest_register'),
    path('guest/success/<str:guest_id>/', views.guest_registration_success, name='guest_registration_success'),
    
    # Church Admin Registration
    path('church-admin/register/', views.signup_church_admin, name='church_admin_register'),
    path('church-admin/success/<str:admin_id>/', views.church_admin_registration_success, name='church_admin_registration_success'),
    
]