from django.urls import path, include
from . import views



urlpatterns = [

    #admin index
    path("admin/dashboard",views.admin_index,name="admin_index"),

    # Menu Management
    path('admin/menus/', views.menu_list, name='menu_list'),
    path('admin/menus/datatable/', views.menu_datatable, name='menu_datatable'),
    path('menus/engineer/', views.menu_engineer, name='menu_engineer_new'),
    path('menus/engineer/<int:menu_id>/', views.menu_engineer, name='menu_engineer'),
    path('menus/save/', views.save_menu, name='save_menu'), # Updated for general details
    path('menus/items/create/', views.menu_item_create, name='menu_item_create'),
    path('menus/items/update/<int:pk>/', views.menu_item_update, name='menu_item_update'),
    path('menus/items/delete/<int:pk>/', views.menu_item_delete, name='menu_item_delete'),
    path('menus/items/reorder/', views.update_menu_order, name='update_menu_order'),
    path('menus/refresh-urls/<int:pk>/', views.refresh_menu_urls, name='refresh_menu_urls'),
    path('menus/delete/<int:menu_id>/', views.delete_menu, name='delete_menu'),
    
    # Pages Management
    path('admin/pages/', views.pages_list, name='pages_list'),
    path('pages/create/', views.page_create, name='page_create'),
    path('pages/<int:pk>/edit/', views.page_edit, name='page_edit'),
    path('pages/<int:pk>/view/', views.page_view, name='page_view'),
    path('pages/<int:pk>/delete/', views.page_delete, name='page_delete'),
    


    # News Management
    path('admin/news', views.news_list, name='news_list'),
    path('datatable/', views.news_datatable, name='news_datatable'),
    path('create/', views.news_create, name='news_create'),
    path('edit/<int:news_id>/', views.news_edit, name='news_edit'),
    path('get/<int:news_id>/', views.news_get, name='news_get'),
    path('delete/<int:news_id>/', views.news_delete, name='news_delete'),
    path('toggle-status/<int:news_id>/', views.news_toggle_status, name='news_toggle_status'),

    # Media Library Management
    path('admin/media/', views.media_list, name='media_list'),
    path('admin/media/upload/', views.media_upload, name='media_upload'),
    path('admin/media/<int:media_id>/get/', views.media_get, name='media_get'),
    path('admin/media/<int:media_id>/update/', views.media_update, name='media_update'),
    path('admin/media/<int:media_id>/delete/', views.media_delete, name='media_delete'),
    
    # Media Library JSON API
    path('admin/media/json/', views.media_library_json, name='media_library_json'),
    path('admin/media/upload/json/', views.media_library_upload_json, name='media_library_upload_json'),
    
    # Video Library JSON API
    path('admin/videos/json/', views.video_library_json, name='video_library_json'),
    path('admin/videos/create/json/', views.video_library_create_json, name='video_library_create_json'),
    
    # YouTube Library JSON API
    path('admin/youtube/json/', views.youtube_library_json, name='youtube_library_json'),
    path('admin/youtube/create/json/', views.youtube_library_create_json, name='youtube_library_create_json'),


    #photo gallery
    
    path('admin/photos', views.photo_gallery, name='photo_gallery'),
    path('photos/datatable/', views.photo_datatable, name='photo_datatable'),
    path('photos/create/', views.photo_create, name='photo_create'),
    path('photos/get/<int:photo_id>/', views.photo_get, name='photo_get'),
    path('photos/update/<int:photo_id>/', views.photo_update, name='photo_update'),
    path('photos/delete/<int:photo_id>/', views.photo_delete, name='photo_delete'),
    path('photos/media-list/', views.media_library_list, name='media_library_list'),



    # Slider Management URLs
    path('admin/sliders/', views.slider_list, name='slider_list'),
    path('sliders/datatable/', views.slider_datatable, name='slider_datatable'),
    path('sliders/create/', views.slider_create, name='slider_create'),
    path('sliders/get/<int:slider_id>/', views.slider_get, name='slider_get'),
    path('sliders/update/<int:slider_id>/', views.slider_update, name='slider_update'),
    path('sliders/delete/<int:slider_id>/', views.slider_delete, name='slider_delete'),
    
    # Slider Photos URLs
    path('sliders/<int:slider_id>/photos/', views.slider_photos_list, name='slider_photos_list'),
    path('sliders/<int:slider_id>/photos/datatable/', views.slider_photos_datatable, name='slider_photos_datatable'),
    path('sliders/<int:slider_id>/photos/create/', views.slider_photo_create, name='slider_photo_create'),
    path('sliders/photos/get/<int:photo_id>/', views.slider_photo_get, name='slider_photo_get'),
    path('sliders/photos/update/<int:photo_id>/', views.slider_photo_update, name='slider_photo_update'),
    path('sliders/photos/delete/<int:photo_id>/', views.slider_photo_delete, name='slider_photo_delete'),

    path("admin/categories", views.category_list, name= "category_list"),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/edit/<int:category_id>/', views.category_edit, name='category_edit'),
    path('categories/view/<int:category_id>/', views.category_view, name='category_view'),
    path('categories/delete/<int:category_id>/', views.category_delete, name='category_delete'),


    # Course management
    path('admin/courses/', views.course_list, name='course_list'),
    path('courses/datatable/', views.course_datatable, name='course_datatable'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/get/<int:course_id>/', views.course_get, name='course_get'),
    path('courses/update/<int:course_id>/', views.course_update, name='course_update'),
    path('courses/delete/<int:course_id>/', views.course_delete, name='course_delete'),


     # Student Management
    path('admin/students/', views.student_list_view, name='student_list'),
    path('students/datatable/', views.student_datatable, name='student_datatable'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/get/<int:student_id>/', views.student_get, name='student_get'),
    
    # Student Detail & Actions
    path('students/view/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/action/approve/<int:student_id>/', views.student_approve_action, name='student_approve_action'),
    path('students/action/disapprove/<int:student_id>/', views.student_disapprove_action, name='student_disapprove_action'),
    path('students/action/activate/<int:student_id>/', views.student_activate_action, name='student_activate_action'),
    path('students/action/deactivate/<int:student_id>/', views.student_deactivate_action, name='student_deactivate_action'),
    path('students/update/<int:student_id>/', views.student_update, name='student_update'),
    path('admin/students/delete/<int:student_id>/', views.student_delete, name='student_delete'),
    

    # Applications
    path('admin/applications/', views.application_list_view, name='application_list_view'),
    
    path('students/toggle-active/<int:student_id>/', views.student_toggle_active, name='student_toggle_active'),
    path('students/toggle-approval/<int:student_id>/', views.student_toggle_approval, name='student_toggle_approval'),

    # Student Books Refined Workflow
    path('admin/students/student-books/', views.student_books_list, name='student_books_list'),
    path('students/books/datatable/', views.student_books_datatable, name='student_books_datatable'),
    path('students/books/bulk-assign/', views.student_books_bulk_assign, name='student_books_bulk_assign'),
    path('students/books/get-students/<int:course_id>/', views.ajax_get_students_by_course, name='ajax_get_students_by_course'),
    path('students/books/get-subjects/<int:student_id>/', views.ajax_get_subjects_by_student, name='ajax_get_subjects_by_student'),
    path('students/books/get-books/<int:subject_id>/', views.ajax_get_books_by_subject, name='ajax_get_books_by_subject'),
    path('students/books/delete/<int:id>/', views.student_books_delete, name='student_books_delete'),

    # Student Subjects Workflow
    path('admin/students/student-subjects/', views.student_subjects_list, name='student_subjects_list'),
    path('admin/students/books/toggle-approval/<int:id>/', views.student_books_toggle_approval, name='student_books_toggle_approval'),
    path('students/subjects/datatable/', views.student_subjects_datatable, name='student_subjects_datatable'),
    path('students/subjects/get-available/<int:student_id>/', views.ajax_get_available_subjects, name='ajax_get_available_subjects'),
    path('students/subjects/bulk-assign/', views.student_subjects_bulk_assign, name='student_subjects_bulk_assign'),
    path('students/subjects/toggle-approval/<int:id>/', views.student_subjects_toggle_approval, name='student_subjects_toggle_approval'),
    path('students/subjects/delete/<int:id>/', views.student_subjects_delete, name='student_subjects_delete'),
    
    # Student Instructors Workflow
    path('admin/students/student-instructor/', views.student_instructors_list, name='student_instructors_list'),
    path('students/instructors/datatable/', views.student_instructors_datatable, name='student_instructors_datatable'),
    path('students/instructors/get-subjects/<int:student_id>/', views.ajax_get_assigned_subjects_by_student, name='ajax_get_assigned_subjects_by_student'),
    path('students/instructors/get-available/<int:student_id>/<int:subject_id>/', views.ajax_get_available_instructors, name='ajax_get_available_instructors'),
    path('students/instructors/bulk-assign/', views.student_instructors_bulk_assign, name='student_instructors_bulk_assign'),
    path('students/instructors/delete/<int:id>/', views.student_instructors_delete, name='student_instructors_delete'),
    
    # Student Uploads Workflow
    path('admin/students/student-uploads/', views.student_uploads_list, name='student_uploads_list'),
    path('students/uploads/datatable/', views.student_uploads_datatable, name='student_uploads_datatable'),
    path('students/uploads/get-available/<int:student_id>/<int:subject_id>/', views.ajax_get_available_uploads, name='ajax_get_available_uploads'),
    path('students/uploads/bulk-assign/', views.student_uploads_bulk_assign, name='student_uploads_bulk_assign'),
    path('students/uploads/delete/<int:id>/', views.student_uploads_delete, name='student_uploads_delete'),
    
    # Student Exams Workflow
    path('admin/students/student-exams', views.student_exams_list, name='student_exams_list'),
    path('students/exams/datatable/', views.student_exams_datatable, name='student_exams_datatable'),
    path('students/exams/get-available/<int:student_id>/<int:subject_id>/', views.ajax_get_available_exams, name='ajax_get_available_exams'),
    path('students/exams/bulk-assign/', views.student_exams_bulk_assign, name='student_exams_bulk_assign'),
    path('students/exams/delete/<int:id>/', views.student_exams_delete, name='student_exams_delete'),
    path('students/exams/toggle-approval/<int:id>/', views.student_exams_toggle_approval, name='student_exams_toggle_approval'),
    path('students/exams/get/<int:id>/', views.student_exams_get, name='student_exams_get'),
    path('students/exams/update/<int:id>/', views.student_exams_update, name='student_exams_update'),
    # Answer Sheet Viewing and Grading
    path('admin/students/exam-answer-sheet/<int:exam_id>/', views.view_answer_sheet, name='view_answer_sheet'),
    path('admin/students/update-answer-marks/', views.update_answer_marks, name='update_answer_marks'),
    # Student Submitted Exams (Admin-facing)
    path('admin/students/student-submitted-exams/', views.student_submitted_exams_list, name='student_submitted_exams_list'),
    path('admin/students/student-submitted-exams/datatable/', views.student_submitted_exams_datatable, name='student_submitted_exams_datatable'),

    # Student Assignments (Admin-Facing)
    path('admin/students/student-submitted-assignment/', views.student_assignment_list, {'submitted_only': True}, name='student_submitted_assignment_list'), # Alias
    path('admin/students/student-assignment/', views.student_assignment_list, name='student_assignment_list'),
    path('students/assignments/datatable/', views.student_assignment_datatable, name='student_assignment_datatable'),
    path('admin/students/assignment-answer-sheet/<int:id>/', views.view_assignment_answer_sheet, name='view_assignment_answer_sheet'),
    path('admin/students/student-assignment/edit/<int:id>/', views.student_assignment_edit, name='student_assignment_edit'),
    path('admin/students/student-assignment/delete/<int:id>/', views.student_assignment_delete, name='student_assignment_delete'),
    path('admin/students/update-assignment-marks/', views.update_assignment_marks, name='update_assignment_marks'),
    
    # Assign Assignment AJAX
    path('admin/students/assign-assignment/', views.student_assignments_assign, name='student_assignments_assign'),
    path('ajax/get-students-by-course/', views.ajax_get_students_by_course, name='ajax_get_students_by_course'),
    path('ajax/get-subjects-by-student/', views.ajax_get_subjects_by_student, name='ajax_get_subjects_by_student'),
    path('ajax/get-assignments-by-subject/', views.ajax_get_assignments_by_subject, name='ajax_get_assignments_by_subject'),

    #videos

    path("admin/videos", views.video_list, name = "video_list"),
    path('videos/create/', views.video_create, name='video_create'),
    path('videos/<int:video_id>/edit/', views.video_edit, name='video_edit'),
    path('videos/<int:video_id>/view/', views.video_view, name='video_view'),
    path('videos/<int:video_id>/delete/', views.video_delete, name='video_delete'),


    #roles and permissions
    path("admin/roles",views.roles,name="roles"),
    path("roles/create/", views.roles_create, name="roles_create"),
    path("roles/<int:id>/view/", views.roles_view, name="roles_view"),
    path("roles/<int:id>/edit/", views.roles_edit, name="roles_edit"),
    path("roles/<int:id>/delete/", views.roles_delete, name="roles_delete"),


    # languages

    path("admin/languages",views.languages, name="languages_list"),
    path("admin/language/create",views.language_create, name="language_create"),
    path("admin/language/<int:language_id>/view", views.language_view, name="language_view"),
    path("admin/language/<int:language_id>/edit", views.language_edit, name="language_edit"),
    path("admin/language/<int:language_id>/delete", views.language_delete, name="language_delete"),

    #subjects

    path("admin/subjects",views.subjects, name="subjects_list"),
    path("admin/subjects/create",views.subjects_create, name="subjects_create"),
    path("admin/subjects/<int:subjects_id>/view", views.subjects_view, name="subjects_view"),
    path("admin/subjects/<int:subjects_id>/edit", views.subjects_edit, name="subjects_edit"),
    path("admin/subjects/<int:subjects_id>/delete", views.subjects_delete, name="subjects_delete"),


    #branches

    path("admin/branches", views.branches_list, name="branches_list"),
    path("admin/branches/create", views.branches_create, name="branches_create"),
    path("admin/branches/<int:branch_id>/view", views.branches_view, name="branches_view"),
    path("admin/branches/<int:branch_id>/edit", views.branches_edit, name="branches_edit"),
    path("admin/branches/<int:branch_id>/delete", views.branches_delete, name="branches_delete"),

    #contact request
    path("admin/contact",views.contact_list, name='contact_list'),
    path('contacts/delete/<int:id>/', views.contact_delete, name='contact_delete'),
    path('contacts/permanent-delete/<int:id>/', views.contact_permanent_delete, name='contact_permanent_delete'),


    #exams 

    path("admin/exams", views.exams_list, name="exams_list"),
    path('exams/create/', views.exam_create, name='exams_create'),
    path('exams/<int:exam_id>/view/', views.exam_view, name='exams_view'),
    path('exams/<int:exam_id>/edit/', views.exam_edit, name='exams_edit'),
    path('exams/<int:exam_id>/delete/', views.exam_delete, name='exams_delete'),
    
    # Exam Questions
    path('exams/<int:exam_id>/question/descriptive/create/', views.question_descriptive_create, name='question_descriptive_create'),
    path('exams/question/descriptive/<int:question_id>/edit/', views.question_descriptive_edit, name='question_descriptive_edit'),
    path('exams/question/descriptive/<int:question_id>/delete/', views.question_descriptive_delete, name='question_descriptive_delete'),
    
    path('exams/<int:exam_id>/question/objective/create/', views.question_objective_create, name='question_objective_create'),
    path('exams/question/objective/<int:question_id>/edit/', views.question_objective_edit, name='question_objective_edit'),
    path('exams/question/objective/<int:question_id>/delete/', views.question_objective_delete, name='question_objective_delete'),

    #staffs

    path("admin/staffs", views.staffs_list, name="staffs_list"),
    path('staffs/create/', views.staff_create, name='staffs_create'),
    path('staffs/<int:staff_id>/view/', views.staff_view, name='staffs_view'),
    path('staffs/<int:staff_id>/edit/', views.staff_edit, name='staffs_edit'),
    path('staffs/<int:staff_id>/delete/', views.staff_delete, name='staffs_delete'),


    #assignments 

    path("admin/assignments", views.assignments_list, name="assignments_list"),
    path('assignments/create/', views.assignment_create, name='assignments_create'),
    path('assignments/<int:assignment_id>/view/', views.assignment_view, name='assignments_view'),
    path('assignments/<int:assignment_id>/edit/', views.assignment_edit, name='assignments_edit'),
    path('assignments/<int:assignment_id>/delete/', views.assignment_delete, name='assignments_delete'),


    # Reference files

    path("admin/references", views.reference_list, name="reference_list"),
    path('references/create/', views.reference_create, name='reference_create'),
    path('references/<int:reference_id>/view/', views.reference_view, name='reference_view'),
    path('references/<int:reference_id>/edit/', views.reference_edit, name='reference_edit'),
    path('references/<int:reference_id>/delete/', views.reference_delete, name='reference_delete'),
    

    #support 

    path("admin/support", views.support_list, name = "support_list"),
    path('support/<int:support_id>/view/', views.support_view, name='support_view'),
    path('support/<int:support_id>/delete/', views.support_delete, name='support_delete'),
    path('support/replay/<int:pk>/delete/', views.support_reply_delete, name='support_reply_delete'),

    
    #uploads 
    path("admin/uploads/", views.uploads_list, name="uploads_list"),
    path("uploads/create/", views.uploads_create, name="uploads_create"),
    path("uploads/<int:id>/", views.uploads_view, name="uploads_view"),
    path("uploads/<int:id>/edit/", views.uploads_edit, name="uploads_edit"),
    path("uploads/<int:id>/delete/", views.uploads_delete, name="uploads_delete"),


    #payments 

    path("admin/payments/", views.payments_list, name="payments_list"),
    path("payments/<int:id>/view/", views.payments_view, name="payments_view"),
    path("payments/<int:id>/delete/", views.payments_delete, name="payments_delete"),


    #users 

    path("admin/users/", views.users_list, name="users_list"),
    path("users/<int:id>/view/", views.users_view, name="users_view"),
    path("users/<int:id>/delete/", views.users_delete, name="users_delete"),

    # Church Login Codes
    path('admin/codes/', views.church_code_list, name='church_code_list'),
    path('admin/codes/create/', views.church_code_create, name='church_code_create'),
    path('admin/codes/<int:code_id>/edit/', views.church_code_edit, name='church_code_edit'),
    path('admin/codes/<int:code_id>/delete/', views.church_code_delete, name='church_code_delete'),

    # Church Admins
    path('admin/church-admins/', views.church_admin_list, name='church_admin_list'),
    path('admin/church-admins/create/', views.church_admin_create, name='church_admin_create'),
    path('admin/church-admins/<int:admin_id>/delete/', views.church_admin_delete, name='church_admin_delete'),

    # Church Code Usage (Church Admins List)
    path('admin/church-codes', views.church_codes_usage_list, name='church_codes_usage_list'),
    path('admin/church-codes/delete/<int:admin_id>/', views.church_codes_usage_delete, name='church_codes_usage_delete'),
]
