from django.urls import path 
from  .import views

urlpatterns = [
    path('',views.index, name='index'),
   
    path("home/", views.student_home, name="student_home"),
    path("subjects/", views.student_subjects, name="student_subjects"),
    path("view-posts/", views.student_view_post, name="student_view_post"),
    path("exam-hall/", views.student_exam_hall, name="student_exam_hall"),
    path("score-card/", views.student_score_card, name="student_score_card"),
    path("class-recordings/", views.student_class_recordings, name="student_class_recordings"),
    path("submitted-assignment/", views.student_submitted_assignment, name="student_submitted_assignment"),
# Dynamic page URL (keep this last)
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
   

    path("student_index",views.student_index,name="student_index"),
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

    
]