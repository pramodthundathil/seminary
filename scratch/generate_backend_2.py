routes_data = [
    {"prefix": "course", "model": "Courses"},
    {"prefix": "student_books", "model": "StudentsBooks"},
    {"prefix": "student_subjects", "model": "StudentsSubjects"},
    {"prefix": "student_instructors", "model": "StudentsInstructor"},
    {"prefix": "student_uploads", "model": "StudentsUploads"},
    {"prefix": "student_exams", "model": "StudentsExams"},
    {"prefix": "student_assignment", "model": "StudentsAssignment"},
    {"prefix": "student", "model": "Students", "real_delete": True}, # Student uses hard delete .delete() in original!
    {"prefix": "staff", "model": "Staffs"},
    {"prefix": "assignment", "model": "Assignments"},
    {"prefix": "reference", "model": "BookReferences"},
    {"prefix": "payments", "model": "Payments"},
    {"prefix": "church_codes_usage", "model": "ChurchAdmins"},
    {"prefix": "users", "model": "Users"},
    {"prefix": "church_code", "model": "ChurchLoginCodeSettings"}
]

views_content = ""

for item in routes_data:
    prefix = item["prefix"]
    model = item["model"]
    real_delete = item.get("real_delete", False)
    
    if real_delete:
        update_logic = f"{model}.objects.filter(id__in=ids).delete()"
    elif prefix == "users":
        update_logic = f"{model}.objects.filter(id__in=ids).update(deleted_at=timezone.now(), is_active=False)"
    else:
        update_logic = f"{model}.objects.filter(id__in=ids).update(deleted_at=timezone.now())"
        
    views_content += f"""
@login_required
@require_POST
def {prefix}_bulk_delete(request):
    import json
    ids = request.POST.getlist('ids')
    if not ids:
        try:
            ids = json.loads(request.body).get('ids', [])
        except:
            pass
    if ids:
        {update_logic}
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({{'success': True, 'message': f'Successfully deleted {{len(ids)}} items'}})
        messages.success(request, f'Successfully deleted {{len(ids)}} items!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({{'success': False, 'message': 'No items selected'}}, status=400)
        messages.warning(request, 'No items selected for deletion.')
    
    # We must redirect to the correct list view, but if it's AJAX, we already returned JsonResponse.
    # We'll just redirect to HTTP_REFERER if available, else a safe default.
    return redirect(request.META.get('HTTP_REFERER', '/menu/admin/'))
"""

print(views_content)
