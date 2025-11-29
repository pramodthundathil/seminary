from django.urls import path 
from  .import views

urlpatterns = [
    path("home/", views.student_home, name="student_home"),
    path("subjects/", views.student_subjects, name="student_subjects"),
    path("view-posts/", views.student_view_post, name="student_view_post"),
    path("exam-hall/", views.student_exam_hall, name="student_exam_hall"),
    path("score-card/", views.student_score_card, name="student_score_card"),
    path("class-recordings/", views.student_class_recordings, name="student_class_recordings"),
    path("submitted-assignment/", views.student_submitted_assignment, name="student_submitted_assignment"),
    path("pending-assignment/", views.student_pending_assignment, name="student_pending_assignment"),
    path("doubts-answers/", views.student_doubts_answers, name="student_doubts_answers"),
    path("request-exam/", views.student_request_exam, name="student_request_exam"),
    path("student-profile/", views.student_profile_view, name="student_profile_view"),

    path('',views.index, name='index'),
    path("about_us",views.about_us,name="about_us"),
    path("admin_index",views.admin_index,name="admin_index"),
    path("student_index",views.student_index,name="student_index"),
    path("signin/",views.signin,name="signin"),
    path("signout",views.signout,name="signout"),
    path("register/",views.register,name="register"),
    path("contact/",views.contact,name="contact"),
    # path("signup_student/",views.signup_student,name="signup_student"),
    path('student/register/', views.signup_student, name='signup_student'),
    path('student/application/success/', views.student_application_success, name='student_application_success'),

    # Admissions dropdown pages
    path('admissions/accreditation/', views.accreditation, name='accreditation'),
    path('admissions/admission-process/', views.admission_process, name='admission_process'),    
    path('admissions/fees-structure/', views.fees_structure, name='fees_structure'),
    path('admissions/scholarship/', views.scholarship, name='scholarship'),
    path('admissions/new-admission-form/', views.new_admission_form, name='new_admission_form'),
    path('admissions/reference-form/', views.reference_form, name='reference_form'),
    path('admissions/payment-options/', views.payment_options, name='payment_options'),

    # Admissions dropdown pages
    path('admissions/doctoral-program/', views.doctoral_program, name='doctoral_program'),
    path('admissions/masters-program/', views.masters_program, name='masters_program'),       
    path('admissions/bachelors-program/', views.bachelors_program, name='bachelors_program'),
    path('admissions/diploma-program/', views.diploma_program, name='diploma_program'),
    path('admissions/certificate-program/', views.certificate_program, name='certificate_program'),
    
]