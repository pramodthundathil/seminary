routes_data = [
    {"route": "admin/pages/", "prefix": "pages", "model": "Pages"},
    {"route": "admin/courses/", "prefix": "course", "model": "Courses"},
    {"route": "admin/students/student-books/", "prefix": "student_books", "model": "StudentBooks"},
    {"route": "admin/students/student-subjects/", "prefix": "student_subjects", "model": "StudentSubjects"},
    {"route": "admin/students/student-instructor/", "prefix": "student_instructors", "model": "StudentInstructors"},
    {"route": "admin/students/student-uploads/", "prefix": "student_uploads", "model": "StudentUploads"},
    {"route": "admin/students/student-submitted-exams/", "prefix": "student_submitted_exams", "model": "StudentSubmittedExams"},
    {"route": "admin/students/student-submitted-assignment/", "prefix": "student_submitted_assignment", "model": "StudentSubmittedAssignment"},
    {"route": "admin/students/student-exams", "prefix": "student_exams", "model": "StudentExams"},
    {"route": "admin/students/student-assignment/", "prefix": "student_assignment", "model": "StudentAssignment"},
    {"route": "admin/students/", "prefix": "student", "model": "Students"},
    {"route": "admin/applications/", "prefix": "application", "model": "Applications"},
    {"route": "admin/staffs", "prefix": "staff", "model": "Staffs"},
    {"route": "admin/assignments", "prefix": "assignment", "model": "Assignments"},
    {"route": "admin/references", "prefix": "reference", "model": "References"},
    {"route": "admin/support", "prefix": "support", "model": "Support"},
    {"route": "admin/uploads/", "prefix": "uploads", "model": "Uploads"},
    {"route": "admin/payments/", "prefix": "payments", "model": "Payments"},
    {"route": "admin/church-codes", "prefix": "church_codes_usage", "model": "ChurchCodesUsage"},
    {"route": "admin/users/", "prefix": "users", "model": "Users"},
    {"route": "admin/codes/", "prefix": "church_code", "model": "ChurchCodes"},
    {"route": "admin/church-admin-applications/", "prefix": "church_admin_applications", "model": "ChurchAdminApplications"}
]

views_content = ""
urls_content = ""

for item in routes_data:
    prefix = item["prefix"]
    model = item["model"]
    
    views_content += f"""
@login_required
@require_POST
def {prefix}_bulk_delete(request):
    ids = request.POST.getlist('ids')
    if not ids:
        import json
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        {model}.objects.filter(id__in=ids).update(deleted_at=timezone.now())
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({{'success': True, 'message': f'Successfully deleted {{len(ids)}} items'}})
        messages.success(request, f'Successfully deleted {{len(ids)}} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({{'success': False, 'message': 'No items selected'}}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    return redirect('{prefix}_list')
"""

print(views_content)
