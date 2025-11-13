from django.urls import path
from . import views



urlpatterns = [
    # Menu Management
    path('menus/', views.menu_list, name='menu_list'),
    path('menus/engineer/', views.menu_engineer, name='menu_engineer_new'),
    path('menus/engineer/<int:menu_id>/', views.menu_engineer, name='menu_engineer'),
    path('menus/save/', views.save_menu, name='save_menu'),
    path('menus/save-items/', views.save_menu_items, name='save_menu_items'),
    path('menus/delete/<int:menu_id>/', views.delete_menu, name='delete_menu'),
    path('menus/get-items/<int:menu_id>/', views.get_menu_items, name='get_menu_items'),
    
    # Pages Management
    path('pages/', views.pages_list, name='pages_list'),


    # News Management
    path('news_list', views.news_list, name='news_list'),
    path('datatable/', views.news_datatable, name='news_datatable'),
    path('create/', views.news_create, name='news_create'),
    path('edit/<int:news_id>/', views.news_edit, name='news_edit'),
    path('get/<int:news_id>/', views.news_get, name='news_get'),
    path('delete/<int:news_id>/', views.news_delete, name='news_delete'),
    path('toggle-status/<int:news_id>/', views.news_toggle_status, name='news_toggle_status'),

    # Media Library Management
    path('media/', views.media_list, name='media_list'),
    path('media/datatable/', views.media_datatable, name='media_datatable'),
    path('media/upload/', views.media_upload, name='media_upload'),
    path('media/get/<int:media_id>/', views.media_get, name='media_get'),
    path('media/update/<int:media_id>/', views.media_update, name='media_update'),
    path('media/delete/<int:media_id>/', views.media_delete, name='media_delete'),


    #photo gallery

    path("photo_gallery",views.photo_gallery,name="photo_gallery"),



    # Slider management
    path('sliders/', views.slider_list, name='slider_list'),
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


    # Course management
    path('courses/', views.course_list, name='course_list'),
    path('courses/datatable/', views.course_datatable, name='course_datatable'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/get/<int:course_id>/', views.course_get, name='course_get'),
    path('courses/update/<int:course_id>/', views.course_update, name='course_update'),
    path('courses/delete/<int:course_id>/', views.course_delete, name='course_delete'),


     # Student Management
    path('students/', views.student_list_view, name='student_list'),
    path('students/datatable/', views.student_datatable, name='student_datatable'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/get/<int:student_id>/', views.student_get, name='student_get'),
    path('students/update/<int:student_id>/', views.student_update, name='student_update'),
    path('students/delete/<int:student_id>/', views.student_delete, name='student_delete'),
    path('students/toggle-active/<int:student_id>/', views.student_toggle_active, name='student_toggle_active'),
    path('students/toggle-approval/<int:student_id>/', views.student_toggle_approval, name='student_toggle_approval'),
]
