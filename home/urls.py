from django.urls import path 
from  .import views

urlpatterns = [
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

    
]