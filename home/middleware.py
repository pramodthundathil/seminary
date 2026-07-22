from django.shortcuts import redirect
from django.contrib import messages
from home.models import RoleHasPermissions

class PermissionAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only enforce permission checks on paths starting with /menu/
        if request.path.startswith('/menu/'):
            # Check if user is authenticated
            if request.user.is_authenticated:
                try:
                    role_user = request.user.user_roles.first()
                    role = role_user.role if role_user else None
                    role_name = role.name if role else None
                except Exception:
                    role = None
                    role_name = None

                # Check if user is Church Admin
                from home.models import ChurchAdmins
                is_church_admin = False
                try:
                    if request.user.church_admin or ChurchAdmins.objects.filter(student__user=request.user, deleted_at__isnull=True).exists():
                        is_church_admin = True
                except Exception:
                    pass

                # Students, Church Users, and Church Admins have no access to admin index or admin pages under /menu/
                if role_name == "Student":
                    return redirect('student_home')
                elif is_church_admin or role_name == "Church Admin":
                    return redirect('church_admin_dashboard')
                elif role_name == "Church User":
                    return redirect('church_user_home')

                # Super Admins bypass all checks
                if role_name == "Admin":
                    return self.get_response(request)

                resolver_match = request.resolver_match
                if resolver_match:
                    url_name = resolver_match.url_name
                    
                    # URL Name to permission name mapping
                    permission_map = {
                        # Users
                        'users_list': 'manage-users',
                        'users_create': 'manage-users',
                        'users_view': 'manage-users',
                        'users_edit': 'manage-users',
                        'users_delete': 'manage-users',
                        'church_students_list': 'manage-users',
                        'bulk_upload_church_users': 'manage-users',
                        'download_bulk_template': 'manage-users',
                        'download_failed_rows': 'manage-users',
                        
                        # Students
                        'student_list': 'list-students',
                        'student_datatable': 'list-students',
                        'student_create': 'create-students',
                        'student_edit': 'edit-students',
                        'student_get': 'list-students',
                        'student_update': 'edit-students',
                        'student_delete': 'delete-students',
                        'student_detail': 'list-students',
                        'student_toggle_active': 'edit-students',
                        'student_toggle_approval': 'edit-students',
                        'student_approve_action': 'edit-students',
                        'student_disapprove_action': 'edit-students',
                        'student_activate_action': 'edit-students',
                        'student_deactivate_action': 'edit-students',
                        
                        # Books Assignment
                        'student_books_list': 'manage-book-assignments',
                        'student_books_datatable': 'manage-book-assignments',
                        'student_books_bulk_assign': 'manage-book-assignments',
                        'student_books_delete': 'manage-book-assignments',
                        'student_books_toggle_approval': 'manage-book-assignments',
                        
                        # Subjects Assignment
                        'student_subjects_list': 'manage-subject-assignments',
                        'student_subjects_datatable': 'manage-subject-assignments',
                        'student_subjects_bulk_assign': 'manage-subject-assignments',
                        'student_subjects_toggle_approval': 'manage-subject-assignments',
                        'student_subjects_update': 'manage-subject-assignments',
                        'student_subjects_delete': 'manage-subject-assignments',
                        
                        # Instructors Assignment
                        'student_instructors_list': 'manage-instructor-assignment',
                        'student_instructors_datatable': 'manage-instructor-assignment',
                        'student_instructors_bulk_assign': 'manage-instructor-assignment',
                        'student_instructors_delete': 'manage-instructor-assignment',
                        
                        # Uploads Assignment
                        'student_uploads_list': 'manage-upload-assignments',
                        'student_uploads_datatable': 'manage-upload-assignments',
                        'student_uploads_bulk_assign': 'manage-upload-assignments',
                        'student_uploads_delete': 'manage-upload-assignments',
                        
                        # Exams Assignment
                        'student_exams_list': 'manage-exam-assignment',
                        'student_exams_datatable': 'manage-exam-assignment',
                        'student_exams_bulk_assign': 'manage-exam-assignment',
                        'student_exams_delete': 'manage-exam-assignment',
                        'student_exams_toggle_approval': 'manage-exam-assignment',
                        'student_submitted_exams_list': 'manage-exam-assignment',
                        'student_submitted_exams_datatable': 'manage-exam-assignment',
                        'view_answer_sheet': 'manage-exam-assignment',
                        'update_answer_marks': 'manage-exam-assignment',
                        'mark_student_exam_retest_paid': 'manage-exam-assignment',
                        'student_exams_get': 'manage-exam-assignment',
                        'student_exams_update': 'manage-exam-assignment',
                        
                        # Assignment Assignment
                        'student_assignment_list': 'manage-assignment-assignment',
                        'student_submitted_assignment_list': 'manage-assignment-assignment',
                        'student_assignment_datatable': 'manage-assignment-assignment',
                        'view_assignment_answer_sheet': 'manage-assignment-assignment',
                        'student_assignment_edit': 'manage-assignment-assignment',
                        'student_assignment_delete': 'manage-assignment-assignment',
                        'update_assignment_marks': 'manage-assignment-assignment',
                        'student_assignments_assign': 'manage-assignment-assignment',
                        
                        # Applications
                        'application_list_view': 'manage-applications',
                        
                        # Menus
                        'menu_list': 'manage-menu',
                        'menu_datatable': 'manage-menu',
                        'menu_engineer': 'manage-menu',
                        'menu_engineer_new': 'manage-menu',
                        'save_menu': 'manage-menu',
                        'menu_item_create': 'manage-menu',
                        'menu_item_update': 'manage-menu',
                        'menu_item_delete': 'manage-menu',
                        'update_menu_order': 'manage-menu',
                        'delete_menu': 'manage-menu',
                        'refresh_menu_urls': 'manage-menu',
                        
                        # Pages
                        'pages_list': 'list-pages',
                        'page_create': 'create-pages',
                        'page_edit': 'edit-pages',
                        'page_view': 'list-pages',
                        'page_delete': 'delete-pages',
                        
                        # News
                        'news_list': 'list-news',
                        'news_datatable': 'list-news',
                        'news_create': 'create-news',
                        'news_get': 'list-news',
                        'news_edit': 'edit-news',
                        'news_delete': 'delete-news',
                        'news_toggle_status': 'edit-news',
                        
                        # Media
                        'media_list': 'manage-media',
                        'media_upload': 'manage-media',
                        'media_get': 'manage-media',
                        'media_update': 'manage-media',
                        'media_delete': 'manage-media',
                        'media_library_json': 'manage-media',
                        'media_library_upload_json': 'manage-media',
                        'media_library_list': 'manage-media',
                        
                        # Photo Gallery
                        'photo_gallery': 'manage-photo-gallery',
                        'photo_datatable': 'manage-photo-gallery',
                        'photo_create': 'manage-photo-gallery',
                        'photo_get': 'manage-photo-gallery',
                        'photo_update': 'manage-photo-gallery',
                        'photo_delete': 'manage-photo-gallery',
                        
                        # Video Gallery
                        'video_list': 'manage-video-gallery',
                        'video_create': 'manage-video-gallery',
                        'video_edit': 'manage-video-gallery',
                        'video_view': 'manage-video-gallery',
                        'video_delete': 'manage-video-gallery',
                        'video_library_json': 'manage-video-gallery',
                        'video_library_create_json': 'manage-video-gallery',
                        'youtube_library_json': 'manage-video-gallery',
                        'youtube_library_create_json': 'manage-video-gallery',
                        
                        # Sliders
                        'slider_list': 'manage-slider',
                        'slider_datatable': 'manage-slider',
                        'slider_create': 'manage-slider',
                        'slider_get': 'manage-slider',
                        'slider_update': 'manage-slider',
                        'slider_delete': 'manage-slider',
                        'slider_photos_list': 'manage-slider',
                        'slider_photos_datatable': 'manage-slider',
                        'slider_photo_create': 'manage-slider',
                        'slider_photo_get': 'manage-slider',
                        'slider_photo_update': 'manage-slider',
                        'slider_photo_delete': 'manage-slider',
                        
                        # Categories
                        'category_list': 'list-categories',
                        'category_create': 'create-category',
                        'category_edit': 'edit-category',
                        'category_view': 'list-categories',
                        'category_delete': 'delete-category',
                        
                        # Courses
                        'course_list': 'list-course',
                        'course_datatable': 'list-course',
                        'course_create': 'create-course',
                        'course_get': 'list-course',
                        'course_update': 'edit-course',
                        'course_delete': 'delete-course',
                        
                        # Languages
                        'languages_list': 'list-languages',
                        'language_create': 'create-languages',
                        'language_edit': 'edit-languages',
                        'language_view': 'list-languages',
                        'language_delete': 'delete-languages',
                        
                        # Subjects
                        'subjects_list': 'list-subjects',
                        'subjects_export': 'list-subjects',
                        'subjects_create': 'create-subjects',
                        'subjects_view': 'list-subjects',
                        'subjects_edit': 'edit-subjects',
                        'subjects_delete': 'delete-subjects',
                        
                        # Branches
                        'branches_list': 'list-branches',
                        'branches_create': 'create-branches',
                        'branches_edit': 'edit-branches',
                        'branches_view': 'list-branches',
                        'branches_delete': 'delete-branches',
                        
                        # Contact Requests
                        'contact_list': 'manage-contacts',
                        'contact_view': 'manage-contacts',
                        'contact_delete': 'manage-contacts',
                        'contact_permanent_delete': 'manage-contacts',
                        
                        # Exams
                        'exams_list': 'list-exams',
                        'exams_create': 'create-exams',
                        'exams_view': 'list-exams',
                        'exams_edit': 'edit-exams',
                        'exams_delete': 'delete-exams',
                        'question_descriptive_create': 'edit-exams',
                        'question_descriptive_edit': 'edit-exams',
                        'question_descriptive_delete': 'edit-exams',
                        'question_objective_create': 'edit-exams',
                        'question_objective_edit': 'edit-exams',
                        'question_objective_delete': 'edit-exams',
                        
                        # Staffs
                        'staffs_list': 'list-staffs',
                        'staffs_create': 'create-staffs',
                        'staffs_view': 'list-staffs',
                        'staffs_edit': 'edit-staffs',
                        'staffs_delete': 'delete-staffs',
                        
                        # Assignments
                        'assignments_list': 'list-assignments',
                        'assignments_create': 'create-assignments',
                        'assignments_view': 'list-assignments',
                        'assignments_edit': 'edit-assignments',
                        'assignments_delete': 'delete-assignments',
                        
                        # References
                        'reference_list': 'list-references',
                        'reference_create': 'create-references',
                        'reference_view': 'list-references',
                        'reference_edit': 'edit-references',
                        'reference_delete': 'delete-references',
                        
                        # Support
                        'support_list': 'manage-supports',
                        'support_view': 'manage-supports',
                        'support_delete': 'manage-supports',
                        'support_reply_delete': 'manage-supports',
                        
                        # Uploads
                        'uploads_list': 'list-uploads',
                        'uploads_create': 'create-uploads',
                        'uploads_view': 'list-uploads',
                        'uploads_edit': 'edit-uploads',
                        'uploads_delete': 'delete-uploads',
                        
                        # Payments
                        'payments_list': 'manage-payments',
                        'payments_view': 'manage-payments',
                        'payments_delete': 'manage-payments',
                        'payment_dashboard': 'manage-payments',
                        
                        # Church Codes/Admins
                        'church_code_list': 'list-branches',
                        'church_code_create': 'list-branches',
                        'church_code_edit': 'list-branches',
                        'church_code_delete': 'list-branches',
                        'church_admin_list': 'list-branches',
                        'church_admin_create': 'list-branches',
                        'church_admin_delete': 'list-branches',
                        'church_codes_usage_list': 'list-branches',
                        'church_codes_usage_view': 'list-branches',
                        'church_codes_usage_delete': 'list-branches',
                        'church_admin_toggle_payment': 'list-branches',
                        'church_admin_applications_list': 'manage-church-admin-applications',
                        'approve_church_admin': 'manage-church-admin-applications',
                        'reject_church_admin': 'manage-church-admin-applications',
                        'get_church_admin_application_details': 'manage-church-admin-applications',
                        
                        # Roles
                        'roles': 'list-role',
                        'roles_create': 'list-role',
                        'roles_view': 'list-role',
                        'roles_edit': 'list-role',
                        'roles_delete': 'list-role',
                    }
                    
                    required_permission = permission_map.get(url_name)
                    if required_permission:
                        has_perm = RoleHasPermissions.objects.filter(role=role, permission__name=required_permission).exists()
                        if not has_perm:
                            messages.error(request, f"Access denied. You do not have permission to access that section ({required_permission}).")
                            return redirect('admin_index')
            else:
                return redirect('signin')

        return self.get_response(request)
