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

    
]