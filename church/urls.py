from django.urls import path
from . import views

urlpatterns = [
    # Church User Dashboard
    path('user-dashboard/', views.church_user_home, name='church_user_home'),
    path('user-dashboard/change-password/', views.church_user_change_password, name='church_user_change_password'),
    path('user-dashboard/subjects/', views.church_user_subjects, name='church_user_subjects'),
    path('user-dashboard/assignments/', views.church_user_assignments, name='church_user_assignments'),
    path('user-dashboard/recordings/', views.church_user_recordings, name='church_user_recordings'),
    
    # User Expanded Modules
    path('user-dashboard/submitted-assignment/', views.church_user_submitted_assignment, name='church_user_submitted_assignment'),
    path('user-dashboard/assignment/<int:assignment_id>/', views.church_user_view_assignment, name='church_user_view_assignment'),
    path('user-dashboard/submit-assignment/<int:pk>/', views.church_submit_assignment, name='church_submit_assignment'),
    path('user-dashboard/exam-hall/', views.church_user_exam_hall, name='church_user_exam_hall'),
    path('user-dashboard/take-exam/<int:exam_id>/', views.church_user_take_exam, name='church_user_take_exam'),
    path('user-dashboard/submit-exam/<int:exam_id>/', views.church_user_submit_exam, name='church_user_submit_exam'),
    path('user-dashboard/score-card/', views.church_user_score_card, name='church_user_score_card'),
    path('user-dashboard/start-exam/<int:exam_id>/', views.church_user_start_exam, name='church_user_start_exam'),
    path('user-dashboard/profile/', views.church_user_profile_view, name='church_user_profile_view'),
    path('user-dashboard/doubts-answers/', views.church_user_doubts_answers, name='church_user_doubts_answers'),
    path('user-dashboard/support/create/', views.church_user_support_create, name='church_user_support_create'),
    path('user-dashboard/doubts-answers/view/<int:id>/', views.church_user_doubt_view, name='church_user_doubt_view'),

    path('user-dashboard/subject/<int:subject_id>/', views.church_user_subject_uploads, name='church_user_subject_uploads'),
    path('admin-dashboard/', views.church_admin_dashboard, name='church_admin_dashboard'),
    path('settings/', views.church_admin_settings, name='church_admin_settings'),
    
    # Students Management for Church Admin
    path('students/', views.church_students_list, name='church_students_list'),
    path('students/<int:id>/view/', views.church_student_view, name='church_student_view'),
    path('students/<int:id>/approve/', views.church_student_approve, name='church_student_approve'),
    path('students/<int:id>/delete/', views.church_student_delete, name='church_student_delete'),

    # Subjects Management for Church Admin
    path('subjects/', views.church_subjects_list, name='church_subjects_list'),
    path('subjects/<int:id>/view/', views.church_subject_view, name='church_subject_view'),
]
