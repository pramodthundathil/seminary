from django.urls import path, include
from . import views



urlpatterns = [

    #admin index
    path("admin/dashboard",views.admin_index,name="admin_index"),

    # Menu Management
    path('admin/menus/', views.menu_list, name='menu_list'),
    path('menus/engineer/', views.menu_engineer, name='menu_engineer_new'),
    path('menus/engineer/<int:menu_id>/', views.menu_engineer, name='menu_engineer'),
    path('menus/save/', views.save_menu, name='save_menu'),
    path('menus/save-items/', views.save_menu_items, name='save_menu_items'),
    path('menus/delete/<int:menu_id>/', views.delete_menu, name='delete_menu'),
    path('menus/get-items/<int:menu_id>/', views.get_menu_items, name='get_menu_items'),
    
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


    #photo gallery
    
    path('admin/photos', views.photo_gallery, name='photo_gallery'),
    path('photos/datatable/', views.photo_datatable, name='photo_datatable'),
    path('photos/create/', views.photo_create, name='photo_create'),
    path('photos/get/<int:photo_id>/', views.photo_get, name='photo_get'),
    path('photos/update/<int:photo_id>/', views.photo_update, name='photo_update'),
    path('photos/delete/<int:photo_id>/', views.photo_delete, name='photo_delete'),
    path('photos/media-list/', views.media_library_list, name='media_library_list'),



    # Slider management
    path('admin/sliders', views.slider_list, name='slider_list'),
    path('sliders/datatable/', views.slider_datatable, name='slider_datatable'),
    path('sliders/create/', views.slider_create, name='slider_create'),
    path('sliders/get/<int:slider_id>/', views.slider_get, name='slider_get'),
    path('sliders/update/<int:slider_id>/', views.slider_update, name='slider_update'),
    path('sliders/delete/<int:slider_id>/', views.slider_delete, name='slider_delete'),
    
    # Slider photos management
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
    path('students/update/<int:student_id>/', views.student_update, name='student_update'),
    path('students/delete/<int:student_id>/', views.student_delete, name='student_delete'),
    path('students/toggle-active/<int:student_id>/', views.student_toggle_active, name='student_toggle_active'),
    path('students/toggle-approval/<int:student_id>/', views.student_toggle_approval, name='student_toggle_approval'),


    #videos

    path("admin/videos", views.video_list, name = "video_list"),
    path('videos/create/', views.video_create, name='video_create'),
    path('videos/<int:video_id>/edit/', views.video_edit, name='video_edit'),
    path('videos/<int:video_id>/view/', views.video_view, name='video_view'),
    path('videos/<int:video_id>/delete/', views.video_delete, name='video_delete'),


    #roles and permissions

    path("admin/roles",views.roles,name="roles"),


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

]
